# Copyright 2023 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""aiocomelit library."""

__version__ = "3.0.0"

from .api import ComelitDeviceObject, ComelitVedoAreaObject, ComelitVedoZoneObject
from .devices.bridge import ComeliteSerialBridgeApi
from .devices.hub import ComelitHubApi
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
    "ComelitHubApi",
    "ComelitVedoApi",
    "ComelitVedoAreaObject",
    "ComelitVedoZoneObject",
    "ComeliteSerialBridgeApi",
    "DeviceStorageFailureError",
]
