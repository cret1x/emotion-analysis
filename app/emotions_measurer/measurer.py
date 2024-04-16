from typing import Tuple, Optional, Final
import cv2
from pydantic_core import ValidationError
from app.emotions_measurer.frame_analyzer import FrameAnalyzer
from app.utils.utility_functions import (
    get_amount_of_frames,
    separate_frames_into_arrays,
    analyze_several_frames,
)
from app.data_models.models import EmotionalReport, Emotions
from multiprocessing.pool import Pool


THREADS_AMOUNT: Final[int] = 6
EMOTIONS_GRAPH_INTERPRETATION: Final[dict[Emotions, float]] = {
    Emotions.NEUTRAL: 0.0,
    Emotions.ANGRY: -0.75,
    Emotions.SAD: -0.5,
    Emotions.DISGUST: -0.25,
    Emotions.FEAR: -1.0,
    Emotions.SURPRISE: 0.5,
    Emotions.HAPPY: 1.0
}


class EmotionsMeasurer:
    """
    Class for videofiles measurement.
    An instance of the class is used initially when data from user is provided.
    It is an entry point for all analysis features implemented.
    """

    def __init__(
            self,
            input_path: str,
            thread_amount: Optional[int],
            mode: str,
    ) -> None:
        """
        Initialisation of the measurer.
        
        The given files are given by the user.
        During the initialization, the video capture is created.
        All esentials are being created.
        """
        self._frames_amount = 0
        if mode == '' or mode is None:
            self._input_path = input_path
            self._video_capture = cv2.VideoCapture(
                filename=self._input_path
            )
            self._size: Tuple[int, int] = (0, 0)
            self._thread_amount = thread_amount \
                if thread_amount is not None else THREADS_AMOUNT
            self._frames_amount = get_amount_of_frames(self._video_capture)
        self._emotions_occurances: dict[Emotions, int] = dict()
        self._looked_away = 0
        self._coordinates: list[Tuple[int, float]] = list()
        self._best_performance = dict()

    def analyse_prepared_video(self) -> None:
        """
        Shares info between processes and initializes the analysis.

        The following steps are taken:
        1. Separate frames between threads.
        2. Start threads according to users input.
        3. In each thread, the frames are being analyzed one by one.
        4. Afterwards, the results are gathered and registered.        
        """
        self._frames_arrays = separate_frames_into_arrays(
            self._video_capture,
            self._thread_amount,
            self._frames_amount
        )
        print('[INFO] Starting to analyse the video.')
        processes_arguments = [
            (self._frames_arrays[i], i + 1) \
                for i in range(self._thread_amount)
        ]
        results: list[dict[Emotions], int, list[Tuple[int, float]]] = list()
        with Pool(processes=self._thread_amount) as pool:
            try:
                results = pool.starmap(
                    func=analyze_several_frames,
                    iterable=processes_arguments,
                )
            except MemoryError:
                print(
                    '[WARNING] MemoryError was raised '
                    'while executing the analysis. '
                    'Try lowering the amount of threads.')
            finally:
                self._video_capture.release()
        for result in results:
            for emotion in result[0].keys():
                if Emotions(emotion) not in \
                        self._emotions_occurances.keys():
                    self._emotions_occurances[Emotions(emotion)] = 0
                self._emotions_occurances[Emotions(emotion)] += \
                    result[0][emotion]
            self._looked_away += result[1]
            for coordinate in result[2]:
                self._coordinates.append(
                    (
                        results.index(result) * \
                            (self._frames_amount // self._thread_amount) + \
                                coordinate[0],
                        coordinate[1],
                    )
                )
            for emotion in result[3].keys():
                if Emotions(emotion) not in \
                        self._best_performance.keys():
                    self._best_performance[Emotions(emotion)] = list()
                self._best_performance[Emotions(emotion)].append(result[3][emotion])

    def analyze_realtime(self) -> None:
        """Analyze emotions in realtime from camera."""
        best_performance_frame = dict()
        best_confidence = dict()
        brows_predictor = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml'
        )
        eye_predictor = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml'
        )
        self._video_capture = cv2.VideoCapture(0)
        while self._video_capture.isOpened():
            return_code, frame = self._video_capture.read()
            if not return_code:
                print('[INFO] Input was ended.')
                break
            self._frames_amount += 1
            emotions = list()
            try:
                emotions = FrameAnalyzer.analyze_frame(
                    frame,
                    brows_predictor,
                    eye_predictor
                )
            except Exception:
                self._looked_away += 1
            for emotion in emotions:
                try:
                    emotion_model = EmotionalReport.model_validate(emotion)
                    if Emotions(emotion_model.dominant_emotion) not in \
                            self._emotions_occurances.keys():
                        self._emotions_occurances[
                            Emotions(emotion_model.dominant_emotion)
                        ] = 0
                        best_confidence[
                            Emotions(emotion_model.dominant_emotion)
                        ] = -1
                    if best_confidence[Emotions(emotion_model.dominant_emotion)] < \
                            emotion_model.face_confidence:
                        best_performance_frame[
                            Emotions(emotion_model.dominant_emotion)
                        ] = frame
                        best_confidence[
                            Emotions(emotion_model.dominant_emotion)
                        ] = emotion_model.face_confidence
                    self._emotions_occurances[
                        Emotions(emotion_model.dominant_emotion)
                    ] += 1
                    cv2.putText(
                        frame,
                        emotion_model.dominant_emotion,
                        (frame.shape[0] // 2, frame.shape[1] // 2),
                        cv2.FONT_HERSHEY_COMPLEX,
                        0.9,
                        (255, 0, 0), 
                        3,       
                    )
                    self._coordinates.append(
                        (
                            self._frames_amount - 1,
                            EMOTIONS_GRAPH_INTERPRETATION[
                                Emotions(emotion_model.dominant_emotion)
                            ]
                        )
                    )
                except ValidationError:
                    try:
                        dominant = emotion['dominant_emotion']
                        if Emotions(dominant) not in \
                                self._emotions_occurances.keys():
                            self._emotions_occurances[Emotions(dominant)] = 0
                            self._best_performance[
                                Emotions(dominant)
                            ] = -1
                        self._emotions_occurances[Emotions(dominant)] += 1
                        cv2.putText(
                            frame,
                            dominant,
                            (frame.shape[0] // 2, frame.shape[1] // 2),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.9,
                            (255, 0, 0), 
                            3,       
                        )
                        self._coordinates.append(
                            (
                                self._frames_amount - 1,
                                EMOTIONS_GRAPH_INTERPRETATION[
                                    Emotions(dominant)
                                ]
                            )
                        )
                    except KeyError:
                        continue
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) == ord('q'):
                break
        self._video_capture.release()
        cv2.destroyAllWindows()
        for emotion in best_performance_frame:
            self._best_performance[Emotions(emotion)] = [best_performance_frame[emotion]]
