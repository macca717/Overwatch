from __future__ import annotations
import asyncio
from contextlib import suppress
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
import time
from typing import cast, Optional
from aiohttp import ClientSession, ClientError
from loguru import logger
from app.config import save_config_to_file, TomlConfigSerializer
from app.events import Event, Publisher, Topic
from app.datastructures import (
    AlertData,
    AppConfig,
    CommandRequest,
    State,
    SystemCommand,
    SystemStatus,
    TestCmdData,
    SilenceCmdData,
    ConfigUpdateData,
    ShutdownData,
)
from app.capture import run_detection_task
from app.metrics import Metrics
from app.alerter import Alerter
from app.video_grabber import VideoGrabber
import app.web_server as web
import app.websocket_server as ws
from app.scheduler import run_scheduler_task
from .state_machine import ConditionsNotMet, StateMachine, transition, InvalidStartState

__all__ = ["run_system_tasks"]


async def run_system_tasks(
    config: AppConfig, publisher: Publisher, process_pool: ProcessPoolExecutor
):
    """Run the system tasks

    Args:
        config (AppConfig): Application configuration
        publisher (Publisher): Main publisher
        process_pool (ProcessPoolExecutor): Process pool for async operations
    """
    await System(config, publisher, process_pool).run()


class System:  # pylint: disable=too-few-public-methods
    def __init__(
        self, config: AppConfig, publisher: Publisher, process_pool: ProcessPoolExecutor
    ):
        self.config = config
        self.publisher = publisher
        self.process_pool = process_pool
        self.thread_pool = ThreadPoolExecutor(thread_name_prefix="system")
        self.state_machine = SystemState(
            publisher,
            config,
        )
        self.config_file_serializer = TomlConfigSerializer()
        self._command_queue: asyncio.Queue[CommandRequest] = asyncio.Queue()

    async def run(self):
        logger.info("Starting system")
        logger.debug(f"System state is {self.state_machine}")
        self._subscribe()
        Metrics(self.publisher).run()
        run_periodic_tasks(self.config, self.publisher)
        await asyncio.gather(
            run_sub_tasks(self.config, self.publisher, self.process_pool),
            self._consume_command_requests(),
            return_exceptions=False,
        )

    def _subscribe(self):
        self.publisher.subscribe(
            Topic.CAPTURE_DETECTION_UPDATE, self._detection_update_handler
        )
        self.publisher.subscribe(Topic.COMMAND_REQUEST, self._command_request_handler)
        self.publisher.subscribe(
            Topic.SCHEDULER_CAPTURE_STOP, self._scheduler_update_handler
        )

    def _detection_update_handler(self, event: Event):
        motion_detected: bool = event.data
        if motion_detected:
            with suppress(ConditionsNotMet):
                self.state_machine.alarm(
                    AlertData(msg="Alarm", is_test=False, exclusion_list=[])
                )
        else:
            with suppress(InvalidStartState):  # Reset if in alarm
                self.state_machine.alarm_reset()

    def _command_request_handler(self, event: Event):
        cmd_request: CommandRequest = event.data
        asyncio.create_task(self._command_queue.put(cmd_request))

    def _scheduler_update_handler(self, event: Event):
        stop: bool = event.data
        try:
            if stop:
                self.state_machine.turn_off()
            else:
                self.state_machine.turn_on()
        except (InvalidStartState, ConditionsNotMet) as ex:
            logger.trace(f"State Transition error: {ex}")

    async def _consume_command_requests(self):
        while True:
            cmd_request = await self._command_queue.get()
            logger.debug(f"Got command {cmd_request}")
            command = cmd_request.command
            reply_msg = {"sender_uuid": cmd_request.sender_uuid, "status": "OK"}
            if command == SystemCommand.CONFIG_UPDATE:
                config_data = cast(ConfigUpdateData, cmd_request.data)
                new_config = config_data.config
                self.config = config_data.config
                self.publisher.send_message(
                    Topic.SYSTEM_CONFIG_UPDATE, Event(data=self.config)
                )
                self.thread_pool.submit(
                    partial(
                        save_config_to_file,
                        new_config,
                        self.config_file_serializer,
                        path=new_config.flags.config_path,
                    ),
                )

            elif command == SystemCommand.SHUTDOWN:

                def shutdown():
                    raise SystemExit(0)

                shutdown_data = cast(ShutdownData, cmd_request.data)
                asyncio.get_event_loop().call_at(shutdown_data.shutdown_in, shutdown)
            elif command == SystemCommand.SILENCE:
                try:
                    silence_data = cast(SilenceCmdData, cmd_request.data)
                    self.state_machine.silence(silence_data.silence_for)
                except InvalidStartState as ex:
                    del reply_msg["status"]
                    reply_msg["error"] = str(ex)

            elif command == SystemCommand.TEST:
                test_data = cast(TestCmdData, cmd_request.data)
                alert_data = AlertData("Test, Test", True, test_data.excluded)
                self.publisher.send_message(Topic.SYSTEM_ALARM, Event(alert_data))
            else:
                raise RuntimeError(f"Unhandled Command {command}")

            self.publisher.send_message(Topic.COMMAND_PROCESSED, Event(data=reply_msg))


def run_periodic_tasks(config: AppConfig, publisher: Publisher):
    loop = asyncio.get_event_loop()
    loop.call_soon(run_tick_task, publisher)


async def run_sub_tasks(
    config: AppConfig, publisher: Publisher, process_pool: ProcessPoolExecutor
) -> None:
    alerter = Alerter(config, publisher)
    video_grabber = VideoGrabber(config, publisher, process_pool)
    websocket_server = ws.WebSocketServer(config, publisher)
    tasks = [
        run_detection_task(config, publisher),
        alerter.run(),
        video_grabber.run(),
        websocket_server.start(),
        run_webserver_task(config),
        run_scheduler_task(config, publisher),
    ]
    # Fail hard and fast here
    await asyncio.gather(*tasks, return_exceptions=False)


def run_tick_task(publisher: Publisher):
    loop = asyncio.get_event_loop()
    loop.call_later(1, run_tick_task, publisher)
    publisher.send_message(Topic.SYSTEM_TICK, Event())


async def run_webserver_task(config: AppConfig):
    port = config.server.webserver_port
    url = f"http://{config.server.host_name}:{port}/health"
    loop = asyncio.get_event_loop()
    session: ClientSession | None = None
    web_server: web.Server | None = None
    while True:
        try:
            web_server = web.Server(config)
            await loop.run_in_executor(None, web_server.start)
            session = ClientSession(raise_for_status=True)
            while True:
                await asyncio.sleep(60)
                await session.get(url, timeout=5)
        except ClientError as ex:
            logger.error(f"The webserver failed the health check: {ex}")
        finally:
            if session:
                await session.close()
            if web_server:
                web_server.shutdown()


########### StateMachine ##########


# Conditions


def alarm_hysteresis_finished(machine: SystemState, *_) -> bool:
    now = time.time()
    if machine.last_alarm == 0.0:
        return True
    return now > machine.last_alarm + machine.alarm_hysteresis


def not_silenced(machine: StateMachine, *_) -> bool:
    return not machine.state == State.SILENCED


class SystemState(StateMachine):
    def __init__(
        self,
        publisher: Publisher,
        config: AppConfig,
    ):
        # TODO: Refactor after self._status added
        self._config = config
        self.alarm_hysteresis = config.alerting.alarm_hysteresis_s
        self.publisher = publisher
        self._status = SystemStatus()
        self.last_alarm = 0.0
        self.initial_alarm = 0.0
        self._initial_alarm_duration_s = config.alerting.initial_alarm_duration_m * 60
        self._unsilence_timer: Optional[asyncio.TimerHandle] = None
        super().__init__(State.ON)
        self._subscribe()

    def _subscribe(self):
        self.publisher.subscribe(Topic.SYSTEM_TICK, self._tick_handler)
        self.publisher.subscribe(
            Topic.SYSTEM_CONFIG_UPDATE, self._config_update_handler
        )

    def _tick_handler(self, *_):
        self._status = SystemStatus.update(self._status, time_stamp=time.time())
        self.publisher.send_message(
            Topic.SYSTEM_STATUS_UPDATE, Event(data=self._status.copy())
        )

    def _config_update_handler(self, event: Event):
        logger.debug("State Machine updating configuration")
        new_config = cast(AppConfig, event.data)
        self.alarm_hysteresis = new_config.alerting.alarm_hysteresis_s
        self._initial_alarm_duration_s = (
            new_config.alerting.initial_alarm_duration_m * 60
        )

    def _unsilence_callback(self):
        self.unsilence()

    @transition(
        source=[State.OFF, State.SILENCED],
        target=State.ON,
        conditions=[not_silenced],
    )
    def turn_on(self):
        logger.debug(f"System state changed to {self}")
        self._status = SystemStatus.update(
            self._status, state=self.state, initial_alarm=self.initial_alarm
        )

    @transition(source=[State.ON, State.ALARM, State.SILENCED], target=State.OFF)
    def turn_off(self):
        logger.debug(f"System state changed to {self}")
        self._status = SystemStatus.update(
            self._status, state=self.state, initial_alarm=self.initial_alarm
        )

    @transition(
        source=[State.ON, State.ALARM, State.SILENCED],
        target=State.ALARM,
        conditions=[alarm_hysteresis_finished, not_silenced],
    )
    def alarm(self, data: AlertData):
        logger.debug(f"System state changed to {self}")
        self.last_alarm = time.time()
        if self.initial_alarm + self._initial_alarm_duration_s < self.last_alarm:
            self.initial_alarm = self.last_alarm
        self.publisher.send_message(Topic.SYSTEM_ALARM, Event(data=data))
        self._status = SystemStatus.update(
            self._status, state=self.state, initial_alarm=self.initial_alarm
        )

    @transition(source=[State.ALARM, State.ON, State.SILENCED], target=State.SILENCED)
    def silence(self, silenced_for: float):
        logger.debug(f"System state changed to {self}")
        if self._unsilence_timer:
            self._unsilence_timer.cancel()
        self._unsilence_timer = asyncio.get_event_loop().call_later(
            silenced_for, self._unsilence_callback
        )
        self._status = SystemStatus.update(
            self._status,
            state=self.state,
            initial_alarm=self.initial_alarm,
            silenced_till=time.time() + silenced_for,
        )

    @transition(source=[State.ALARM], target=State.ON)
    def alarm_reset(self):
        logger.debug("Alarm reset to on")
        self._status = SystemStatus.update(
            self._status,
            state=self.state,
        )

    @transition(source=[State.SILENCED], target=State.ON)
    def unsilence(self):
        logger.debug("Unsilencing system")
        self._status = SystemStatus.update(
            self._status,
            state=self.state,
        )
