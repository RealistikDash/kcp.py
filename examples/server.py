# Example of the KCP Async Server
from __future__ import annotations

import logging

from kcp import AsyncKCPServer
from kcp.server import ConnectionContext

# Optional logging
logging.basicConfig(level=logging.DEBUG)

server = AsyncKCPServer(
    address="127.0.0.1",
    port=1234,
)


@server.on_data
async def on_data(ctx: ConnectionContext, data: bytes) -> None:
    print(f"Received data from {ctx}: {data}")


server.start()
