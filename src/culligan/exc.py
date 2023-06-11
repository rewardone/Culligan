"""Exceptions"""

# Default messages
AUTH_EXPIRED_MESSAGE = 'Ayla Networks API authentication expired.  Re-authenticate and retry.'
AUTH_FAILURE_MESSAGE = 'Error authenticating to Ayla Networks.'
NOT_AUTHED_MESSAGE = 'Ayla Networks API not authenticated.  Authenticate first and retry.'


class CulliganError(RuntimeError):
    """Parent class for all Culligan exceptions"""


class CulliganAuthError(CulliganError):
    """Exception authenticating"""
    def __init__(self, msg=AUTH_FAILURE_MESSAGE, *args):
        super().__init__(msg, *args)


class CulliganAuthExpiringError(CulliganError):
    """Authentication expired and needs to be refreshed"""
    def __init__(self, msg=AUTH_EXPIRED_MESSAGE, *args):
        super().__init__(msg, *args)


class CulliganNotAuthedError(CulliganError):
    """Shark not authorized"""
    def __init__(self, msg=NOT_AUTHED_MESSAGE, *args):
        super().__init__(msg, *args)


class CulliganReadOnlyPropertyError(CulliganError):
    """Tried to set a read-only property"""
    pass