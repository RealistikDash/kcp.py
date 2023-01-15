from __future__ import annotations

from kcp.extension import OldKCPControl


def test_reversability():
    SEND_DATA = b"Your father is dead."
    con = OldKCPControl("")
    con.update()
    con.send(SEND_DATA)
    outbound = con.read_outbound()

    con.receive(outbound)
    inbound = con.read_inbound()

    assert bytes(inbound) == SEND_DATA
