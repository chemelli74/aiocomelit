# Copyright 2023 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""aiocomelit library."""

__version__ = "2.0.8"

from .api import ComelitDeviceObject, ComelitVedoAreaObject, ComelitVedoZoneObject
from .devices.bridge import ComeliteSerialBridgeApi
from .devices.vedo import ComelitVedoApi
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
    "ComelitDeviceObject",
    "ComelitError",
    "ComelitVedoApi",
    "ComelitVedoAreaObject",
    "ComelitVedoZoneObject",
    "ComeliteSerialBridgeApi",
    "DeviceStorageFailureError",
]
