from typing import Tuple, Optional, Final
from deepface import DeepFace
import cv2
from app.utils.utility_functions import (
    get_amount_of_frames,
    separate_frames_into_arrays,
    analyze_several_frames,
)
from app.emotions_measurer.frame_analyzer import FrameAnalyzer
from app.data_models.models import *
from pydantic_core import ValidationError
from multiprocessing.pool import Pool


THREADS_AMOUNT: Final[int] = 4


class EmotionsMeasurer:
    """Class for media measurement."""

    def __init__(self, input_path: str, thread_amount: Optional[int]) -> None:
        """Initialisation of the measurer."""
        self._input_path = input_path
        self._video_capture = cv2.VideoCapture(filename=self._input_path)
        self._size: Tuple[int, int] = (0, 0)
        self._thread_amount = thread_amount \
            if thread_amount != None else THREADS_AMOUNT
        self._frames_amount = get_amount_of_frames(self._video_capture)
        self._emotions_occurances: dict[Emotions, int] = dict()

    def analyse_prepared_video(self):
        frames_arrays = separate_frames_into_arrays(
            self._video_capture,
            self._thread_amount,
            self._frames_amount
        )
        processes_arguments = [
            (frames_arrays[i], i + 1) for i in range(self._thread_amount)
        ]
        results: list[dict[Emotions], int] = list()
        with Pool(processes=self._thread_amount) as pool:
            try:
                results = pool.starmap(
                    analyze_several_frames,
                    processes_arguments
                )
            except MemoryError:
                print(
                    'MemoryError was raised while executing the analysis. '
                    'Try lowering the amount of threads.')
            finally:
                self._video_capture.release()
        for result in results:
            print(result)
            for emotion in result.keys():
                if Emotions(emotion) not in self._emotions_occurances.keys():
                    self._emotions_occurances[Emotions(emotion)] = 0
                self._emotions_occurances[Emotions(emotion)] += 1
        print(self._emotions_occurances)
            
