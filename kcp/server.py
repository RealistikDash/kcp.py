from __future__ import annotations

import asyncio
import time
from asyncio import transports
from dataclasses import dataclass
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Optional

from .extension import KCP


DataMutator = Callable[[bytes], bytes]


@dataclass(slots=True)
class Connection:
    _kcp: KCP
    _server: KCPServerAsync
    address: str
    port: int
    last_active: float
    _data_mutators: list[DataMutator]

    def __post_init__(self) -> None:
        self._kcp.include_outbound_handler(self._send_kcp)

    @property
    def address_tuple(self) -> AddressType:
        return self.address, self.port

    def _perform_mutations(self, data: bytes) -> bytes:
        for mutator in self._data_mutators:
            data = mutator(data)

        return data

    def receive(self, data: bytes) -> None:
        """Handles receiving data from the client."""
        self._kcp.receive(data)

        self.last_active = time.perf_counter()

        for data in self._kcp.get_all_received():
            data = self._perform_mutations(data)
            await self._server._data_handler(self, data)  # type: ignore

    def enqueue(self, data: bytes) -> None:
        """Enqueues data to be sent to the client."""
        self._kcp.enqueue(data)
        self.last_active = time.perf_counter()

    # Functions for the kcp extension
    def _send_kcp(self, _, data: bytes) -> None:
        self._server._transport.sendto(  # type: ignore
            data,
            self.address_tuple,
        )

    def update(self, ts_ms: Optional[int] = None) -> None:
        """Updates the timing information for the connection. May cause data
        to be sent to the client.

        :param ts_ms: The current time in milliseconds. If not provided, the
            the time will be calculated.
        """
        self._kcp.update(ts_ms)

    # Decorators
    def add_data_mutator(self, mutator: DataMutator) -> None:
        """Adds a local data mutator to the connection.

        :param mutator: The mutator to add.
        """

        self._data_mutators.append(mutator)


AddressType = tuple[Any, int]
DataHandler = Callable[[Connection, bytes], Awaitable[None]]
EventHandler = Callable[[], Awaitable[None]]


class KCPServerAsync(asyncio.DatagramProtocol):
    def __init__(
        self,
        address: str,
        port: int,
        conv_id: int,
        delay: int = 100,
        connection_timeout: int = 600,
    ) -> None:
        """Configures the asynchronous KCP server.

        :param address: The address to listen on (usually `127.0.0.1`).
        :param port: The port to listen on.
        :param conv: The conversation number to use for the KCP protocol.
        :param delay: The delay between KCP updates in milliseconds.
        :param connection_timeout: The amount of time in seconds to wait before
            cleaning up after a connection.
        """
        self.address = address
        self.port = port
        self._transport: Optional[transports.DatagramTransport] = None
        self._loop = asyncio.get_event_loop()
        self._conv = conv_id
        self._delay = delay

        self._connections: dict[AddressType, Connection] = {}
        self.connection_timeout = connection_timeout
        self._closed = False

        # Event handlers
        self._data_handler: Optional[DataHandler] = None
        self._on_start: Optional[EventHandler] = None
        self._on_stop: Optional[EventHandler] = None

        self._data_mutators: list[DataMutator] = []

    # Private API
    # Called by the protocol.
    def datagram_received(self, data: bytes, address: AddressType) -> None:
        connection = self._ensure_connection(address)
        connection.receive(data)

    def _ensure_connection(self, address: AddressType) -> Connection:
        connection = self._connections.get(address)
        if connection is None:
            connection = Connection(
                _kcp=KCP(self._conv),
                _server=self,
                address=address[0],
                port=address[1],
                last_active=time.perf_counter(),
                _data_mutators=self._data_mutators.copy(),
            )
            self._connections[address] = connection

        return connection

    # Public API
    async def listen(self) -> None:
        """Starts listening for connections alongside the KCP update loop."""
        transport, _ = await self._loop.create_datagram_endpoint(
            lambda: self,  # type: ignore
            local_addr=(self.address, self.port),
        )
        self._transport = transport

        # Call the start event handler.
        if self._on_start is not None:
            self._loop.create_task(self._on_start())  # type: ignore

        # Update connection timing information.
        while not self._closed:
            current_time = time.perf_counter()
            current_time_ms = int(current_time * 1000)
            await asyncio.sleep(self._delay / 1000)
            # Create a copy of the connections to avoid a modifying dictionary
            # while iterating over it.
            for connection in tuple(self._connections.values()):
                connection.update(current_time_ms)

                if current_time - connection.last_active > self.connection_timeout:
                    self._connections.pop(connection.address_tuple)

        # Handle cleanup.
        self._transport.close()
        self._transport = None
        self._connections.clear()

        if self._on_stop is not None:
            await self._on_stop()

    def start(self) -> None:
        """Creates the event loop and starts listening for connections."""
        self._loop.run_until_complete(self.listen())

    def stop(self) -> None:
        """Tells the server to stop listening for connections after the next
        update loop."""
        self._closed = True

    # Decorators
    def on_data(self, handler: DataHandler) -> DataHandler:
        """Decorator registering a handler which will be called when data is
        received from a client."""
        self._data_handler = handler
        return handler

    def on_start(self, handler: EventHandler) -> EventHandler:
        """Decorator registering a handler which will be called when the server
        starts listening for connections."""
        self._on_start = handler
        return handler

    def on_stop(self, handler: EventHandler) -> EventHandler:
        """Decorator registering a handler which will be called when the server
        stops listening for connections."""
        self._on_stop = handler
        return handler

    def add_data_mutator(self, mutator: DataMutator) -> DataMutator:
        """Decorator registering a global mutator which will be called on all data
        received from a client."""
        self._data_mutators.append(mutator)
        return mutator
