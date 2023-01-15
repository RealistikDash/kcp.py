from __future__ import annotations

import asyncio
import time
from asyncio import transports
from dataclasses import dataclass
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Optional

from .exceptions import *
from .extension import KCP

# We use asyncio's datagram protocol as it is the fastest way to
# implement a UDP server. We are probably not using it the intended
# way, but it works.
class KCPServerProtocol(asyncio.DatagramProtocol):
    """Implements a KCP server protocol for asyncio."""

    transport: transports.DatagramTransport
    server: KCPServerAsync

    def __init__(self, server: KCPServerAsync) -> None:
        self.server = server
        super().__init__()

    def datagram_received(self, data: bytes, addr: AddressType) -> None:
        self.server._handle_data(data, addr)


@dataclass(slots=True)
class Connection:
    _kcp: KCP
    _server: KCPServerAsync
    address: str
    port: int

    def __post_init__(self) -> None:
        self._kcp.include_outbound_handler(self._send_kcp)

    @property
    def address_tuple(self) -> AddressType:
        return self.address, self.port

    def receive(self, data: bytes) -> Optional[bytes]:
        """Handles receiving data from the client."""
        self._kcp.receive(data)

        while data := self._kcp.get_received():
            server = self._server
            server._loop.create_task(server._data_handler(self, data))  # type: ignore

    def send(self, data: bytes) -> None:
        self._kcp.enqueue(data)

    # Functions for the kcp extension
    def _send_kcp(self, _, data: bytes) -> None:
        self._server._transport.sendto(  # type: ignore
            data,
            self.address_tuple,
        )

    def update(self, ts_ms: Optional[int] = None) -> None:
        self._kcp.update(ts_ms)


AddressType = tuple[str | Any, int]
DataHandler = Callable[[Connection, bytes], Awaitable[None]]
EventHandler = Callable[[], Awaitable[None]]


# TODO: Just merge this with `KCPServerProtocol`.
class KCPServerAsync:
    def __init__(self, address: str, port: int, conv: int, delay: int = 100) -> None:
        self.address = address
        self.port = port
        self._transport: Optional[transports.DatagramTransport] = None
        self._loop = asyncio.get_event_loop()
        self._conv = conv
        self._delay = delay

        self._connections: dict[AddressType, Connection] = {}

        # Event handlers
        self._data_handler: Optional[DataHandler] = None
        self._on_start: Optional[EventHandler] = None
        self._on_stop: Optional[EventHandler] = None

    # Private API
    # Called by the protocol.
    def _handle_data(self, data: bytes, address: AddressType) -> None:
        connection = self._ensure_connection(address)
        res = connection.receive(data)

    def _ensure_connection(self, address: AddressType) -> Connection:
        connection = self._connections.get(address)
        if connection is None:
            connection = Connection(
                _kcp=KCP(self._conv),
                _server=self,
                address=address[0],
                port=address[1],
            )
            self._connections[address] = connection

        return connection

    # Public API
    async def listen(self) -> None:
        transport, protocol = await self._loop.create_datagram_endpoint(
            lambda: KCPServerProtocol(self),
            local_addr=(self.address, self.port),
        )
        self._transport = transport

        # Call the start event handler.
        if self._on_start is not None:
            self._loop.create_task(self._on_start())  # type: ignore

        # Update connection timing information.
        while True:
            await asyncio.sleep(self._delay / 1000)
            for connection in self._connections.values():
                connection.update()

    def start(self) -> None:
        self._loop.run_until_complete(self.listen())

    # Decorators
    def on_data(self, handler: DataHandler) -> DataHandler:
        self._data_handler = handler
        return handler

    def on_start(self, handler: EventHandler) -> EventHandler:
        self._on_start = handler
        return handler

    def on_stop(self, handler: EventHandler) -> EventHandler:
        self._on_stop = handler
        return handler
