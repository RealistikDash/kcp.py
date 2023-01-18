from __future__ import annotations

import time

from kcp import KCPClientSync

client = KCPClientSync(
    "127.0.0.1",
    9999,
    conv=1,
)


@client.on_data
def handle_data(data: bytes) -> None:
    print(data)


@client.on_start
def on_start() -> None:
    print("Connected to server!")

    while True:
        client.send(b"POLSKA GUROM!!")
        time.sleep(0.1)


client.start()
