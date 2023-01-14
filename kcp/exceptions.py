class KCPInputError(Exception):
    pass

class KCPEmptyBufferError(KCPInputError):
    pass

class KCPError(Exception):
    pass
