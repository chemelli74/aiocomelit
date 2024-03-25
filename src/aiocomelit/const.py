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
    """Alarm area states."""

    ANOMALY = "anomaly"
    ARMED = "armed"
    DISARMED = "disarmed"
    ENTRY_DELAY = "entry_delay"
    EXIT_DELAY = "exit_delay"
    SABOTAGE = "sabotage"
    TRIGGERED = "triggered"
    UNKNOWN = "unknown"


class AlarmZoneState(Enum):
    """Alarm zone states."""

    ALARM = "alarm"
    ARMED = "armed"
    OPEN = "open"
    EXCLUDED = "excluded"
    FAULTY = "faulty"
    INHIBITED = "inhibited"
    ISOLATED = "isolated"
    REST = "rest"
    SABOTATED = "sabotated"
    UNAVAILABLE = "unavailable"
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
    # Alarm state needs to be checked first
    # because is reported as OPEN + ALARM + ARMED [51]
    2: AlarmZoneState.ALARM,
    0: AlarmZoneState.REST,
    1: AlarmZoneState.OPEN,
    4: AlarmZoneState.FAULTY,
    8: AlarmZoneState.SABOTATED,
    32: AlarmZoneState.ARMED,
    128: AlarmZoneState.EXCLUDED,
    256: AlarmZoneState.ISOLATED,
    512: AlarmZoneState.UNAVAILABLE,
    32768: AlarmZoneState.INHIBITED,
}

# Min wait time between http calls
SLEEP_BETWEEN_BRIDGE_CALLS = 1.5
SLEEP_BETWEEN_VEDO_CALLS = 0.25

# DEFAULT POWER UNIT
WATT = "W"
