import asyncio
import time
from loguru import logger
from app.datastructures import AppConfig, CaptureUpdate, CaptureMetrics
from app.events import Event, Publisher, Topic
from .detection_process import DetectionProcess


__all__ = ["run_detection_task"]


class Capture:
    def __init__(self, config: AppConfig, publisher: Publisher):
        self.config = config
        self.publisher = publisher
        self.process = DetectionProcess(config)
        self.watchdog_interval_s: float = 30
        self.last_watchdog_update = time.time()
        self._subscribe()

    def _subscribe(self):
        self.publisher.subscribe(
            Topic.SCHEDULER_CAPTURE_STOP, self._scheduler_update_handler
        )
        self.publisher.subscribe(Topic.SYSTEM_CONFIG_UPDATE, self.config_update_handler)

    def _scheduler_update_handler(self, evt: Event):
        stop: bool = evt.data  # reversed
        self.process.send_msg((CaptureUpdate(stop_processing=stop, sensitivity=50)))

    def config_update_handler(self, event: Event):
        new_config: AppConfig = event.data
        self.config = new_config
        self._update_process_config(new_config)

    async def run(self):
        logger.info("Starting detection process")
        self.process.start()
        try:
            while True:
                if video_data := self.process.get_video_data():
                    self.publisher.send_message(
                        Topic.VIDEO_RAW_UPDATE, Event(data=video_data)
                    )
                if status_data := self.process.get_status_data():
                    self.publisher.send_message(
                        Topic.CAPTURE_METRICS_UPDATE,
                        Event(
                            data=CaptureMetrics(
                                pid=status_data.pid,
                                frame_processing_times=status_data.frame_processing_times,
                            )
                        ),
                    )
                    self.publisher.send_message(
                        Topic.CAPTURE_DETECTION_UPDATE,
                        Event(data=status_data.motion_detected),
                    )
                    self.last_watchdog_update = time.time()
                if check_watchdog_expired(
                    self.last_watchdog_update, self.watchdog_interval_s
                ):
                    logger.error(
                        "The watchdog timer expired for the detection process, restarting process"
                    )
                    self.process.shutdown()
                    self.process = DetectionProcess(self.config)
                    self.process.start()
                    self.last_watchdog_update = time.time()
                await asyncio.sleep(0.033)  # 30 fps TODO: Make variable
        finally:
            self.process.shutdown()

    def _update_process_config(self, config: AppConfig) -> None:
        # TODO: This is a bit of a heavy hand approach here
        logger.debug("Updating detection process config")
        self.process.shutdown()
        self.process = DetectionProcess(config)
        self.process.start()


async def run_detection_task(config: AppConfig, publisher: Publisher) -> None:
    process = Capture(config, publisher)
    await process.run()


def check_watchdog_expired(last_watchdog_update, watchdog_interval_s) -> bool:
    now = time.time()
    return last_watchdog_update + watchdog_interval_s < now
