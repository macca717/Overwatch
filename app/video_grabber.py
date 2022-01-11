from __future__ import annotations
import asyncio
from collections import deque
from concurrent.futures import Executor
from datetime import datetime
import os
import time
from typing import Awaitable, Deque, List
import cv2 as cv
from loguru import logger
import numpy as np
from app.datastructures import AlertData, AppConfig
from app.events import Event, Publisher, Topic
from app.exceptions import OverwatchException

__all__ = ["VideoGrabber"]


def file_purge_task(directory: str, interval_hrs: int, delete_after_days: int = 7):
    """Video file purge task.

    Deletes old video files (.avi) in the specified directory.

    Args:
        directory (str): Video file directory.
        interval_hrs (int): Hours between the purge checks
        delete_after_days (int, optional): Days to keep the video files. Defaults to 7.
    """
    logger.debug("Beginning purge of video files")
    for filename in os.listdir(directory):
        if not filename.endswith(".avi"):
            continue
        else:
            full_path = directory + "/" + filename
            created = os.path.getmtime(full_path)
            if created + (delete_after_days * 60 * 60 * 24) < time.time():
                os.remove(full_path)
                logger.debug(f"Removed video file {full_path}")

    loop = asyncio.get_event_loop()
    next_call = loop.time() + (interval_hrs * 3600)
    loop.call_at(next_call, file_purge_task, directory, interval_hrs)
    logger.debug(f"Running next video file purge in {interval_hrs}hrs ")


class VideoGrabber:
    def __init__(
        self,
        config: AppConfig,
        publisher: Publisher,
        executor: Executor,
    ):
        """Video Grabber Class

        Saves the video footage prior to the alert being raised

        The duration of the video is equal to the "alerting.alert_time_s" value in the
        configuration.

        The write interval_hrs is limited by the "alerting.alert_time_s" value in the
        configuration.

        Args:
            config (AppConfig): Application config
            publisher (Publisher): Pulisher
            executor (Executor): Pool Executor
        """
        self.config = config
        self.publisher = publisher
        self.executor = executor
        self.save_path = config.server.video_save_dir
        self.video_deque: Deque[bytes] = deque()
        self.pending_writes: List[Awaitable[str]] = []
        self.frame_rate: int = 0
        self.last_write = -9999.9
        self.min_write_interval_s = (
            config.alerting.alert_time_s * 1.5
        )  # Add a 50% buffer for future tuning

    def _subscribe(self):
        self.publisher.subscribe(Topic.VIDEO_RAW_UPDATE, self._raw_video_update_handler)
        self.publisher.subscribe(Topic.SYSTEM_ALARM, self._alarm_raised_handler)

    def _raw_video_update_handler(self, evt: Event):
        self.video_deque.append(evt.data)

    def _alarm_raised_handler(self, evt: Event):
        alert_data: AlertData = evt.data
        if alert_data.is_test:
            logger.debug("Video file not saved (test alert)")
            return
        ready_for_next_write = self.last_write + self.min_write_interval_s < time.time()
        if ready_for_next_write:
            logger.debug("Starting video write task")
            video_data = list(self.video_deque)
            self.video_deque.clear()
            loop = asyncio.get_event_loop()
            self.pending_writes.append(
                loop.run_in_executor(
                    self.executor,
                    write_video_file,
                    self.save_path,
                    video_data,
                    self.frame_rate,
                )
            )
            self.last_write = time.time()
        else:
            logger.debug(
                f"Video file not written, interval_hrs since last write to short({self.min_write_interval_s}s)"
            )

    async def run(self):
        check_save_dir_exists(self.save_path)
        self._subscribe()
        loop = asyncio.get_event_loop()
        loop.call_soon(file_purge_task, self.save_path, 24)
        self.frame_rate = await self.determine_frame_rate()
        logger.debug(f"Calculated frame rate to be {self.frame_rate}")
        # Add a 50% buffer for future tuning
        max_length = self.frame_rate * self.min_write_interval_s
        # Reset the deque to the correct size for the framerate
        collected = list(self.video_deque)
        self.video_deque = deque(maxlen=int(max_length))
        self.video_deque.extend(collected)
        while True:
            for task in asyncio.as_completed(self.pending_writes):
                file_written = await task
                logger.debug(f"Video file written to {self.save_path}/{file_written}")
            self.pending_writes.clear()
            await asyncio.sleep(1)

    async def determine_frame_rate(self) -> int:
        capture_duration_s = 10
        await asyncio.sleep(10)  # Wait for the system to settle
        self.video_deque.clear()  # Clear the deque before starting
        await asyncio.sleep(capture_duration_s)
        assert (
            len(self.video_deque) > 0
        ), "The video deque was empty, can't determine frame rate"
        return int(len(self.video_deque) / capture_duration_s)


def write_video_file(
    path: str,
    data: List[bytes],
    fps: int,
    throttle_time: float | None = None,
) -> str:
    """Write the bytes data to a video file.

    Args:
        path (str): Save directory of the video file.
        data (List[bytes]): List of consecutive images as bytes.
        fps (int): Frame rate for the video
        throttle_time (float | None): Optional CPU throttling delay, if not set the write will be
        throttled to 1/3 of the frame rate (i.e the total write will take 1/3 of the video duration).
    Returns:
        (str): Filename of written file
    """
    out = None
    now = datetime.now()
    filename = now.strftime("%Y_%d_%m-%I_%M_%p") + ".avi"
    try:
        if throttle_time is None:
            throttle_time = (1 / fps) / 3.0
        # read the first frame to check the dimensions
        mat = cv.imdecode(np.frombuffer(data[0], np.uint8), -1)
        height, width = mat.shape
        fourcc = cv.VideoWriter_fourcc(*"MJPG")
        out = cv.VideoWriter(path + f"/{filename}", fourcc, fps, (width, height))
        for frame in data:
            buffer = np.frombuffer(frame, np.uint8)
            img = cv.imdecode(buffer, cv.IMREAD_COLOR)
            out.write(img.astype("uint8"))
            time.sleep(throttle_time)  # Throttle the write if required
    except KeyboardInterrupt:
        pass  # TODO: What happens if we get a SIGINT?
    finally:
        if out is not None:
            out.release()
    return filename


def check_save_dir_exists(save_dir):
    if not os.path.isdir(save_dir):
        raise OverwatchException("Error!, the video save directory does not exist")
