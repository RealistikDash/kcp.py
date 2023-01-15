from typing import Optional

class KCPControl:
    token: str  # The token used to identify the connection.
    """An object that represents a KCP connection to a remote peer."""
    def __init__(self, token: str) -> None: ...
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
