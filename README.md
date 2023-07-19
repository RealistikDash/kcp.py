# kcp.py
Python bindings and networking for the KCP protocol.

## What is KCP?
KCP is a protocol focusing on low latency data delivery with a guarantee of data delivery. It serves as an alternative to the TCP protocol.

## How to install?
kcp.py is available on [PyPi](https://pypi.org/project/kcp-py/), meaning installing is as simple as running
```sh
pip install kcp.py
```

## Examples
### Asynchronous Server
kcp.py features an implementation of an asynchronous server using the event loop protocol API.
```py
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
```

### Client
kcp.py also implements a KCP client using Python's sockets and threads.
```py
from kcp import KCPClientSync

client = KCPClientSync(
    "127.0.0.1",
    9999,
    conv_id=1,
)


@client.on_data
def handle_data(data: bytes) -> None:
    print(data)


@client.on_start
def on_start() -> None:
    print("Connected to server!")

    while True:
        client.send(b"Data!")


client.start()
```

You may find more examples in the `examples` directory within the repo.

## Features
- [x] Bindings to the C implementation of KCP
- [x] Pythonic API over said C bindings
- [ ] Asynchronous KCP Client
- [x] Synchronous KCP Client
- [x] Asynchronous KCP Server
- [x] Full support for installation through pip

## Credit
kcp.py uses [the official KCP implementation](https://github.com/skywind3000/kcp) behind the scenes.
