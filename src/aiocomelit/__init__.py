__version__ = "0.4.0"

from .api import (
    ComeliteSerialBridgeApi,
    ComelitSerialBridgeObject,
    ComelitVedoApi,
    ComelitVedoObject,
)
from .exceptions import (
    CannotAuthenticate,
    CannotConnect,
    CannotRetrieveData,
    ComelitError,
)

__all__ = [
    "ComeliteSerialBridgeApi",
    "ComelitSerialBridgeObject",
    "ComelitVedoApi",
    "ComelitVedoObject",
    "ComelitError",
    "CannotConnect",
    "CannotAuthenticate",
    "CannotRetrieveData",
]
