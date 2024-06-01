from typing import Tuple
from pydantic import BaseModel
from enum import StrEnum

class RegionOfEvaluation(BaseModel):
    """Data class on analysis region position."""
    x: int
    y: int
    w: int
    h: int
    left_eye: Tuple[int, int]
    right_eye: Tuple[int, int]