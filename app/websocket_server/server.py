from __future__ import annotations
import asyncio
import http
import time
from loguru import logger
from websockets.exceptions import ConnectionClosedError
import websockets.legacy.server as ws
from app.datastructures import AppConfig, MetricsData, SystemStatus
from app.events import Publisher, Event, Topic
from .client_manager import Client, ClientList
from .route_handler import (
    RouteMap,
    ROOT_ROUTE,
    RAW_VIDEO_ROUTE,
    METRICS_ROUTE,
    HEALTH_HTTP_ROUTE,
    SNAPSHOT_HTTP_ROUTE,
    CONFIG_HTTP_ROUTE,
)

__all__ = ["WebSocketServer"]


class WebSocketServer:

    SNAPSHOT_INTERVAL = 1.0

    def __init__(self, config: AppConfig, publisher: Publisher):
        """Web Socket Server

        Args:
            config (AppConfig): Application configuration
            publisher (Publisher): Application publisher/Subscriber
        """
        self._config = config
        self.host = config.server.host_name
        self.port = config.server.websocket_port
        self.pub = publisher
        self.clients = ClientList()
        self.routes = RouteMap()
        self._stop = asyncio.Event()
        self._last_snapshot = time.time()
        self._snapshot: bytes = b""
        self._subscribe()

    def _subscribe(self):
        self.pub.subscribe(Topic.SYSTEM_STATUS_UPDATE, self._status_update_handler)
        self.pub.subscribe(Topic.VIDEO_RAW_UPDATE, self._raw_video_update_handler)
        self.pub.subscribe(Topic.SYSTEM_METRICS_READY, self._metrics_update_handler)
        self.pub.subscribe(Topic.SYSTEM_SHUTDOWN, self._shutdown_handler)
        self.pub.subscribe(Topic.SYSTEM_CONFIG_UPDATE, self._config_update_handler)

    def _shutdown_handler(self, *_):
        self._stop.set()

    def _status_update_handler(self, evt: Event):
        status: SystemStatus = evt.data
        data = status.json(by_alias=True)
        self._broadcast(ROOT_ROUTE, data)

    def _raw_video_update_handler(self, evt: Event):
        if self._last_snapshot + WebSocketServer.SNAPSHOT_INTERVAL < time.time():
            self._snapshot = evt.data
            self._last_snapshot = time.time()
        self._broadcast(RAW_VIDEO_ROUTE, evt.data)

    def _metrics_update_handler(self, evt: Event):
        metrics: MetricsData = evt.data
        self._broadcast(METRICS_ROUTE, metrics.json(by_alias=True))

    def _config_update_handler(self, evt: Event):
        logger.debug("Websocket server updating configuration")
        new_config: AppConfig = evt.data
        self._config = new_config

    def _broadcast(self, path: str, data: str | bytes) -> None:
        for coro in [
            client.send(data) for client in self.clients if client.path == path
        ]:
            asyncio.create_task(coro)

    async def http_interceptor(self, path: str, request_headers):
        if path == HEALTH_HTTP_ROUTE:
            return http.HTTPStatus.OK, [], b"OK\n"
        elif path == SNAPSHOT_HTTP_ROUTE:
            return (
                http.HTTPStatus.OK,
                [
                    ("Content-type", "image/jpeg"),
                    ("Content-length", len(self._snapshot)),
                    ("Cache-control", "no-cache"),
                    ("Access-Control-Allow-Origin", "*"),
                    ("Time", self._last_snapshot),
                ],
                self._snapshot,
            )
        elif path == CONFIG_HTTP_ROUTE:
            return (
                http.HTTPStatus.OK,
                [
                    ("Content-type", "application/json"),
                    ("Cache-control", "no-cache"),
                    ("Access-Control-Allow-Origin", "*"),
                    ("Time", self._last_snapshot),
                ],
                self._config.json().encode("UTF-8"),
            )
        # Allow WS requests to pass through

    async def route_handler(self, websocket: ws.WebSocketServerProtocol, path: str):
        client = Client(websocket, path)
        try:
            with self.clients.register(client):
                handler = self.routes.get_handler(path)
                await handler(client, self.pub)
        except ConnectionClosedError:
            logger.debug(f"Client disconnected ({client:short})")

    async def start(self):
        async with ws.serve(
            self.route_handler,
            self.host,
            self.port,
            process_request=self.http_interceptor,
        ) as server:
            await self._stop.wait()
            server.close()
            await server.wait_closed()
