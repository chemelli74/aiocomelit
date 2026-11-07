# Copyright 2023 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""Constants for Comelit Simple Home."""

import logging
from enum import Enum, IntEnum, StrEnum

from aiohttp import ClientTimeout

_LOGGER = logging.getLogger(__package__)

DEFAULT_TIMEOUT = ClientTimeout(10)
DEFAULT_HUB_MQTT_PORT = 1883

# Host types
BRIDGE = "Serial bridge"
VEDO = "Vedo system"
HUB = "Hub"

# Device types
CLIMATE = "clima"
COVER = "shutter"
IRRIGATION = "irrigation"
LIGHT = "light"
OTHER = "other"
SCENARIO = "scenario"
ALARM_AREA = "alarm_areas"
ALARM_ZONE = "alarm_zones"

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
ALARM_AREA_STATUS: dict[str, AlarmAreaState] = {
    "out_time": AlarmAreaState.EXIT_DELAY,
    "in_time": AlarmAreaState.ENTRY_DELAY,
    "sabotage": AlarmAreaState.SABOTAGE,
    "alarm": AlarmAreaState.TRIGGERED,
    "armed": AlarmAreaState.ARMED,
    "ready": AlarmAreaState.DISARMED,
}
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
SLEEP_AFTER_VEDO_LOGIN = 1.5

# DEFAULT POWER UNIT
WATT = "W"


# Hub (MQTT) specific
class HubRequestType(IntEnum):
    """Comelit Hub MQTT request types."""

    STATUS = 0
    ACTION = 1
    LOGIN = 5
    PARAMETERS = 8
    ANNOUNCE = 13


class HubElementClass(StrEnum):
    """Comelit Hub element id prefixes, identifying a device's role."""

    LOGICAL = "GEN#PL"
    AUTOMATION = "DOM#AU"
    LIGHT = "DOM#LT"
    POWER = "DOM#CN"
    TEMPERATURE = "DOM#CL"
    COVER = "DOM#BL"
    SCENARIO = "GEN#SC"
    OTHER = "DOM#LD"


HUB_TOPIC_PREFIX = "HSrv"
HUB_STATUS_OBJ_ID = "GEN#17#13#1"
HUB_REQUEST_TIMEOUT = 10.0

# Default MQTT broker credentials shared by most Comelit Hub installs
DEFAULT_HUB_MQTT_USER = "hsrv-user"
DEFAULT_HUB_MQTT_PASSWORD = "sf1nE9bjPc"  # noqa: S105
