from sqlalchemy import (
    Column, 
    ForeignKey,
    Integer,
    String,
    Float,
)
from database import Base


class EmotionReports(Base):
    """Table for emotion reports registry."""

    __tablename__ = 'emotionReports'

    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String)


class EmotionReportResults(Base):
    """Table for storing emotional reports results."""

    __tablename__ = 'emotionReportResults'

    id = Column(Integer, primary_key=True, index=True)
    reportId = Column(Integer, ForeignKey('emotionReports.id'))


class EmotionReportData(Base):
    """Table for storing inner parts of the report results."""
    
    __tablename__ = 'resultDetails'

    id = Column(Integer, index=True, primary_key=True)
    reportResultId = Column(Integer, ForeignKey('emotionReportResults.id'))
    neutral = Column(Float, default=0.0)
    angry = Column(Float, default=0.0)
    disgust = Column(Float, default=0.0)
    fear = Column(Float, default=0.0)
    happy = Column(Float, default=0.0)
    sad = Column(Float, default=0.0)
    surprise = Column(Float, default=0.0)
    lookedAway = Column(Float, default=0.0)
