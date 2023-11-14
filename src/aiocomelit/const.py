"""Constants for Comelit Simple Home."""
import logging
from enum import Enum

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
class AlarmAreaState(Enum):
    ANOMALY = "anomaly"
    ARMED = "armed"
    DISARMED = "disarmed"
    ENTRY_DELAY = "entry_delay"
    EXIT_DELAY = "exit_delay"
    SABOTAGE = "sabotage"
    TRIGGERED = "triggered"
    UNKNOWN = "unknown"


class AlarmZoneState(Enum):
    ALARM = "alarm"
    OPEN = "open"
    EXCLUDED = "excluded"
    INHIBITED = "inhibited"
    ISOLATED = "isolated"
    REST = "rest"
    SABOTATED = "sabotated"
    UNKNOWN = "unknown"


ALARM_DISABLE = "dis"
ALARM_ENABLE = "tot"
ALARM_AREAS = "alarm_areas"
ALARM_AREA_STATUS: dict[str, AlarmAreaState] = {
    "out_time": AlarmAreaState.EXIT_DELAY,
    "in_time": AlarmAreaState.ENTRY_DELAY,
    "anomaly": AlarmAreaState.ANOMALY,
    "sabotage": AlarmAreaState.SABOTAGE,
    "alarm": AlarmAreaState.TRIGGERED,
    "armed": AlarmAreaState.ARMED,
    "ready": AlarmAreaState.DISARMED,
}
ALARM_ZONES = "alarm_zones"
ALARM_ZONE_STATUS: dict[int, AlarmZoneState] = {
    0: AlarmZoneState.REST,
    1: AlarmZoneState.OPEN,
    2: AlarmZoneState.ALARM,
    12: AlarmZoneState.SABOTATED,
    128: AlarmZoneState.EXCLUDED,
    256: AlarmZoneState.ISOLATED,
    32768: AlarmZoneState.INHIBITED,
}

# Min wait time after login
SLEEP = 0.5

# DEFAULT POWER UNIT
WATT = "W"
