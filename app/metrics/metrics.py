from __future__ import annotations
from loguru import logger
import psutil
from app.datastructures import CaptureMetrics
from app.events import Event, Publisher, Topic
from .calc import calc_metrics

__all__ = ["Metrics"]


class Metrics:
    def __init__(self, publisher: Publisher):
        """System Metrics

        Class to handle system metrics.
        Updated metrics are published to 'Topic.SYSTEM_METRICS_READY'

        Args:
            publisher (Publisher): Application publisher object
        """
        self.publisher = publisher
        self.sys_process = psutil.Process()
        self.cap_pid: int | None = None
        self.cap_process: psutil.Process | None = None

    def _subscribe(self):
        self.publisher.subscribe(
            Topic.CAPTURE_METRICS_UPDATE, self._capture_metrics_handler
        )

    def _capture_metrics_handler(self, event: Event) -> None:
        data: CaptureMetrics = event.data
        cap_pid_changed = self.cap_pid is None or self.cap_pid != data.pid
        if cap_pid_changed:  # If the capture process is (re)started we new the new pid
            self.cap_pid = data.pid
            self.cap_process = psutil.Process(self.cap_pid)
        if self.cap_process is not None:
            metrics = calc_metrics(
                self.sys_process,
                self.cap_process,
                data.frame_processing_times,
            )
            self.publisher.send_message(Topic.SYSTEM_METRICS_READY, Event(data=metrics))
        else:
            logger.warning("The capture is None")

    def run(self):
        """Start the metric capture process."""
        self._subscribe()
