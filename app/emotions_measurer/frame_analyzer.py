import cv2
from deepface import DeepFace
from typing import Final, Any


SCALE_FACTOR: Final[float] = 1.1
MIN_NEIGHBORS: Final[int] = 5



class FrameAnalyzer:
    """
    Frame analyzer utility.
    
    The class is used to parse frames by the given algorithm.
    """

    @staticmethod
    def analyze_frame(
            frame,
            brows_predictor: cv2.CascadeClassifier,
            eye_predictor: cv2.CascadeClassifier,
    ) -> list[dict[str, Any]]:
        """
        Processes given frame and detects an emotional state of the person on it.

        The function follows the following steps in order to do so:
        1. Set up variables, that will determine the boundaries.
        2. Convert frame to the gray color in order to user classifier.
        3. Delect brows on the frame.
        4. Go through detected features and modify boundaries if needed.
        5. Detect eyes on the frame.
        6. Go through detected features and modify boundaries if needed.
        7. Detect emotions on the frame with given boundaries.`
        """
        top = -1
        bottom = 2 ** 31
        left = 2 * 31
        right = -1
        gray_frame = cv2.cvtColor(
            src=frame,
            code=cv2.COLOR_BGR2GRAY,
        )
        brows = brows_predictor.detectMultiScale(
            image=gray_frame,
            scaleFactor=SCALE_FACTOR,
            minNeighbors=MIN_NEIGHBORS,
        )
        for x, y, width, height in brows:
            cv2.rectangle(
                img=frame,
                pt1=(x, y),
                pt2=(x + width, y + height),
                color=(255, 0, 0),
                thickness=2,
            )
            left = min(left, x)
            right = max(right, x + width)
            top = max(top, y + height)
            bottom = min(bottom, y)
        eyes = eye_predictor.detectMultiScale(
            image=gray_frame,
            scaleFactor=SCALE_FACTOR,
            minNeighbors=MIN_NEIGHBORS,
        )
        if len(eyes) == 0:
            raise Exception('Looked away')
        for x, y, width, height in eyes:
            cv2.rectangle(
                img=frame,
                pt1=(x, y),
                pt2=(x + width, y + height), 
                color=(255, 0, 0),
                thickness=2,
            )
            left = min(left, x)
            right = max(right, x + width)
            top = max(top, y + height)
            bottom = min(bottom, y)
        emotions = None
        try:
            emotions = DeepFace.analyze(
                img_path=frame[bottom:top, left:right],
                actions=['emotion']
            )
        except ValueError:
            emotions = DeepFace.analyze(
                img_path=frame,
                actions=['emotion'],
                enforce_detection=False
            )
        return emotions
