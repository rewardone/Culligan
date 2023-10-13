"""Python API for Culligan devices"""

from .uniapi_culliganiot import new_culligan_api, CulliganApi
from .exc import (
    CulliganError,
    CulliganAuthExpiringError,
    CulliganNotAuthedError,
    CulliganAuthError,
    CulliganReadOnlyPropertyError,
)

__version__ = '1.0.9'