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
from sqlalchemy import func

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
                measurer._best_performance,
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


@app.post("/uploadReport/")
async def uploadLastReport(db: db_dependency):
    lastReport = db.query(func.max(models.EmotionReportResults.id)).first()[0]
    s3_client = boto3.client(
        's3',
        region_name='ru-central-1',
        endpoint_url='http://127.0.0.1:9000',
        aws_access_key_id='SECOND_USER',
        aws_secret_access_key='SECOND_USER_SECRET',
    )
    buckets = s3_client.list_buckets().get('Buckets', list())
    creationNeeded = True
    for bucket in buckets:
        if bucket['Name'] == 'results':
            creationNeeded = False
    if creationNeeded:
        print('[INFO] Bucket non existent, need to create. Creating...')
        s3_client.create_bucket(Bucket='results')
    print('[INFO] Uploading file...')
    s3_client.upload_file('emotional_report.pdf', 'results', f'result{lastReport}')
    return Response(str(lastReport))


@app.get("/getReportFromS3/{id}/")
async def getReportFromS3(id: int):
    s3_client = boto3.client(
        's3',
        region_name='ru-central-1',
        endpoint_url='http://127.0.0.1:9000',
        aws_access_key_id='SECOND_USER',
        aws_secret_access_key='SECOND_USER_SECRET',
    )
    with open(f'result{id}.pdf', 'wb') as file:
        s3_client.download_fileobj(
            'results',
            f'result{id}',
            file,
        )
    pdf_bytes = open(f'result{id}.pdf', 'rb').read()
    response = Response(content=pdf_bytes)
    response.headers['Content-Disposition'] = f'attachment; filename="result{id}.pdf"'
    response.headers['Content-Type'] = 'application/pdf'
    return response