from __future__ import annotations
from contextlib import contextmanager, suppress
from typing import AsyncGenerator, Dict, Union
from uuid import UUID, uuid4
from loguru import logger
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.server import WebSocketServerProtocol


class ClientNotConnectedException(Exception):
    """Raised if client is not connected"""


class ClientList:
    def __init__(self) -> None:
        """Connected client list"""
        self._clients: Dict[UUID, Client] = {}

    def get(self, uuid_str: str) -> Client:
        """Get a connected client

        Args:
            uuid_str (str): UUID of the client

        Raises:
            ClientNotConnectedException: If UUID is not connected

        Returns:
            Client: A connected client
        """
        uuid = UUID(uuid_str)
        if uuid not in self._clients:
            raise ClientNotConnectedException()
        return self._clients[uuid]

    def __iter__(self):
        return self._clients.values().__iter__()

    def __len__(self):
        return self._clients.__len__()

    def __contains__(self, client: Client) -> bool:
        return client.uuid in self._clients

    @contextmanager
    def register(self, client: Client):
        try:
            self._clients[client.uuid] = client
            logger.debug(f"Adding client ({client})")
            yield
        finally:
            logger.debug(f"Removing client ({client:short})")
            del self._clients[client.uuid]


class Client:
    def __init__(self, websocket: WebSocketServerProtocol, path: str) -> None:
        self._connection = websocket
        self._path = path
        self._uuid = uuid4()

    @property
    def uuid(self) -> UUID:
        return self._uuid

    @property
    def path(self) -> str:
        return self._path

    async def messages(self) -> AsyncGenerator[Union[str, bytes], None]:
        """Get pending received messages.

        Yields:
            [Union[str,bytes]]: Received data
        """
        async for msg in self._connection:
            yield msg

    async def send(self, message: str | bytes):
        with suppress(ConnectionClosedError):
            await self._connection.send(message)

    def __str__(self) -> str:
        return str(self._uuid)

    def __format__(self, format_spec: str) -> str:
        if format_spec == "short":
            return str(self._uuid)[:8]
        return str(self)
