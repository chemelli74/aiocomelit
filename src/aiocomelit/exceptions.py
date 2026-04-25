"""Comelit SimpleHome library exceptions."""

from __future__ import annotations


class ComelitError(Exception):
    """Base class for aiocomelit errors."""


class CannotConnect(ComelitError):
    """Exception raised when connection fails."""


class CannotAuthenticate(ComelitError):
    """Exception raised when credentials are incorrect."""


class CannotRetrieveData(ComelitError):
    """Exception raised when data retrieval fails."""


class DeviceStorageFailureError(ComelitError):
    """Exception raised when device SD storage is failing or becoming unreliable."""
