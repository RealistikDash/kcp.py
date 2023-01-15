from __future__ import annotations


class KCPInputError(Exception):
    pass


class KCPEmptyBufferError(KCPInputError):
    pass


class KCPError(Exception):
    pass


class KCPAsyncServerError(Exception):
    pass
