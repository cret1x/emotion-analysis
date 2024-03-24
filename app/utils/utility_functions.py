from datetime import datetime
import os
from typing import Final, Tuple
from cv2 import VideoCapture
import cv2
import pathlib
from app.data_models.models import EmotionalReport, Emotions
from app.emotions_measurer.frame_analyzer import FrameAnalyzer
from pydantic_core import ValidationError
from pylatex import (
    Document,
    Section,
    TikZ,
    Plot,
    Axis,
)


LOOKED_AWAY_THRESHOLD: Final[float] = 7.5
HAPPY_TO_ANGRY_DIFFERENCE_THRESHOLD: Final[float] = 10.0
HAPPY_TO_SAD_DIFFERENCE_THRESHOLD: Final[float] = 10.0
NEUTRAL_TO_SURPRISED_THRESHOLD: Final[float] = 10.0
FEAR_THRESHOLD: Final[float] = 5.0
HAPPY_THRESHOLD: Final[float] = 20.0
DISGUST_ANGRY_THRESHOLD: Final[float] = 12.5
SAD_THRESHOLD: Final[float] = 15.0


EMOTIONS_GRAPH_INTERPRETATION: Final[dict[Emotions, float]] = {
    Emotions.NEUTRAL: 0.0,
    Emotions.ANGRY: -0.75,
    Emotions.SAD: -0.5,
    Emotions.DISGUST: -0.25,
    Emotions.FEAR: -1.0,
    Emotions.SURPRISE: 0.5,
    Emotions.HAPPY: 1.0
}



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
) -> Tuple[dict[Emotions, int], int, list[Tuple[int, float]]]:
    """
    Analyze frames for emotions.
    
    Main points:
    1. The method is created for threads to work with.
    2. It creates the classifier and goes frame by frame through the list.
    3. Each 100 frames, a message is being written for tracking.
    4. The reports are being validated by BaseModel and the report is passed back.
    """
    coordinates: list[Tuple[int, float]] = list()
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
    for i in range(len(frames)):
        emotions = list()
        try:
            emotions = FrameAnalyzer.analyze_frame(
                frames[i],
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
                coordinates.append(
                    (
                        i,
                        EMOTIONS_GRAPH_INTERPRETATION[
                            Emotions(emotion_model.dominant_emotion)
                        ]
                    )
                )
                cv2.putText(
                    frames[i],
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
                    coordinates.append(
                        (
                            i,
                            EMOTIONS_GRAPH_INTERPRETATION[
                                Emotions(dominant)
                            ]
                        )
                    )
                    cv2.putText(
                        frames[i],
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
    return analysis_result, looked_away, coordinates


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
    print('[INFO] For more detailed response go through the pdf report.')


def generate_latex_report_from_result_dictionary(
        result: dict[Emotions, int],
        looked_away: int,
        overall_frames_amount: int,
        coordinates: list[Tuple[int, float]],
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
    geometry_options = {'tmargin': '1cm', 'lmargin': '1cm'}
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
            f'Person looked away {looked_away} times, which is '
            f'{looked_away_percentage}% of the time.'
        )
    with document.create(Section('Key takeaways from the video')):
        document.append(
            'These are the main takeaways from the given parameters:\n'
        )
        takeaways = get_textual_takeaways_on_emotional_state(
            sorted_percentages,
            looked_away_percentage,
        )
        if takeaways == '':
            document.append('there were no outliars in the video.')
        else:
            document.append(takeaways)
    with document.create(Section('Graphical appearance')):
        document.append('There are the following marks for each emotion:\n')
        for emotion, value in EMOTIONS_GRAPH_INTERPRETATION.items():
            document.append(f'Emotion "{emotion}" level: {value}.\n')
        document.append(
            'Lower there is an interpretation of emotional shifts via graphic.\n'
        )
        with document.create(TikZ()):
            plot_options = 'height=25cm, width=20cm'
            with document.create(Axis(options=plot_options)) as plot:
                plot.append(Plot(name='emotional report', coordinates=coordinates))
    document.generate_pdf(
        filepath='emotional_report',
        clean_tex=False,
        compiler='pdflatex',
    )


def get_percentages_from_results(
        result: dict[Emotions, int],
        looked_away: int,
        overall_frames_amount: int,
):
    """Get percentages of occurances based on provided parameters."""
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
    result_percentages: dict[str, float] = dict()
    result_percentages['lookedAway'] = looked_away_percentage
    result_percentages['neutral'] = sorted_percentages[Emotions.NEUTRAL] \
        if Emotions.NEUTRAL in sorted_percentages.keys() else 0.0
    result_percentages['angry'] = sorted_percentages[Emotions.ANGRY] \
        if Emotions.ANGRY in sorted_percentages.keys() else 0.0
    result_percentages['sad'] = sorted_percentages[Emotions.SAD] \
        if Emotions.SAD in sorted_percentages.keys() else 0.0
    result_percentages['disgust'] = sorted_percentages[Emotions.DISGUST] \
        if Emotions.DISGUST in sorted_percentages.keys() else 0.0
    result_percentages['surprise'] = sorted_percentages[Emotions.SURPRISE] \
        if Emotions.SURPRISE in sorted_percentages.keys() else 0.0
    result_percentages['fear'] = sorted_percentages[Emotions.FEAR] \
        if Emotions.FEAR in sorted_percentages.keys() else 0.0
    result_percentages['happy'] = sorted_percentages[Emotions.HAPPY] \
        if Emotions.HAPPY in sorted_percentages.keys() else 0.0
    return result_percentages


def get_textual_takeaways_on_emotional_state(
        emotions_percentages: dict[Emotions, float],
        looked_away_percentage: float,
) -> str:
    takeaways = list()
    if looked_away_percentage >= LOOKED_AWAY_THRESHOLD:
        takeaway = 'The person looked away quite often'
        if Emotions.FEAR in emotions_percentages.keys():
            if emotions_percentages[Emotions.FEAR] >= FEAR_THRESHOLD:
                takeaway += (
                    ', which combined with the fact, that fear emotion was displayed, may '
                    'signal that the person is worried or is feeling endangered. '
                    'The best way to approach the situation is to contact the person '
                    'and ensure ones safety'
                )
        if Emotions.HAPPY in emotions_percentages.keys():
            if emotions_percentages[Emotions.HAPPY] >= HAPPY_THRESHOLD:
                takeaway += (
                    ', at the same time, happiness emotion was seen a lot, '
                    'so a conclusion may be drawn, that the person is feeling '
                    'excited and impatient about some further occurance'
                )
            takeaway += (
                '. All in all, that might be due to the fact, '
                'that the person is being distracted by something, '
                'or, in case if that is some kind of examination, is trying to cheat'
            )
        takeaways.append(takeaway)
    if Emotions.HAPPY in emotions_percentages.keys() \
            and Emotions.SAD in emotions_percentages.keys():
        if abs(emotions_percentages[Emotions.HAPPY] - emotions_percentages[Emotions.SAD]) < \
                HAPPY_TO_SAD_DIFFERENCE_THRESHOLD:
            takeaway = (
                'Throughout the video, the person displayed mixed emotions, as '
                'sadness is somewhat close to happiness in terms of occurances'
            )
            takeaways.append(takeaway)
    if Emotions.HAPPY in emotions_percentages.keys() \
            and Emotions.ANGRY in emotions_percentages.keys():
        if abs(emotions_percentages[Emotions.HAPPY] - emotions_percentages[Emotions.ANGRY]) < \
                HAPPY_TO_ANGRY_DIFFERENCE_THRESHOLD:
            takeaway = (
                'The person was showing mixed emotions in terms of the mood, '
                'as anger was mixed with the happiness. That may be tied '
                'to the fact that person is exhausted or burnt out'
            )
            takeaways.append(takeaway)
    if Emotions.NEUTRAL in emotions_percentages.keys() and \
            Emotions.SURPRISE in emotions_percentages.keys():
        if abs(emotions_percentages[Emotions.NEUTRAL] - emotions_percentages[Emotions.SURPRISE]) < \
                NEUTRAL_TO_SURPRISED_THRESHOLD:
            takeaway = (
                'In terms of neutral appearance, it was seldom mixed with '
                'suprised state, which outlines that the person is either curious, '
                'or hears, or experiences something new and unexpected'
            )
            takeaways.append(takeaway)
    if emotions_percentages.get(Emotions.ANGRY, 0.0) + \
            emotions_percentages.get(Emotions.DISGUST, 0.0) >= DISGUST_ANGRY_THRESHOLD:
        takeaway = (
            'Anger and disgust emotions were recorded '
            'for a substantial amount of time, which might be a signal '
            'to person being heavily disstressed or irritated'
        )
        takeaways.append(takeaway)
    if emotions_percentages.get(Emotions.SAD, 0.0) > SAD_THRESHOLD:
        takeaway = (
            'Sadness was displayed on a big chunk of the video. '
            'With that being said, it is highly recomended to approach '
            'the person and try to comfort him or her.'
        )
        takeaways.append(takeaway)
    return '.\n'.join(takeaways)
