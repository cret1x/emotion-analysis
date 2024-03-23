from datetime import datetime
import os
from typing import Tuple
from cv2 import VideoCapture
import cv2
import pathlib
from app.data_models.models import EmotionalReport, Emotions
from app.emotions_measurer.frame_analyzer import FrameAnalyzer
from pydantic_core import ValidationError
from pylatex import (
    Document,
    Section,
    Subsection,
    Axis,
    Plot,
    Figure,
    Matrix,
    Alignat,
)


def get_amount_of_frames(capture: VideoCapture) -> int:
    """Get the amount of frames in the provided video."""
    return int(capture.get(cv2.CAP_PROP_FRAME_COUNT))


def separate_frames_into_arrays(
        capture: VideoCapture,
        threads_amount: int,
        frames_amount: int
) -> list[list]:
    """
    The given video's frames are being separated between processes.

    The method is dedicated to separate frames between threads.
    There are following rules for that:
    1. Frames should remain in the same order for further processing.
    2. Each thread initially gets the same amount of frames.
    3. If any frames are left, the last ones are sent to the last thread.
    """
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


def validate_input(
        filename: str,
        threads_amount: str,
        mode: str,
) -> Tuple[bool, str]:
    """
    User input is being validated.
    
    The following validation operations are implied:
    1. File with the video exists and is of type mp4.
    2. Thread amount is a number and is digit.
    3. If mode is provided, than it should be realtime.
    """
    if mode != '' and mode != 'realtime':
        return (
            False,
            'When providing mode parameter, specify it as "realtime".'
        )
    if mode != '':
        return (True, '')
    file = pathlib.Path(filename)
    if not file.exists():
        return (
            False,
            'File is non-existent.'
        )
    if not filename.lower().endswith('mp4'):
        return (
            False,
            'File is of unexpected type. MP4 is supported.'
        )
    if threads_amount != '' and (not threads_amount.isdigit()):
        if threads_amount.startswith('-'):
            return (
                False,
                'Threads amount is expected to be a non-negative integer.'
            )
        return (
            False,
            'Threads amount is supposed to be an integer.'
        )
    if threads_amount == '0':
        return (
            False,
            'Threads amount is supposed to be a non-zero integer.'
        )
    return (True, '')


def analyze_several_frames(
        frames: list,
        thread: int
) -> Tuple[dict[Emotions, int], int]:
    """
    Analyze frames for emotions.
    
    Main points:
    1. The method is created for threads to work with.
    2. It creates the classifier and goes frame by frame through the list.
    3. Each 100 frames, a message is being written for tracking.
    4. The reports are being validated by BaseModel and the report is passed back.
    """
    looked_away = 0
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
        emotions = list()
        try:
            emotions = FrameAnalyzer.analyze_frame(
                frame,
                brows_predictor,
                eye_predictor
            )
        except Exception:
            looked_away += 1
        if i % 100 == 0:
            print(f'[INFO] Thread number {thread}: processed {i} frames.')
        for emotion in emotions:
            try:
                emotion_model = EmotionalReport.model_validate(emotion)
                if Emotions(emotion_model.dominant_emotion) not in \
                        analysis_result.keys():
                    analysis_result[
                        Emotions(emotion_model.dominant_emotion)
                    ] = 0
                analysis_result[Emotions(emotion_model.dominant_emotion)] += 1
                cv2.putText(
                    frame,
                    emotion_model.dominant_emotion,
                    (0, 0),
                    cv2.FONT_HERSHEY_PLAIN,
                    0.9,
                    (255, 0, 0), 
                    3,       
                )
            except ValidationError:
                validationErrorsEncountered += 1
                try:
                    dominant = emotion['dominant_emotion']
                    if Emotions(dominant) not in \
                            analysis_result.keys():
                        analysis_result[Emotions(dominant)] = 0
                    analysis_result[Emotions(dominant)] += 1
                    cv2.putText(
                        frame,
                        dominant,
                        (0, 0),
                        cv2.FONT_HERSHEY_PLAIN,
                        0.9,
                        (255, 0, 0), 
                        3,       
                    )
                except KeyError:
                    continue
        i += 1
    print(
        f'[INFO] Thread {thread} finished working. '
        f'Validation errors encountered: {validationErrorsEncountered}'
    )
    return analysis_result, looked_away


def generate_textual_report_from_result_dictionary(
        result: dict[Emotions, int],
        looked_away: int,
        overall_frames_amount: int,
) -> None:
    """
    Following the gathered results, provide textual output on emotional state.
    """
    overall_labeled_frames_amount = 0
    for emotion in result.keys():
        overall_labeled_frames_amount += result[emotion]
    emotions_percentages: dict[Emotions, float] = dict()
    for emotion in result.keys():
        emotions_percentages[emotion] = result[emotion] / \
            overall_labeled_frames_amount * 100
    sorted_percentages = {
        key: value for key, value in sorted(
            emotions_percentages.items(),
            key=lambda item: -item[1]
        )
    }
    looked_away_percentage = round(
        looked_away / overall_frames_amount * 100,
        2
    )
    print(
        '[INFO] Emotions encountered on the video '
        '(from the most popular to the least popular):'
    )
    for emotion, percentage in sorted_percentages.items():
        print(
            f'[INFO] Emotion "{emotion}" was present on '
            f'{round(percentage, 2)}% of labeled frames.'
        )
    print(
        f'[INFO] Person also looked away {looked_away} times, which is '
        f'{looked_away_percentage}% of the time.'
    )


def generate_latex_report_from_result_dictionary(
        result: dict[Emotions, int],
        looked_away: int,
        overall_frames_amount: int,
) -> None:
    """
    Following the gathered results, provide file output on emotional state.
    """
    overall_labeled_frames_amount = 0
    for emotion in result.keys():
        overall_labeled_frames_amount += result[emotion]
    emotions_percentages: dict[Emotions, float] = dict()
    for emotion in result.keys():
        emotions_percentages[emotion] = result[emotion] / \
            overall_labeled_frames_amount * 100
    sorted_percentages = {
        key: value for key, value in sorted(
            emotions_percentages.items(),
            key=lambda item: -item[1]
        )
    }
    looked_away_percentage = round(
        looked_away / overall_frames_amount * 100,
        2
    )
    geometry_options = {'tmargin': '1cm', 'lmargin': '10cm'}
    document = Document(geometry_options=geometry_options)
    with document.create(Section('Emotions recorded')):
        document.append(
            ' Emotions encountered on the video '
            '(from the most popular to the least popular):\n'
        )
        for emotion, percentage in sorted_percentages.items():
            document.append(
                f'Emotion "{emotion}" was present on '
                f'{round(percentage, 2)}% of labeled frames.\n'
            )
    with document.create(Section('Looked away occurances')):
        document.append(
            f'Person also looked away {looked_away} times, which is '
            f'{looked_away_percentage}% of the time.'
        )
    document.generate_pdf(
        filepath='emotional_report',
        clean_tex=False,
        compiler='pdflatex',
    )
