from typing import Optional
from typing import Callable
from typing import Any

class KCP:
    identity_token: Any
    # Dunders
    def __init__(
        self,
        conv_id: int,
        max_transmission: int = 1400,
        no_delay: bool = True,
        update_interval: int = 100,
        resend_count: int = 2,
        no_congestion_control: bool = False,
        identity_token: Any = None,
    ) -> None:
        """Creates an instance of the KCP protocol.

        :param conv_id: The conversation ID. Must be equal on both ends of the
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
    def get_received(self) -> bytearray:
        """Returns the next received packet of data."""
        ...
    def get_all_received(self) -> list[bytearray]:
        """Returns all individual received packets of data as a list."""
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
    # Properties
    @property
    def next_packet_available(self) -> bool:
        """Returns whether there is a packet available to be received."""
        ...

OutboundDataHandler = Callable[[KCP, bytes], None]
