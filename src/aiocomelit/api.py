"""Support for Comelit SimpleHome."""
import asyncio
from dataclasses import dataclass
from datetime import datetime
from http.cookies import SimpleCookie
from typing import Any

import aiohttp

from .const import (
    _LOGGER,
    BRIDGE,
    CLIMATE,
    COVER,
    COVER_STATUS,
    ERROR_STATUS,
    LIGHT,
    LIGHT_ON,
    MAX_ZONES,
    OTHER,
    SLEEP,
    VEDO,
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


class ComelitCommonApi:
    """Common API calls for Comelit SimpleHome devices."""

    def __init__(self, host: str, pin: int) -> None:
        """Initialize the session."""
        self.host = host
        self.device_pin = pin
        self.base_url = f"http://{self.host}"
        self._headers = {
            "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.5",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
        }
        jar = aiohttp.CookieJar(unsafe=True)
        self._session = aiohttp.ClientSession(cookie_jar=jar)

    async def _get_page_result(
        self, page: str, reply_json: bool = True
    ) -> tuple[int, dict[str, Any]]:
        """Return status and data from a GET query."""
        timestamp = datetime.now().strftime("%s")
        url = f"{self.base_url}{page}&_={timestamp}"
        try:
            response = await self._session.get(
                url,
                headers=self._headers,
                timeout=10,
            )
        except (asyncio.exceptions.TimeoutError, aiohttp.ClientConnectorError) as exc:
            _LOGGER.warning("Connection error during GET for host %s", self.host)
            raise CannotConnect from exc

        if not reply_json:
            return response.status

        data = await response.json() if response.status == 200 else {}
        return response.status, data

    async def _post_page_result(
        self, page: str, payload: dict[str, Any]
    ) -> SimpleCookie[str]:
        """Return status and data from a POST query."""
        url = f"{self.base_url}{page}"
        try:
            response = await self._session.post(
                url,
                data=payload,
                headers=self._headers,
                timeout=10,
            )
        except (asyncio.exceptions.TimeoutError, aiohttp.ClientConnectorError) as exc:
            _LOGGER.warning("Connection error during POST for host %s", self.host)
            raise CannotConnect from exc

        return response.cookies

    async def _login(self, payload: dict[str, Any], host_type: str) -> bool:
        """Login into Comelit device."""
        _LOGGER.debug("Logging into host %s [%s]", self.host, host_type)

        if self.device_pin:
            cookies = await self._post_page_result("/login.cgi", payload)

            if not cookies:
                _LOGGER.warning(
                    "Authentication failed for host %s [%s]: no cookies received",
                    self.host,
                    host_type,
                )
                raise CannotAuthenticate

            self._session.cookie_jar.update_cookies(cookies)

        reply_status, reply_json = await self._get_page_result("/login.json")

        if host_type == BRIDGE:
            logged = reply_json["domus"] != "000000000000"
        else:
            logged = reply_json["logged"] == 1

        if not logged:
            _LOGGER.warning(
                "Authentication failed for host %s [%s]: generic error",
                self.host,
                host_type,
            )
            raise CannotAuthenticate

        return True

    async def logout(self) -> None:
        """Comelit Simple Home logout."""
        self._session.cookie_jar.clear()

    async def close(self) -> None:
        """Comelit Simple Home close session."""
        await self._session.close()


class ComeliteSerialBridgeApi(ComelitCommonApi):
    """Queries Comelit SimpleHome Serial bridge."""

    def __init__(self, host: str, bridge_pin: int) -> None:
        """Initialize the session."""
        super().__init__(host, bridge_pin)
        self._devices: dict[str, dict[int, ComelitSerialBridgeObject]] = {}

    async def _set_device_status(
        self, device_type: str, index: int, action: int
    ) -> bool:
        """Set device action.
        0 = off/close
        1 = on/open
        """
        reply_status = await self._get_page_result(
            f"/user/action.cgi?type={device_type}&num{action}={index}", False
        )
        return reply_status == 200

    async def _get_device_status(self, device_type: str, index: int) -> int:
        """Get device status, -1 means API call failed."""

        reply_status, reply_json = await self._get_page_result(
            f"/user/icon_status.json?type={device_type}"
        )
        if reply_status != 200:
            return ERROR_STATUS

        _LOGGER.debug(
            "Device %s[%s] status: %s", device_type, index, reply_json["status"]
        )
        return reply_json["status"][index]

    async def _translate_device_status(self, dev_type: str, dev_status: int) -> str:
        """Makes status human readable."""

        if dev_type == COVER:
            return COVER_STATUS[dev_status]

        return "on" if dev_status == LIGHT_ON else "off"

    async def login(self) -> bool:
        """Login to Serial Bridge device."""
        payload = {"dom": self.device_pin}
        return await self._login(payload, BRIDGE)

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
            reply_status, reply_json = await self._get_page_result(
                f"/user/icon_desc.json?type={dev_type}"
            )
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


class ComelitVedoApi(ComelitCommonApi):
    """Queries Comelit SimpleHome VEDO alarm."""

    def __init__(self, host: str, alarm_pin: int) -> None:
        """Initialize the VEDO session."""
        super().__init__(host, alarm_pin)
        self._alarm: dict[str, dict[int, ComelitVedoObject]] = {}

    async def login(self) -> bool:
        """Login to VEDO system."""
        payload = {"code": self.device_pin}
        return await self._login(payload, VEDO)

    async def get_config(self) -> dict[str, dict[int, ComelitVedoObject]]:
        """Get VEDO system configuration."""
        reply_status, reply_json_desc = await self._get_page_result(
            "/user/area_desc.json"
        )
        _LOGGER.debug("Alarm description: %s", reply_json_desc)
        reply_status, reply_json_stat = await self._get_page_result(
            "/user/area_stat.json"
        )
        _LOGGER.debug("Alarm statistics: %s", reply_json_stat)

        if (reply_json_desc or reply_json_stat) is {}:
            return {}

        alarms = {}
        for i in range(MAX_ZONES):
            if not reply_json_desc["p1_pres"][i] and not reply_json_desc["p2_pres"][i]:
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
