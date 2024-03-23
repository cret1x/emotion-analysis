from typing import Optional
from cv2 import VideoCapture
import cv2
import pathlib
from app.data_models.models import *
from app.emotions_measurer.frame_analyzer import FrameAnalyzer
from pydantic_core import ValidationError


def get_amount_of_frames(capture: VideoCapture) -> int:
    return int(capture.get(cv2.CAP_PROP_FRAME_COUNT))


def separate_frames_into_arrays(
        capture: VideoCapture,
        threads_amount: int,
        frames_amount: int
) -> list[list]:
    frames_per_thread = list()
    overall_frames = list()
    for _ in range(frames_amount):
        _, frame = capture.read()
        overall_frames.append(frame)
    batches = frames_amount // threads_amount
    for i in range(threads_amount):
        frames_per_thread.append(
            overall_frames[
                (i * batches):((i + 1) * batches)
            ]
        )
    if batches * threads_amount == batches:
        return frames_per_thread
    frames_per_thread[threads_amount - 1].extend(
        overall_frames[threads_amount * batches:]
    )
    return frames_per_thread


def validate_input(filename: str, threads_amount: str) -> bool:
    threads_valid: bool = True
    filename_valid: bool = True
    file = pathlib.Path(filename)
    if not file.exists() or not filename.lower().endswith('mp4'):
        filename_valid = False
    if threads_amount != '' and not threads_amount.isdigit():
        threads_valid = False
    return threads_valid and filename_valid


def analyze_several_frames(frames: list, thread: int) -> dict[Emotions, int]:
    analysis_result: dict[Emotions, int] = dict()
    brows_predictor = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml'
    )
    eye_predictor = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml'
    )
    i = 0
    validationErrorsEncountered = 0
    for frame in frames:
        emotions = FrameAnalyzer.analyze_frame(
            frame,
            brows_predictor,
            eye_predictor
        )
        if i % 100 == 0:
            print(f'Thread number {thread}: processed {i} frames.')
        for emotion in emotions:
            try:
                emotion_model = EmotionalReport.model_validate(emotion)
                if Emotions(emotion_model.dominant_emotion) not in analysis_result.keys():
                    analysis_result[Emotions(emotion_model.dominant_emotion)] = 0
                analysis_result[Emotions(emotion_model.dominant_emotion)] += 1
            except ValidationError:
                validationErrorsEncountered += 1
                try:
                    dominant = emotion['dominant_emotion']
                except KeyError:
                    continue
                if Emotions(dominant) not in analysis_result.keys():
                    analysis_result[Emotions(dominant)] = 0
                analysis_result[Emotions(dominant)] += 1
        i += 1
    print(
        f'Thread {thread} finished working. '
        f'Validation errors encountered: {validationErrorsEncountered}'
    )
    return analysis_result
