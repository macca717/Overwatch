import asyncio
from typing import Tuple
import arrow
from loguru import logger
from app.datastructures import AppConfig, AlertingOptions
from app.events import Topic, Event, Publisher


__all__ = ["run_scheduler_task"]


class TimeData:
    def __init__(self, *, start_time: str, end_time: str) -> None:
        """Helper for closure in run_scheduler_task

        Args:
            start_time (str): Start time (e.g "08:00")
            end_time (str): End time (e.g "12:00")
        """
        self._start: Tuple[int, int] = AlertingOptions.parse_time_str(start_time)
        self._end: Tuple[int, int] = AlertingOptions.parse_time_str(end_time)

    @property
    def start(self) -> Tuple[int, int]:
        return self._start

    def set_start(self, value: str):
        self._start = AlertingOptions.parse_time_str(value)

    @property
    def end(self) -> Tuple[int, int]:
        return self._end

    def set_end(self, value: str):
        self._end = AlertingOptions.parse_time_str(value)


async def run_scheduler_task(config: AppConfig, publisher: Publisher):
    capture_stopped = False
    test_mode = config.flags.test
    time_data = TimeData(
        start_time=config.alerting.start_time, end_time=config.alerting.end_time
    )

    def config_update_handler(event: Event):
        new_config: AppConfig = event.data
        time_data.set_start(new_config.alerting.start_time)
        time_data.set_end(new_config.alerting.end_time)
        logger.debug("Scheduler updated config times")

    publisher.subscribe(Topic.SYSTEM_CONFIG_UPDATE, config_update_handler)
    if test_mode:
        logger.warning("Scheduler running in test mode")

    while True:
        if not test_mode:  # Disable the scheduling if in test mode
            now = arrow.now()
            if check_if_scheduled(now, time_data.start, time_data.end):  # scheduled
                if capture_stopped:  # start
                    logger.debug("Capture scheduled, sending start event")
                    capture_stopped = False
                    # publisher.send_message(
                    #     Topic.SCHEDULER_CAPTURE_STOP, Event(data=capture_stopped)
                    # )
            else:  # Not scheduled
                if not capture_stopped:  # stop
                    logger.debug("Capture not scheduled, sending stop event")
                    capture_stopped = True
                    # publisher.send_message(
                    #     Topic.SCHEDULER_CAPTURE_STOP, Event(data=capture_stopped)
                    # )
            publisher.send_message(
                Topic.SCHEDULER_CAPTURE_STOP, Event(data=capture_stopped)
            )
        await asyncio.sleep(1)


def check_if_scheduled(
    now: arrow.Arrow, start: Tuple[int, int], end: Tuple[int, int]
) -> bool:
    start_time = now.replace(hour=start[0], minute=start[1])
    end_time = now.replace(hour=end[0], minute=end[1])
    if start_time <= now or end_time >= now:
        return True
    return False
