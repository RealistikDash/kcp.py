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


@dataclass
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

    def __update_activity(self) -> None:
        self.last_active = time.perf_counter()

    async def receive(self, data: bytes) -> None:
        """Handles receiving data from the client."""
        self._kcp.receive(data)

        self.__update_activity()
        assert self._server._data_handler is not None  # SHUT UP MYPY

        for data in self._kcp.get_all_received():
            data = self._perform_mutations(data)
            await self._server._data_handler(self, data)

    def enqueue(self, data: bytes) -> None:
        """Enqueues data to be sent to the client."""
        self._kcp.enqueue(data)
        self.__update_activity()

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
        max_transmission: int = 1400,
        no_delay: bool = False,
        resend_count: int = 2,
        no_congestion_control: bool = False,
        receive_window_size: int = 128,
        send_window_size: int = 32,
    ) -> None:
        """Configures the asynchronous KCP server.

        :param address: The address to listen on (usually `127.0.0.1`).
        :param port: The port to listen on.
        :param conv: The conversation number to use for the KCP protocol.
        :param delay: The delay between KCP updates in milliseconds.
        :param connection_timeout: The amount of time in seconds to wait before
            cleaning up after a connection.
        :param max_transmission: The maximum transmission unit (MTU) of outbound
            packets.
        :param no_delay: Whether to enable no-delay mode.
        :param resend_count: The number of times to resend a packet if it is
            not acknowledged.
        :param no_congestion_control: Whether to disable congestion control.
        :param receive_window_size: The size of the receive window in packets.
        :param send_window_size: The size of the send window in packets.
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

        # Connection settings.
        self._max_transmission = max_transmission
        self._no_delay = no_delay
        self._resend_count = resend_count
        self._no_congestion_control = no_congestion_control
        self._send_window_size = send_window_size
        self._receive_window_size = receive_window_size

    # Private API
    # Called by the protocol.
    def datagram_received(self, data: bytes, address: AddressType) -> None:
        connection = self._ensure_connection(address)
        self._loop.create_task(connection.receive(data))

    def _ensure_connection(self, address: AddressType) -> Connection:
        connection = self._connections.get(address)
        if connection is None:
            kcp = KCP(
                self._conv,
                max_transmission=self._max_transmission,
                no_delay=self._no_delay,
                update_interval=self._delay,
                resend_count=self._resend_count,
                no_congestion_control=self._no_congestion_control,
                send_window_size=self._send_window_size,
                receive_window_size=self._receive_window_size,
            )
            connection = Connection(
                _kcp=kcp,
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

    def set_performance_options(
        self,
        no_delay: Optional[bool] = None,
        update_interval: Optional[int] = None,
        resend_count: Optional[int] = None,
        no_congestion_control: Optional[bool] = None,
        receive_window_size: Optional[int] = None,
        send_window_size: Optional[int] = None,
    ) -> None:
        """Configures the performance options for all **future** KCP connections.

        :param no_delay: Whether to enable no-delay mode.
        :param update_interval: The internal update interval in milliseconds.
        :param resend_count: The number of times to resend a packet if it is
        not acknowledged.
        :param no_congestion_control: Whether to disable congestion control.
        """

        self._no_delay = no_delay if no_delay is not None else self._no_delay
        self._delay = update_interval if update_interval is not None else self._delay
        self._resend_count = resend_count if resend_count is not None else self._resend_count
        self._no_congestion_control = (
            no_congestion_control
            if no_congestion_control is not None
            else self._no_congestion_control
        )
        self._receive_window_size = (
            receive_window_size if receive_window_size is not None else self._receive_window_size
        )
        self._send_window_size = (
            send_window_size if send_window_size is not None else self._send_window_size
        )

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
