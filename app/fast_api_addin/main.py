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
from fastapi.middleware.cors import CORSMiddleware
from app.utils.utility_functions import generate_latex_report_from_result_dictionary

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


class ReportResultsBase(BaseModel):
    id: int
    reportResultId: int
    neutral: float
    angry: float
    disgust: float
    fear: float
    happy: float
    sad: float
    surprise: float
    lookedAway: float

    class Config:
        orm_mode = True


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

    class Config:
        orm_mode = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.post('/requestReport/')
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
            generate_latex_report_from_result_dictionary(
                measurer._emotions_occurances,
                measurer._looked_away,
                measurer._frames_amount,
                measurer._coordinates,
            )
            return Response(content=str(reportResult.id), status_code=200)
    except Exception as ex:
        return Response(content=ex, status_code=404)


@app.get("/getReportResult/{reportResultId}/", response_model=ReportResultsBase)
async def getReportResult(reportResultId: int, db: db_dependency):
    result = db.query(
        models.EmotionReportData
    ).filter(
        models.EmotionReportData.reportResultId == reportResultId
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail='No such report result.')
    return result

@app.get("/getReportResults/", response_model=List[ReportResultsBase])
async def getReportResults(db: db_dependency):
    result = db.query(
        models.EmotionReportData
    )
    if not result:
        return Response(content='No reports', status_code=404)
    return result

@app.get("/getLastReport/")
async def getLastReport():
    pdf_bytes = open('emotional_report.pdf', 'rb').read()
    response = Response(content=pdf_bytes)
    response.headers['Content-Disposition'] = 'attachment; filename="emotional_report.pdf"'
    response.headers['Content-Type'] = 'application/pdf'
    return response
