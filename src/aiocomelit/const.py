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
STATE_OFF = 0
STATE_ON = 1

# Alarm specific
ALARM_DISABLE = "dis"
ALARM_ENABLE = "tot"
ALARM_AREAS = "alarm_areas"
ALARM_AREA_STATUS: dict[str, str] = {
    "out_time": "arming",
    "in_time": "disarming",
    "anomaly": "anomaly",
    "sabotage": "sabotage",
    "alarm": "alarm",
    "armed": "armed",
    "ready": "ready",
}
ALARM_ZONES = "alarm_zones"
ALARM_ZONE_STATUS: dict[int, str] = {
    1: "open",
    2: "alarm",
    12: "sabotated",
    128: "excluded",
    256: "isolated",
    32768: "inhibited",
}

# Min wait time after login
SLEEP = 0.5

# DEFAULT POWER UNIT
WATT = "W"
