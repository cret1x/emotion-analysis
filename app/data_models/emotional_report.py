from typing import Tuple
from pydantic import BaseModel
from enum import StrEnum

class EmotionalReport(BaseModel):
    """The model of reports of emotions."""
    emotion: EmotionalState
    dominant_emotion: str
    region: RegionOfEvaluation
    face_confidence: float