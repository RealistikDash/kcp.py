from typing import Optional
from typing import Callable
from typing import Any

class OldKCPControl:
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
    def no_delay(self, nodelay: bool, interval: int, resend: int, nc: int) -> None:
        """Sets the connection's no-delay parameters.

        :param nodelay: Toggle nodelay.
        :param interval: The internal update interval in milliseconds.
        :param resend: The number of times to resend a packet if it is not acknowledged.
        :param nc: Whether to disable congestion control.
        """
        ...

class KCP:
    identity_token: Any
    # Dunders
    def __init__(
        self,
        conv: int,
        max_transmission: int = 1400,
        no_delay: bool = True,
        update_interval: int = 100,
        resend_count: int = 2,
        no_congestion_control: bool = False,
        identity_token: Any = None,
    ) -> None:
        """Creates an instance of the KCP protocol.

        :param conv: The conversation ID. Must be equal on both ends of the
        connection.
        :param max_transmission: The maximum transmission unit (MTU) of outbound
        packets.
        :param no_delay: Whether to enable no-delay mode.
        :param update_interval: The internal update interval in milliseconds.
        :param resend_count: The number of times to resend a packet if it is
        not acknowledged.
        :param no_congestion_control: Whether to disable congestion control.
        :param identity_token: Any data that can be used to identify the
        connection. This is not used by KCP itself.
        """
        ...
    # Handler configuration
    def include_outbound_handler(self, handler: OutboundDataHandler) -> None:
        """Adds a handler to be called when outbound data is ready to be
        sent."""
        ...
    def outbound_handler(self, handler: OutboundDataHandler) -> None:
        """Decorator equivalent of `include_outbound_handler`."""
        ...
    # I/O
    def enqueue(self, data: bytes) -> None:
        """Enqueues raw data to be sent."""
        ...
    def receive(self, data: bytes) -> None:
        """Handles receiving KCP data and adds it to the internal buffer."""
        ...
    def get_received(self) -> bytes:
        """Returns the next received packet of data."""
        ...
    def update(self, ts_ms: Optional[int] = None) -> None:
        """Updates the connection timing information, potentially calling
        the outbound handler. This should be regularly called (~10-100ms).

        :param ts_ms: The current time in milliseconds. If not provided,
        it will be computed by the Python interpreter.
        """
        ...
    def update_check(self, ts_ms: Optional[int] = None) -> bool:
        """Checks when the next update should be called.

        :param ts_ms: The current time in milliseconds. If not provided,
        it will be computed by the Python interpreter.
        """
        ...
    def flush(self) -> None:
        """Flushes the internal buffer to the outbound handler."""
        ...
    # Configuration
    def set_maximum_transmission(self, max_transmission: int) -> None:
        """Sets the MTU (maximum transmission unit)."""
        ...
    def set_performance_options(
        self,
        no_delay: bool,
        update_interval: int,
        resend_count: int,
        no_congestion_control: bool,
    ) -> None:
        """Sets the performance options for the connection.

        :param no_delay: Whether to enable no-delay mode.
        :param update_interval: The internal update interval in milliseconds.
        :param resend_count: The number of times to resend a packet if it is
        not acknowledged.
        :param no_congestion_control: Whether to disable congestion control.
        """
        ...
    # Statistics
    def get_outbound_packets(self) -> int:
        """Returns the number of packets queued to be sent."""
        ...
    def get_next_packet_size(self) -> int:
        """Returns the size of the next packet received."""
        ...
    # Other
    def update_loop(self) -> None:
        """A blocking loop that continuously updates the connection
        according to `update_check()`."""
        ...

OutboundDataHandler = Callable[[KCP, bytes], None]
