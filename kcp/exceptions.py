from __future__ import annotations


class KCPException(Exception):
    pass


class KCPInputError(KCPException):
    pass


class KCPEmptyBufferError(KCPException):
    pass


class KCPError(KCPException):
    pass


class KCPAsyncServerError(KCPException):
    pass


class KCPConvMismatchError(KCPException):
    pass
