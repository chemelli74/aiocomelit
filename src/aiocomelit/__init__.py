"""aiocomelit library."""

__version__ = "1.1.0"

from .api import (
    ComeliteSerialBridgeApi,
    ComelitSerialBridgeObject,
    ComelitVedoApi,
    ComelitVedoAreaObject,
    ComelitVedoZoneObject,
)
from .exceptions import (
    CannotAuthenticate,
    CannotConnect,
    CannotRetrieveData,
    ComelitError,
)

__all__ = [
    "CannotAuthenticate",
    "CannotConnect",
    "CannotRetrieveData",
    "ComelitError",
    "ComelitSerialBridgeObject",
    "ComelitVedoApi",
    "ComelitVedoAreaObject",
    "ComelitVedoZoneObject",
    "ComeliteSerialBridgeApi",
]
