import cv2
from deepface import DeepFace
from typing import Final


SCALE_FACTOR: Final[float] = 1.1
MIN_NEIGHBORS: Final[int] = 5



class FrameAnalyzer:
    """Frame analyzer utility."""

    @staticmethod
    def analyze_frame(
            frame,
            brows_predictor: cv2.CascadeClassifier,
            eye_predictor: cv2.CascadeClassifier,
    ):
        top = -1
        bottom = 2 ** 31
        left = 2 * 31
        right = -1
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brows = brows_predictor.detectMultiScale(gray_frame, SCALE_FACTOR, MIN_NEIGHBORS)
        for x, y, width, height in brows:
            cv2.rectangle(frame, (x, y), (x + width, y + height), (255, 0, 0), 2)
            left = min(left, x)
            right = max(right, x + width)
            top = max(top, y + height)
            bottom = min(bottom, y)
        eyes = eye_predictor.detectMultiScale(
            gray_frame,
            SCALE_FACTOR,
            MIN_NEIGHBORS
        )
        for x, y, width, height in eyes:
            cv2.rectangle(frame, (x, y), (x + width, y + height), (255, 0, 0), 2)
            left = min(left, x)
            right = max(right, x + width)
            top = max(top, y + height)
            bottom = min(bottom, y)
        emotions = None
        try:
            emotions = DeepFace.analyze(frame[bottom:top, left:right], actions=['emotion'])
        except ValueError:
            emotions = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
        return emotions
