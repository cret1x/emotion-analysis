from typing import Tuple
from pydantic import BaseModel
from enum import StrEnum


class Emotions(StrEnum):
    """Enumeration to outline emotion types."""
    ANGRY = 'angry'
    DISGUST = 'disgust'
    FEAR = 'fear'
    HAPPY = 'happy'
    SAD = 'sad'
    SURPRISE = 'surprise'
    NEUTRAL = 'neutral'


class FacialMeasurements(BaseModel):
    """Data class to outline coordinates and measurements of a feature."""
    x: int
    y: int
    width: int
    height: int


class EmotionalState(BaseModel):
    """Data class to outline emotional state on a given frame."""
    angry: float
    disgust: float
    fear: float
    happy: float
    sad: float
    surprise: float
    neutral: float


class RegionOfEvaluation(BaseModel):
    """Data class on analysis region position."""
    x: int
    y: int
    w: int
    h: int
    left_eye: Tuple[int, int]
    right_eye: Tuple[int, int]


class EmotionalReport(BaseModel):
    """The model of reports of emotions."""
    emotion: EmotionalState
    dominant_emotion: str
    region: RegionOfEvaluation
    face_confidence: float
