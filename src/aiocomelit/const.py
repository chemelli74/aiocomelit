"""Constants for Comelit Simple Home."""
import logging

_LOGGER = logging.getLogger(__package__)

# Host types
BRIDGE = "Serial bridge"
VEDO = "Vedo system"

# Device types
CLIMATE = "clima"
COVER = "shutter"
IRRIGATION = "irrigation"
LIGHT = "light"
OTHER = "other"
SCENARIO = "scenario"

# Statuses
ERROR_STATUS = -1
COVER_STATUS: list[str] = ["stopped", "opening", "closing"]

# Actions
COVER_CLOSE = 0
COVER_OPEN = 1
LIGHT_OFF = 0
LIGHT_ON = 1

# Maximum number of zones for a VEDO alarm device
MAX_ZONES = 8

# Min time between updates
SLEEP = 0.5

# DEFAULT POWER UNIT
WATT = "W"
