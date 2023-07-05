"""Constants for Comelit Simple Home."""
import logging

_LOGGER = logging.getLogger(__package__)

# Device types
COVER = "shutter"
LIGHT = "light"
CLIMATE = "clima"
OTHER = "other"

# Statuses
COVER_STATUS: list[str] = ["stopped", "opening", "closing"]

# Maximum number of zones for a VEDO alarm device
MAX_ZONES = 8
