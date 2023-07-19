"""Support for Comelit SimpleHome."""
import asyncio
from dataclasses import dataclass
from datetime import datetime
from http.cookies import SimpleCookie
from typing import Any

import aiohttp

from .const import (
    _LOGGER,
    CLIMATE,
    COVER,
    COVER_STATUS,
    LIGHT,
    LIGHT_ON,
    MAX_ZONES,
    OTHER,
    SLEEP,
)
from .exceptions import CannotAuthenticate, CannotConnect


@dataclass
class ComelitSerialBridgeObject:
    """Comelit SimpleHome Serial bridge class."""

    index: int
    name: str
    status: int
    human_status: str
    type: str
    val: int | dict[Any, Any]  # Temperature or Humidity (CLIMATE)
    protected: int
    zone: str


@dataclass
class ComelitVedoObject:
    """Comelit SimpleHome VEDO class."""

    index: int
    name: str
    p1: bool
    p2: bool
    zone_open: int
    ready: bool
    armed: bool
    alarm: bool
    alarm_memory: bool
    sabotage: bool
    anomaly: bool
    in_time: bool
    out_time: bool


class ComeliteSerialBridgeAPi:
    """Queries Comelit SimpleHome Serial bridge."""

    def __init__(self, host: str, alarm_pin: int) -> None:
        """Initialize the session."""
        self.host = host
        self.alarm_pin = alarm_pin
        self.base_url = f"http://{self.host}"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.5",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
        }
        jar = aiohttp.CookieJar(unsafe=True)
        self.session = aiohttp.ClientSession(cookie_jar=jar)
        self._unique_id: str | None = None
        self._devices: dict[str, dict[int, ComelitSerialBridgeObject]] = {}
        self._alarm: dict[str, dict[int, ComelitVedoObject]] = {}
        self._alarm_logged: bool = False

    async def _get_devices(self, device_type: str) -> dict[str, Any]:
        """Get devices description."""
        timestamp = datetime.now().strftime("%s")
        url = f"{self.base_url}/user/icon_desc.json?type={device_type}&_={timestamp}"
        response = await self.session.get(
            url,
            headers=self.headers,
            timeout=10,
        )

        return await response.json() if response.status == 200 else {}

    async def _set_device_status(
        self, device_type: str, index: int, action: int
    ) -> bool:
        """Set device action.
        0 = off/close
        1 = on/open
        """
        timestamp = datetime.now().strftime("%s")
        url = f"{self.base_url}/user/action.cgi?type={device_type}&num{action}={index}&_={timestamp}"
        response = await self.session.get(
            url,
            headers=self.headers,
            timeout=10,
        )
        return response.status == 200

    async def _get_device_status(self, device_type: str, index: int) -> int:
        """Get device status, -1 means API call failed."""
        url = f"{self.base_url}/user/icon_status.json?type={device_type}"
        response = await self.session.get(
            url,
            headers=self.headers,
            timeout=10,
        )
        if response.status == 200:
            json = await response.json()
            _LOGGER.debug("Device %s status: %s", device_type, json["status"])
            return json["status"][index]
        return -1

    async def _set_cookie(self, value: str) -> None:
        """Enable required session cookie."""
        self.session.cookie_jar.update_cookies(
            SimpleCookie(f"domain={self.host}; name=sid; value=1;")
        )

    async def _do_alarm_login(self) -> bool:
        """Login into VEDO system via Comelit Serial Bridge."""
        payload = {"alm": self.alarm_pin}
        url = f"{self.base_url}/login.cgi"
        response = await self.session.post(
            url,
            data=payload,
            headers=self.headers,
            timeout=10,
        )
        if "sid" not in response.cookies:
            _LOGGER.debug('No "sid" cookie in VEDO login response for %s', self.host)
            return False

        await self._set_cookie(response.cookies["sid"])

        return response.status == 200

    async def _get_alarm_desc(self) -> dict[str, Any]:
        """Get alarm description for VEDO system."""
        timestamp = datetime.now().strftime("%s")
        url = f"{self.base_url}/user/vedo_area_desc.json?_={timestamp}"
        response = await self.session.get(
            url,
            headers=self.headers,
            timeout=10,
        )

        return await response.json() if response.status == 200 else {}

    async def _get_alarm_stat(self) -> dict[str, Any]:
        """Get alarm statistics for VEDO system."""
        timestamp = datetime.now().strftime("%s")
        url = f"{self.base_url}/user/vedo_area_stat.json?_={timestamp}"
        response = await self.session.get(
            url,
            headers=self.headers,
            timeout=10,
        )

        return await response.json() if response.status == 200 else {}

    async def _translate_device_status(self, dev_type: str, dev_status: int) -> str:
        """Makes status human readable."""

        if dev_type == COVER:
            return COVER_STATUS[dev_status]

        return "on" if dev_status == LIGHT_ON else "off"

    async def login(self) -> bool:
        """Login to Serial Bridge device."""
        _LOGGER.info("Logging into Serial Bridge %s", self.host)
        url = f"{self.base_url}/login.json"
        response = await self.session.get(
            url,
            headers=self.headers,
            timeout=10,
        )

        return response.status == 200

    async def light_switch(self, index: int, action: int) -> bool:
        """Set status of the light."""
        return await self._set_device_status(LIGHT, index, action)

    async def light_status(self, index: int) -> int:
        """Get status of the light."""
        await asyncio.sleep(SLEEP)
        return await self._get_device_status(LIGHT, index)

    async def cover_move(self, index: int, action: int) -> bool:
        """Move cover up/down."""
        return await self._set_device_status(COVER, index, action)

    async def cover_status(self, index: int) -> int:
        """Get cover status."""
        await asyncio.sleep(SLEEP)
        return await self._get_device_status(COVER, index)

    async def get_all_devices(self) -> dict[str, dict[int, ComelitSerialBridgeObject]]:
        """Get all connected devices."""

        _LOGGER.debug("Getting all devices for host %s", self.host)

        for dev_type in (CLIMATE, COVER, LIGHT, OTHER):
            reply_json = await self._get_devices(dev_type)
            _LOGGER.debug(
                "List of devices of type %s: %s",
                dev_type,
                reply_json,
            )
            devices = {}
            for i in range(reply_json["num"]):
                status = reply_json["status"][i]
                dev_info = ComelitSerialBridgeObject(
                    index=i,
                    name=reply_json["desc"][i],
                    status=status,
                    human_status=await self._translate_device_status(dev_type, status),
                    type=dev_type,
                    val=reply_json["val"][i],
                    protected=reply_json["protected"][i],
                    zone=reply_json["env_desc"][reply_json["env"][i]],
                )
                devices.update({i: dev_info})
            self._devices.update({dev_type: devices})

        return self._devices

    async def alarm_login(self) -> bool:
        """Login to vedo alarm system."""
        _LOGGER.debug("Logging into %s (VEDO)", self.host)
        try:
            self._alarm_logged = await self._do_alarm_login()
        except (asyncio.exceptions.TimeoutError, aiohttp.ClientConnectorError) as exc:
            _LOGGER.warning("Connection error for %s", self.host)
            raise CannotConnect from exc

        if not self._alarm_logged:
            _LOGGER.warning("Authentication failed for %s (VEDO)", self.host)
            raise CannotAuthenticate

        await asyncio.sleep(SLEEP)
        return True

    async def get_alarm_config(self) -> dict[str, dict[int, ComelitVedoObject]]:
        """Get Comelit SimpleHome alarm configuration."""

        await self.alarm_login()

        reply_json_desc = await self._get_alarm_desc()
        _LOGGER.debug("Alarm description: %s", reply_json_desc)
        reply_json_stat = await self._get_alarm_stat()
        _LOGGER.debug("Alarm statistics: %s", reply_json_stat)

        if (reply_json_desc or reply_json_stat) is {}:
            return {}

        alarms = {}
        for i in range(MAX_ZONES):
            if reply_json_desc["description"][i] == "":
                continue
            vedo = ComelitVedoObject(
                index=i,
                name=reply_json_desc["description"][i],
                p1=reply_json_desc["p1_pres"][i],
                p2=reply_json_desc["p2_pres"][i],
                zone_open=reply_json_stat["zone_open"],
                ready=reply_json_stat["ready"][i],
                armed=reply_json_stat["armed"][i],
                alarm=reply_json_stat["alarm"][i],
                alarm_memory=reply_json_stat["alarm_memory"][i],
                sabotage=reply_json_stat["sabotage"][i],
                anomaly=reply_json_stat["anomaly"][i],
                in_time=reply_json_stat["in_time"][i],
                out_time=reply_json_stat["out_time"][i],
            )
            alarms.update({i: vedo})
        self._alarm.update({"alarm": alarms})

        return self._alarm

    async def logout(self) -> None:
        """Comelit Simple Home Serial bridge logout."""
        self.session.cookie_jar.clear()

    async def close(self) -> None:
        """Comelit Simple Home Serial close session."""
        await self.session.close()
