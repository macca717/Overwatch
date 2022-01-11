from __future__ import annotations
from copy import copy
import multiprocessing as mp
from queue import Empty
import signal
import time
from typing import List
from loguru import logger
import numpy as np
import numpy.typing as npt
from app.exceptions import CaptureError
from app.detection import BasicDetectionAlgorithm
from app.datastructures import AppConfig, DetectionData, CaptureUpdate
from app.bootstrap.logger import set_log_level
from .filter import BilateralFilter, GuassianBlurFilter
from .device import CaptureDevice, CameraCaptureDevice, FileCaptureDevice
from .helpers import resize_mat, to_gray_scale, mat_to_bytes

__all__ = ["DetectionProcess"]


def sig_term_handler(*_):
    raise SystemExit(0)


class DetectionProcess:
    def __init__(
        self,
        config: AppConfig,
    ) -> None:
        super().__init__()
        ctx = mp.get_context("spawn")
        self.msg_queue: "mp.Queue[CaptureUpdate]" = ctx.Queue()
        self.status_queue: "mp.Queue[DetectionData]" = ctx.Queue()
        self.raw_video_queue: "mp.Queue[bytes]" = ctx.Queue()
        self.queues: List[mp.Queue] = [
            self.msg_queue,
            self.status_queue,
            self.raw_video_queue,
        ]
        self.config = config
        self.detection_running = True
        self.sensitivity = 0  # TODO: Needed
        self.process_fps = 1 / config.processing.fps
        self.last_heartbeat = 0.0
        self.filter = GuassianBlurFilter(ksize=config.processing.gauss_ksize)
        self.capture_device = init_capture_device(config)
        self.last_capture_time: float = 0.0
        # self.filter = BilateralFilter(5, 200, 200)
        self.detection_algo = BasicDetectionAlgorithm(config)
        self.alarm_threshold_reached = False
        self.process_times: List[float] = []
        self.detection_process = ctx.Process(
            target=self._perform_detection, name="DetectionProcess", daemon=True
        )

    def _perform_detection(self):
        set_log_level(self.config.flags.log_level)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, sig_term_handler)
        logger.debug("Starting detection process")
        while True:
            try:
                self._process()
            except CaptureError:
                logger.debug("Capture error, restarting capture....")
            except ConnectionError:
                logger.warning("Connection error, resetting")
                time.sleep(1.0)

    def _process(self):
        for mat in self.capture_device.capture():
            process_start = time.perf_counter()
            mat = to_gray_scale(resize_mat(mat))
            raw = mat_to_bytes(mat)
            self.raw_video_queue.put_nowait(raw)
            if self.detection_running:
                self._perform_motion_detection(mat)
            else:
                self.alarm_threshold_reached = False
            self._check_for_messages()
            self._send_heart_beat()
            self.process_times.append(time.perf_counter() - process_start)

    def _perform_motion_detection(self, mat: npt.NDArray[np.uint8]):
        update_time_ready = (
            time.perf_counter() - self.last_capture_time > self.process_fps
        )
        if update_time_ready and self.detection_running:
            filtered = self.filter.apply(mat)
            mat_as_float = np.array(filtered, dtype=np.float32)
            last_threshold = self.alarm_threshold_reached
            self.alarm_threshold_reached = self.detection_algo.update(mat_as_float)
            if last_threshold != self.alarm_threshold_reached:
                logger.debug(
                    f"Alarm threshold reached changed to {self.alarm_threshold_reached}"
                )
            self.last_capture_time = time.perf_counter()

    def _check_for_messages(self):
        try:
            msg = self.msg_queue.get_nowait()
            self.detection_running = not msg["stop_processing"]
            self.sensitivity = msg["sensitivity"]
        except Empty:
            pass

    def _send_heart_beat(self):  # TODO: Refactor this
        now = time.time()
        if self.last_heartbeat + 1.0 < now:
            data = DetectionData(
                pid=self.detection_process.pid,
                running=self.detection_running,
                motion_detected=self.alarm_threshold_reached,
                frame_processing_times=copy(self.process_times),
            )
            self.status_queue.put_nowait(data)
            self.last_heartbeat = now
            self.process_times.clear()

    def start(self):
        self.detection_process.start()

    def shutdown(self, timout: float = 5):
        logger.debug("Shutting down detection")
        for queue in self.queues:
            queue.close()
            queue.join_thread()
        logger.debug("Sending SIGTERM to detection process")
        self.detection_process.terminate()
        self.detection_process.join(timeout=timout)
        if self.detection_process.is_alive():
            self.detection_process.kill()
        logger.debug("Shutdown complete")

    def send_msg(self, msg: CaptureUpdate):
        self.msg_queue.put(msg)

    def get_video_data(self) -> bytes | None:
        try:
            return self.raw_video_queue.get_nowait()
        except Empty:
            return None

    def get_status_data(self) -> DetectionData | None:
        try:
            return self.status_queue.get_nowait()
        except Empty:
            return None


def init_capture_device(config: AppConfig) -> CaptureDevice:
    if config.flags.file:
        logger.debug(f"Loading video file from {config.flags.file}")
        return FileCaptureDevice(config.flags.file)
    logger.debug(f"Running video file from {config.camera.url}")
    return CameraCaptureDevice(config.camera.url)
