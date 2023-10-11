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
STATE_COVER: list[str] = ["stopped", "opening", "closing"]
STATE_ERROR = -1
STATE_OFF = 0
STATE_ON = 1

# Alarm specific
ALARM_DISABLE = "dis"
ALARM_ENABLE = "tot"
ALARM_FIELDS: dict[str, str] = {
    "out_time": "arming",
    "in_time": "disarming",
    "anomaly": "anomaly",
    "sabotage": "sabotage",
    "alarm": "alarm",
    "armed": "armed",
    "ready": "ready",
}
ALARM_MAX_ZONES = 8

# Min time between updates
SLEEP = 0.5

# DEFAULT POWER UNIT
WATT = "W"
