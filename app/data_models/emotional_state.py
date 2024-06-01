from typing import Tuple
from pydantic import BaseModel
from enum import StrEnum

class EmotionalState(BaseModel):
    """Data class to outline emotional state on a given frame."""
    angry: float
    disgust: float
    fear: float
    happy: float
    sad: float
    surprise: float
    neutral: float