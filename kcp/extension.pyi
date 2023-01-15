from typing import Optional

class KCPControl:
    token: str  # The token used to identify the connection.
    """An object that represents a KCP connection to a remote peer."""
    def __init__(self, token: str, conv: int) -> None: ...
    def send(self, data: bytes) -> None:
        """Enqueues data to be sent to the remote peer."""
        ...
    def receive(self, data: bytes) -> None:
        """Enqueues data to be received from the remote peer."""
        ...
    def update(self, ts_ms: Optional[int] = None) -> Optional[bytes]:
        """Updates the connection timing information. May return a packet to be sent to the remote peer.

        If `ts_ms` is not provided, it will be set to the current time in milliseconds computed by the Python interpreter.
        """
        ...
    def get_queued_packets(self) -> int:
        """Returns the number of packets queued to be sent to the remote peer."""
        ...
    def read_outbound(self) -> bytes:
        """Outputs the KCP packet data to be sent to the remote peer."""
        ...
    def read_inbound(self) -> bytes:
        """Outputs the data received from the remote peer."""
        ...
    def set_mtu(self, mtu: int) -> None:
        """Sets the MTU (maximum transmission unit) of the connection."""
        ...
    def no_delay(self, nodelay: int, interval: int, resend: int, nc: int) -> None:
        """Sets the connection's no-delay parameters.

        :param nodelay: 0 to disable, 1 to enable.
        :param interval: The internal update interval in milliseconds.
        :param resend: The number of times to resend a packet if it is not acknowledged.
        :param nc: Whether to disable congestion control.
        """
        ...
