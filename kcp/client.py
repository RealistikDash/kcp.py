from __future__ import annotations

import socket
import threading
import time
from typing import Callable
from typing import Optional

from .extension import KCP

SyncDataHandler = Callable[[bytes], None]


class KCPClientSync:
    def __init__(
        self,
        address: str,
        port: int,
        conv_id: int,
        no_delay: bool,
        update_interval: int,
        resend_count: int,
        no_congestion_control: bool,
        receive_window_size: int,
        send_window_size: int,
    ) -> None:
        """Configures a synchronous KCP client.

        :param address: The address of the target server.
        :param port: The port of the target server.
        :param conv_id: The conversation ID. Must be equal on both ends of the
            connection.
        :param no_delay: Whether to enable no-delay mode.
        :param update_interval: The internal update interval in milliseconds.
        :param resend_count: The number of times to resend a packet if it is
            not acknowledged.
        :param no_congestion_control: Whether to disable congestion control.
        :param receive_window_size: The size of the receive window in packets.
        :param send_window_size: The size of the send window in packets.
        """

        self.address = address
        self.port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self._kcp = KCP(
            conv_id,
            no_delay=no_delay,
            update_interval=update_interval,
            resend_count=resend_count,
            no_congestion_control=no_congestion_control,
            receive_window_size=receive_window_size,
            send_window_size=send_window_size,
        )
        self._kcp.include_outbound_handler(self._send_kcp)
        # Port 0 means the OS will pick a random port.
        self._local_port = 0

        self._data_sent = False

        # Event handlers
        self._handler: Optional[SyncDataHandler] = None
        self._on_start: Optional[Callable[[], None]] = None

    # Private API
    def _handle_data(self, data: bytes) -> None:
        if self._handler is None:
            raise RuntimeError("No data handler was set.")

        self._handler(data)

    def _send_raw_data(self, data: bytes) -> None:
        self._sock.sendto(
            data,
            (self.address, self.port),
        )
        self._data_sent = True

    def _send_kcp(self, _, data: bytes) -> None:
        self._send_raw_data(data)

    def _receive(self, data: bytes) -> None:
        self._kcp.receive(data)

        # Handle data
        for data in self._kcp.get_all_received():
            self._handle_data(data)

    def _wait_for_address(self) -> None:
        """Waits for the socket to be bound to an address."""

        while not self._data_sent:
            time.sleep(0.1)

    # Public API
    def send(self, data: bytes) -> None:
        """Enqueues data to be sent to the server on the next update cycle."""
        self._kcp.enqueue(data)

    def update_loop(self) -> None:
        """Creates a loop that updates the KCP connection."""

        while True:
            self._kcp.update()
            time.sleep(self._kcp.update_check() / 1000)

    def receive_loop(self) -> None:
        """Creates a loop that receives data from the server."""

        self._wait_for_address()

        while True:
            data, _ = self._sock.recvfrom(2048)
            self._receive(data)

    def start(self) -> None:
        """Starts the KCP Client using threads."""

        threads = [
            threading.Thread(target=self.receive_loop),
        ]

        if self._on_start is not None:
            threads.append(threading.Thread(target=self._on_start))

        for t in threads:
            t.daemon = True
            t.start()

        # Update loop is in Python, meaning signals are handled.
        self.update_loop()

    # Decorators
    def on_data(self, handler: SyncDataHandler) -> SyncDataHandler:
        """Registers a data handler to be called when data is received."""

        self._handler = handler
        return handler

    def on_start(self, handler: Callable[[], None]) -> Callable[[], None]:
        """Registers a handler to be called when the client starts."""

        self._on_start = handler
        return handler
