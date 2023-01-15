from __future__ import annotations

from kcp.extension import KCPControl


def test_reversability():
    SEND_DATA = b"Your father is dead."
    con = KCPControl()
    con.update()
    con.send(SEND_DATA)
    outbound = con.read_outbound()

    con.receive(outbound)
    inbound = con.read_inbound()

    assert bytes(inbound) == SEND_DATA
