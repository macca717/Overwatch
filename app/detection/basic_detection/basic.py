from __future__ import annotations
from collections import deque
from itertools import islice
from typing import Deque, List, Tuple
import cv2 as cv
from loguru import logger
import numpy as np
import numpy.typing as npt
from app.datastructures import AppConfig, ProcessingOptions
from ..base import DetectionAlgorithm, MotionProcessor


__all__ = ["BasicDetectionAlgorithm"]


class BasicDetectionAlgorithm(DetectionAlgorithm):
    def __init__(self, config: AppConfig) -> None:
        """Basic motion detection algorithm

        Args:
            config (AppConfig): Application configuration.
        """
        self.config = config
        self.motion_processor: MotionProcessor = AverageMotionProcessor()
        self.alerting_options = config.alerting
        self.processing_options = config.processing
        self.detection_list: List[int] = []  # This is the raw pixel change
        motion_history_length = config.alerting.alert_time_s
        self.motion_history: Deque[int] = deque(
            np.zeros(motion_history_length, dtype=int).tolist(),
            maxlen=motion_history_length,
        )
        self.processeing_fps = config.processing.fps
        self.last_detection_update = False

    def update(self, img: npt.NDArray[np.float32]) -> bool:
        pixel_change = self.motion_processor.detect_motion(
            img,
            self.processing_options,
        )
        self.detection_list.append(pixel_change)
        if self._detection_list_full():
            self.last_detection_update = raise_alert(
                self.detection_list, self.motion_history, self.config
            )
            logger.trace(self.detection_list)
            self.detection_list.clear()
        return self.last_detection_update

    def _detection_list_full(self) -> bool:
        """Checks if if the curent detection list is full

        The list is full if it contains 1 second worth of data.
        """
        full_length = self.config.processing.fps
        return len(self.detection_list) >= full_length


def raise_alert(
    detected_motion_list: List[int], motion_history: Deque[int], config: AppConfig
) -> bool:
    low = config.processing.pixel_threshold_lo
    high = config.processing.pixel_threshold_hi
    if is_motion(np.array(detected_motion_list, dtype=int), low, high):
        motion_history.appendleft(1)
    else:
        motion_history.appendleft(0)
    if is_in_alarm(motion_history, config.alerting.min_movement_s):
        return True
    # logger.debug(f"Motion Deque: {motion_history}")
    return False


def is_motion(
    data: npt.NDArray[np.int32],
    pixel_chg_low: int,
    pixel_change_hi: int,
    min_frames_chg: int = 1,
) -> bool:
    """Determines if their has been overall movement in the frames
    i.e. If "min_frames_chg" frames have more than zero pixels then
    movement is True
    NB. The "min_frames_chg"is the amount of frame per second with the required threshold change
    A "min_frames_chg" of 1 would mean at least 1 frame has motion.
    Zero pixels is considered to be either no movement or not within the bandpass filter

    Args:
        data (np.array): Array of pixel changes in each frame
        pixel_chg_low (int): Minimum number of pixels to be considered movement
        pixel_change_hi (int): Maximum number of pixels to be considered movement
        min_frames_chg (int): Minimum number of frames to be considered movement. Default is 1
    Returns:
        bool: True if there is movement
    """
    data = bandpass_filter(data, low=pixel_chg_low, high=pixel_change_hi)
    if np.size(data[data > 0]) >= min_frames_chg:
        return True
    return False


def is_in_alarm(data: "Deque[int]", min_move_s: int) -> bool:
    """Applies a moving window of "min_move_s" to the data LIFO. Equivalent to: has
    there been movement for no less than "min_move_s" throughout the entire data
    capture.
    (t1, t2, t3, [t4, t5, t6, t7]-->, t8, t9)
    The window traverses the data array from latest to oldest movement data, if the
    window doesn't contain a "1" at anytime then the traverse is terminated and False
    returned
    Args:
        data (Deque[int]): Data LIFO
        min_move_s (int): Size of moving window
    Returns:
        bool: True if there is movement within the "min_move_s" window
    """
    if len(data) - min_move_s == 0:
        if 1 not in data:
            return False
        return True
    for i in range(len(data) - min_move_s):
        window = list(islice(data, i, i + min_move_s))
        if 1 not in window:
            return False
    return True


def bandpass_filter(
    data: npt.NDArray[np.int32], low: int, high: int
) -> npt.NDArray[np.int32]:
    """Filter the data only allowing values between hi and low to remain
    Excluded values are changed to -1

    Args:
        data (np.array): Array of changed pixel values
        low (int): min change level
        high (int): max change level

    Returns:
        np.array: Filtered array
    """
    data[data < low] = -1
    data[data > high] = -1
    return data


class AverageMotionProcessor:
    def __init__(self) -> None:
        """Average motion processing

        Detects the amount of changed pixels between image updates.
        """
        self._average_frame: npt.NDArray[np.float32] | None = None

    def detect_motion(
        self, img: npt.NDArray[np.float32], options: ProcessingOptions
    ) -> int:
        pixel_change, self._average_frame = detect_pixel_change(
            img, self._average_frame, options
        )
        return pixel_change


def detect_pixel_change(
    img: npt.NDArray[np.float32],
    average_frame: npt.NDArray[np.float32] | None,
    options: ProcessingOptions,
) -> Tuple[int, npt.NDArray[np.float32]]:
    dilation_iterations = options.dilation_iterations
    avg_weighting = options.avg_weighting
    fixed_lvl_threshold = options.fixed_lvl_threshold
    if average_frame is None:
        average_frame = img
    cv.accumulateWeighted(img, average_frame, avg_weighting)
    delta_frame = cv.absdiff(average_frame, img)
    _, thres_frame = cv.threshold(
        delta_frame, fixed_lvl_threshold, 255, cv.THRESH_BINARY
    )
    if dilation_iterations:
        thres_frame = cv.dilate(thres_frame, None, dilation_iterations)
    pixel_count = cv.countNonZero(thres_frame)
    return pixel_count, average_frame
