from __future__ import annotations

from kcp import KCP


def test_delivery():
    kcp1 = KCP(
        conv_id=1,
        no_delay=True,
    )
    kcp2 = KCP(
        conv_id=1,
        no_delay=True,
    )
    kcp2.update()
    kcp1.update()

    @kcp1.outbound_handler
    def send_kcp(_, data: bytes) -> None:
        kcp2.receive(data)

    kcp1.enqueue(b"Hello World!")
    kcp1.flush()

    assert kcp2.get_received() == b"Hello World!"
