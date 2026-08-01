# Copyright 2023 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""aiocomelit library."""

__version__ = "2.0.7"

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
    DeviceStorageFailureError,
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
    "DeviceStorageFailureError",
]
