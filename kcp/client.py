from __future__ import annotations

import socket
import threading
import time
from typing import Callable
from typing import Optional

from .extension import KCPControl
from .utils import create_unique_token

SyncDataHandler = Callable[[bytes], None]


class KCPClient:
    def __init__(self, address: str, port: int) -> None:
        """Configures a KCP client."""

        self.address = address
        self.port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._handler: Optional[SyncDataHandler] = None
        self._kcp = KCPControl(create_unique_token())

    # Private API

    def _configure_socket(self) -> socket.socket:
        self._socket.setblocking(False)

        return self._socket

    def _handle_data(self, data: bytes) -> None:
        if self._handler is None:
            raise RuntimeError("No data handler was set.")

        self._handler(data)

    def _send_raw_data(self, data: bytes) -> None:
        self._socket.sendto(
            data,
            (self.address, self.port),
        )

    def _update(self) -> None:
        data = self._kcp.update()
        if data is not None:
            self._send_raw_data(data)

    def _receive(self, data: bytes) -> None:
        self._kcp.receive(data)

        # Handle data
        buffer_data = self._kcp.read_inbound()
        if buffer_data:
            self._handle_data(buffer_data)

    # Public API
    def send(self, data: bytes) -> None:
        """Enqueues data to be sent to the server on the next update cycle."""
        self._kcp.send(data)

    def receive(self, data: bytes) -> None:
        """Receives KCP data from the server."""
        self._receive(data)

    def update_loop(self, delay: float = 0.1) -> None:
        """Creates a loop that updates the KCP connection."""

        while True:
            self._update()
            time.sleep(delay)

    def receive_loop(self) -> None:
        """Creates a loop that receives data from the server."""

        while True:
            data, _ = self._socket.recvfrom(2048)
            self._receive(data)

    def start(self) -> None:
        """Starts the KCP Client using threads."""

        self._configure_socket()

        threads = [
            threading.Thread(target=self.update_loop),
            threading.Thread(target=self.receive_loop),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    # Decorators
    def data_handler(self, handler: SyncDataHandler) -> SyncDataHandler:
        """Registers a data handler to be called when data is received."""

        self._handler = handler
        return handler
