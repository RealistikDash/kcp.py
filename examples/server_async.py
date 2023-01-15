from __future__ import annotations

from kcp.server import Connection
from kcp.server import KCPServerAsync

server = KCPServerAsync(
    "127.0.0.1",
    9999,
)


@server.on_start
async def on_start() -> None:
    print("Server started!")


@server.on_data
async def on_data(connection: Connection, data: bytes) -> None:
    print(f"Received data from {connection.address}: {data}")


server.start()
