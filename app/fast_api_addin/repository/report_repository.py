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


def addReportResults(report, db):
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
    return reportResult


def getReportResult(db):
    result = db.query(
    models.EmotionReportData
    ).filter(
    models.EmotionReportData.reportResultId == reportResultId
    ).first()
    return result

def getReportResults(db):
    result = db.query(
        models.EmotionReportData
    )