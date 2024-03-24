from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import boto3
from app.emotions_measurer.measurer import EmotionsMeasurer
from app.utils.utility_functions import get_percentages_from_results
from starlette.responses import Response


app = FastAPI()
models.Base.metadata.create_all(bind=engine)


class S3CredentialsBase(BaseModel):
    """
    S3 credentials to pass in order to upload the video to the API.
    """
    region: str
    endpoint_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    bucket_name: str
    key_name: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.post('/requestReport')
async def requestReport(credentials: S3CredentialsBase, db: db_dependency):
    try:
        client = boto3.client(
            's3',
            region_name = credentials.region,
            endpoint_url = credentials.endpoint_url,
            aws_access_key_id = credentials.aws_access_key_id,
            aws_secret_access_key = credentials.aws_secret_access_key,
        )
        with open('video.mp4', 'wb') as file:
            client.download_fileobj(
                credentials.bucket_name,
                credentials.key_name,
                file,
            )
            report = models.EmotionReports(
                report_name=f'{credentials.bucket_name}-{credentials.key_name}'
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            measurer = EmotionsMeasurer('video.mp4', None, '')
            measurer.analyse_prepared_video()
            percentages = get_percentages_from_results(
                measurer._emotions_occurances,
                measurer._looked_away,
                measurer._frames_amount
            )
            reportResult = models.EmotionReportResults(reportId=report.id)
            db.add(reportResult)
            db.commit()
            db.refresh(reportResult)
            reportResultData = models.EmotionReportData(
                reportResultId=reportResult.id,
                neutral=percentages['neutral'],
                sad=percentages['sad'],
                happy=percentages['happy'],
                disgust=percentages['disgust'],
                surprise=percentages['surprise'],
                fear=percentages['fear'],
                angry=percentages['angry'],
                lookedAway=percentages['lookedAway'],
            )
            db.add(reportResultData)
            db.commit()
            return Response(content=str(reportResult.id), status_code=200)
    except Exception as ex:
        return Response(content=ex, status_code=404)


@app.get("/getReportResult/{reportResultId}")
async def getReportResult(reportResultId: int, db: db_dependency):
    result = db.query(
        models.EmotionReportData
    ).filter(
        models.EmotionReportData.reportResultId == reportResultId
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail='No such report result.')
    return result
