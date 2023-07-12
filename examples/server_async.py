from __future__ import annotations

from kcp.server import Connection
from kcp.server import KCPServerAsync

# Create the initial server instance.
server = KCPServerAsync(
    "127.0.0.1",
    9999,
    conv_id=1,
    no_delay=True,
)

# Ability to set performance options after initialisation.
server.set_performance_options(
    update_interval=10,
)


# Ran when the server starts.
@server.on_start
async def on_start() -> None:
    print("Server started!")


# Ran when a connection is made.
@server.on_data
async def on_data(connection: Connection, data: bytes) -> None:
    print(f"Received data from {connection.address}: {data}")


server.start()
