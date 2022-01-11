import asyncio
from contextlib import contextmanager
import json
from typing import Awaitable, Dict, Callable
from loguru import logger
from pydantic import ValidationError
from app.events import Event, Publisher, Topic
from app.datastructures import CommandRequest
from .client_manager import Client

Handler = Callable[[Client, Publisher], Awaitable[None]]

__all__ = [
    "RouteMap",
    "ROOT_ROUTE",
    "RAW_VIDEO_ROUTE",
    "METRICS_ROUTE",
    "HEALTH_HTTP_ROUTE",
    "SNAPSHOT_HTTP_ROUTE",
    "CONFIG_HTTP_ROUTE",
]


ROOT_ROUTE = "/"
RAW_VIDEO_ROUTE = "/raw-video"
METRICS_ROUTE = "/metrics"
HEALTH_HTTP_ROUTE = "/health"
SNAPSHOT_HTTP_ROUTE = "/snapshot"
CONFIG_HTTP_ROUTE = "/config"


def generate_route_map() -> Dict[str, Handler]:
    return {
        ROOT_ROUTE: root_handler,
        RAW_VIDEO_ROUTE: simplex_error_handler,
        METRICS_ROUTE: simplex_error_handler,
    }


def set_error_msg(msg: str) -> str:
    error = {"error": msg}
    return json.dumps(error)


class RouteMap:
    def __init__(self):
        self.routes = generate_route_map()
        self.not_found_handler = not_found_handler

    def get_handler(self, path: str) -> Handler:
        handler = self.routes.get(path)
        return handler or not_found_handler


async def not_found_handler(client: Client, *_):
    await client.send(set_error_msg("path not found"))


async def simplex_error_handler(client: Client, *_):
    """One way communcation handler

    Server -> Client
    """
    async for _ in client.messages():  # type:ignore
        await client.send(
            set_error_msg("This path does not support duplex communication")
        )


async def root_handler(client: Client, publisher: Publisher):
    def processed_cmd_handler(evt: Event):
        if evt.data["sender_uuid"] == client.uuid:
            if "status" in evt.data:
                result_json = json.dumps({"status": "OK"})
            else:
                result_json = json.dumps({"error": evt.data["error"]})
            asyncio.create_task(client.send(result_json))

    with command_subscription(processed_cmd_handler, publisher):
        async for message in client.messages():
            try:
                msg_dict = json.loads(message)
                msg_dict["sender_uuid"] = client.uuid
                parsed = CommandRequest(**msg_dict)
                logger.debug(f"Request for command received: {parsed}")
                publisher.send_message(Topic.COMMAND_REQUEST, Event(data=parsed))
            except ValidationError as ex:
                logger.exception(ex)
                await client.send(json.dumps({"error": ex.errors()}))
                logger.warning(f"Command message failed parsing: {ex.errors}")
            except json.JSONDecodeError as ex:
                await client.send(set_error_msg(ex.msg))


@contextmanager
def command_subscription(callback, publisher: Publisher):
    handle = publisher.subscribe(Topic.COMMAND_PROCESSED, callback)
    try:
        yield
    finally:
        publisher.unsubscribe(handle)
