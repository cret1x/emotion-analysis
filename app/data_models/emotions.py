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