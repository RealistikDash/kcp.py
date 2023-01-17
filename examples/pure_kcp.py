from __future__ import annotations

from kcp import KCP

kcp1 = KCP(
    conv_id=1,
)

kcp2 = KCP(
    conv_id=1,
)

kcp1.update()
kcp2.update()


@kcp1.outbound_handler
def send_kcp1(_, data: bytes) -> None:
    kcp2.receive(data)


@kcp2.outbound_handler
def send_kcp2(_, data: bytes) -> None:
    kcp1.receive(data)


kcp1.enqueue(b"Hello, world!")
kcp1.flush()

print(kcp2.get_received())
