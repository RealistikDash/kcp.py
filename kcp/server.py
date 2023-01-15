from .extension import KCPControl
from .exceptions import *

from dataclasses import dataclass
from typing import Callable
from typing import Awaitable
from typing import Optional
import asyncio
import socket
import logging
import uuid


@dataclass
class ConnectionContext:
    """A connection context for a KCP connection."""

    _kcp: KCPControl
    _socket: socket.socket
    _handle_task: asyncio.Task
    _logger: logging.Logger
    address: str
    port: int
    token: str

    def enqueue(self, data: bytes) -> None:
        """Enqueue data to be sent to the client on the next connection update."""
        self._kcp.send(data)

    async def _send(self, data: bytes) -> None:
        """Sends raw data to the connected client."""
        loop = asyncio.get_event_loop()
        await loop.sock_sendall(self._socket, data)

        self._logger.debug(f"Sent data to client {self.token}@{self.address}:{self.port}")

    async def update(self, timestamp_ms: Optional[int] = None) -> None:
        """Update the KCP connection. This will handle sending any queued data alongside 
        updating the timing of the connection. This should be called every 100ms or so."""

        queued = self._kcp.update(timestamp_ms)
        if queued:
            await self._send(queued)

ConnectionHandler = Callable[[ConnectionContext], Awaitable[None]]

class AsyncKCPServer:
    """An asynchronous KCP server running on top of a UDP socket."""

    __slots__ = (
        "_socket",
        "port",
        "address",
        "loop",
        "_handler",
        "_connections",
        "_closing",
        "_update_loop_task",
        "_logger",
    )

    def __init__(self, address: str, port: int) -> None:
        """Configures the KCP server."""
        self.port = port
        self.address = address
        self._socket: Optional[socket.socket] = None
        self._handler: Optional[ConnectionHandler] = None
        self._connections: list[ConnectionContext] = []
        self._closing = False
        self._update_loop_task: Optional[asyncio.Task] = None
        self._logger = logging.getLogger("kcp.async_server")

    def _configure_socket(self) -> socket.socket:
        # Configure a UDP socket.
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(False)

        return self._socket

    async def _update_connection_loop(self) -> None:
        while True:
            for connection in self._connections:
                await connection.update()

            await asyncio.sleep(0.1)

    async def _handle_connection(self, socket: socket.socket) -> None:
        cur_task = asyncio.current_task()
        if cur_task is None:
            raise RuntimeError("`_handle_connection` was called outside of a task.")
        # Create context
        identifier = str(uuid.uuid4())
        kcp = KCPControl(identifier)
        sock_addr, sock_port = socket.getpeername()

        context = ConnectionContext(
            _kcp=kcp,
            _socket=socket,
            _handle_task=cur_task,
            address=sock_addr,
            port=sock_port,
            token=identifier,
            _logger=self._logger,
        )

        self._connections.append(context)

        self._logger.info(f"Received connection from {sock_addr}:{sock_port}")
        
        # Keep listening for data until the connection is closed.
        while True:
            data = await asyncio.get_event_loop().sock_recv(socket, 1024)
            if not data:
                break

            context._kcp.receive(data)
            kcp_data = context._kcp.read_inbound()
            if kcp_data:
                await self._handler(context) # type: ignore

    async def _create_update_loop(self) -> None:
        self._update_loop_task = asyncio.create_task(self._update_connection_loop())

    # Decorator to set the connection handler.
    async def on_data(self) -> Callable[[ConnectionHandler], ConnectionHandler]:
        """Decorator setting the handler for whenever data is received from a client."""
        def decorator(handler: ConnectionHandler) -> ConnectionHandler:
            self._handler = handler
            return handler

        return decorator

    async def close(self) -> None:
        """Closes the server and all connections."""
        self._closing = True
        if self._update_loop_task is not None:
            self._update_loop_task.cancel()

        for connection in self._connections:
            connection._handle_task.cancel()
            connection._socket.close()

    async def listen(self) -> None:
        """Binds the server to the address and port and starts listening for connections."""

        loop = asyncio.get_event_loop()

        if self._handler is None:
            raise KCPError(
                "No connection handler was provided. Try using the @server.on_data decorator."
            )

        sock = self._configure_socket()

        # Bind the socket to the address and port.
        sock.bind((self.address, self.port))
        await self._create_update_loop()

        self._logger.info(f"KCP Server is listening on {self.address}:{self.port}")

        while not self._closing:
            client, _ = await loop.sock_accept(sock)
            loop.create_task(self._handle_connection(client))

    def start(self) -> None:
        """Handles the creation of the loop, and starts the server."""
        loop = asyncio.get_event_loop()

        # Create the update loop task.
        loop.run_until_complete(self._update_connection_loop())
