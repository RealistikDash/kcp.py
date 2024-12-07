# kcp.py
Python bindings and networking for the KCP protocol.

## What is KCP?
KCP is a protocol focusing on low latency data delivery with a guarantee of data delivery. It serves as an alternative to the TCP protocol.

## How to install?
kcp.py is available on [PyPi](https://pypi.org/project/kcp/), meaning installing is as simple as running
```sh
pip install kcp
```

## Examples
### Just the raw connection
While kcp.py features a diverse set of pre-implemented uses of KCP (see below), it also allows you to directly manage your KCP connections.
Here is an example using two independent connections locally.
```py
from kcp import KCP

# Create two connections using the same conversation ID.
kcp1 = KCP(
    conv_id=1,
)

kcp2 = KCP(
    conv_id=1,
)

# Update their timing information.
kcp1.update()
kcp2.update()


# Set each connection to send data to the other one (usually this would go through some network layer, but
# for the purpose of the example we do this).
@kcp1.outbound_handler
def send_kcp1(_, data: bytes) -> None:
    kcp2.receive(data)


@kcp2.outbound_handler
def send_kcp2(_, data: bytes) -> None:
    kcp1.receive(data)

# Enqueue data to be sent and send it off.
kcp1.enqueue(b"Hello, world!")
kcp1.flush()

print(kcp2.get_received()) # b"Hello, world!"
```

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
