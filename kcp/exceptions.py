from __future__ import annotations


class KCPException(Exception):
    """A generic exception for a KCP connection."""

    pass


class KCPConvMismatchError(KCPException):
    """Raised when the conversation ID of a packet does not match the
    conversation ID of the connection."""

    pass
