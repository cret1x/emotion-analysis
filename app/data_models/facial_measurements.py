from typing import Tuple
from pydantic import BaseModel
from enum import StrEnum

class FacialMeasurements(BaseModel):
    """Data class to outline coordinates and measurements of a feature."""
    x: int
    y: int
    width: int
    height: int