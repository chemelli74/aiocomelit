"""Support for Comelit SimpleHome."""
import asyncio
from dataclasses import dataclass
from datetime import datetime
from http.cookies import SimpleCookie
from typing import Any

import aiohttp
import pint

from .const import (
    _LOGGER,
    ALARM_FIELDS,
    ALARM_MAX_ZONES,
    BRIDGE,
    CLIMATE,
    COVER,
    IRRIGATION,
    LIGHT,
    OTHER,
    SCENARIO,
    SLEEP,
    STATE_COVER,
    STATE_ERROR,
    STATE_ON,
    VEDO,
    WATT,
)
from .exceptions import CannotAuthenticate, CannotConnect, CannotRetrieveData


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
    power: float
    power_unit: str = WATT


@dataclass
class ComelitVedoObject:
    """Comelit SimpleHome VEDO class."""

    index: int
    name: str
    p1: bool
    p2: bool
    ready: bool
    armed: bool
    alarm: bool
    alarm_memory: bool
    sabotage: bool
    anomaly: bool
    in_time: bool
    out_time: bool
    human_status: str


class ComelitCommonApi:
    """Common API calls for Comelit SimpleHome devices."""

    def __init__(self, host: str, port: int, pin: int) -> None:
        """Initialize the session."""
        self.host = f"{host}:{port}"
        self.device_pin = pin
        self.base_url = f"http://{host}:{port}"
        self._headers = {
            "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0",
            "Accept-Language": "en-GB,en;q=0.5",
            "X-Requested-With": "XMLHttpRequest",
        }
        jar = aiohttp.CookieJar(unsafe=True)
        self._session = aiohttp.ClientSession(cookie_jar=jar)

    async def _get_page_result(
        self, page: str, reply_json: bool = True
    ) -> tuple[int, dict[str, Any]]:
        """Return status and data from a GET query."""
        _LOGGER.debug("GET page %s [%s]", page, self.host)
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

        _LOGGER.debug("GET response %s [%s]", await response.text(), self.host)

        if not reply_json:
            _LOGGER.debug("GET response is empty [%s]", self.host)
            return response.status

        data = await response.json() if response.status == 200 else {}
        return response.status, data

    async def _post_page_result(
        self, page: str, payload: dict[str, Any]
    ) -> SimpleCookie[str]:
        """Return status and data from a POST query."""
        _LOGGER.debug("POST page %s [%s]", page, self.host)
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

        _LOGGER.debug("POST response %s [%s]", await response.text(), self.host)
        return response.cookies

    async def _check_logged_in(self, host_type: str) -> bool:
        """Check if login is active."""
        reply_status, reply_json = await self._get_page_result("/login.json")

        _LOGGER.debug("%s login reply: %s", host_type, reply_json)
        if host_type == BRIDGE:
            logged = reply_json["domus"] != "000000000000"
        else:
            logged = reply_json["logged"] == 1

        return logged

    async def _login(self, payload: dict[str, Any], host_type: str) -> bool:
        """Login into Comelit device."""
        _LOGGER.debug("Logging into host %s [%s]", self.host, host_type)

        if await self._check_logged_in(host_type):
            return True

        cookies = await self._post_page_result("/login.cgi", payload)

        if not cookies:
            _LOGGER.warning(
                "Authentication failed for host %s [%s]: no cookies received",
                self.host,
                host_type,
            )
            raise CannotAuthenticate

        self._session.cookie_jar.update_cookies(cookies)

        if await self._check_logged_in(host_type):
            return True

        _LOGGER.warning(
            "Authentication failed for host %s [%s]: generic error",
            self.host,
            host_type,
        )
        raise CannotAuthenticate

    async def logout(self) -> None:
        """Comelit Simple Home logout."""
        payload = {"logout": 1}
        await self._post_page_result("/login.cgi", payload)
        self._session.cookie_jar.clear()

    async def close(self) -> None:
        """Comelit Simple Home close session."""
        await self._session.close()


class ComeliteSerialBridgeApi(ComelitCommonApi):
    """Queries Comelit SimpleHome Serial bridge."""

    def __init__(self, host: str, port: int, bridge_pin: int) -> None:
        """Initialize the session."""
        super().__init__(host, port, bridge_pin)
        self._devices: dict[str, dict[int, ComelitSerialBridgeObject]] = {}

    async def _translate_device_status(self, dev_type: str, dev_status: int) -> str:
        """Makes status human readable."""

        if dev_type == COVER:
            return STATE_COVER[dev_status]

        return "on" if dev_status == STATE_ON else "off"

    async def set_device_status(
        self, device_type: str, index: int, action: int
    ) -> bool:
        """Set device action.

        action:
            0 = off/close
            1 = on/open

        """
        reply_status = await self._get_page_result(
            f"/user/action.cgi?type={device_type}&num{action}={index}", False
        )
        return reply_status == 200

    async def get_device_status(self, device_type: str, index: int) -> int:
        """Get device status, -1 means API call failed."""
        await asyncio.sleep(SLEEP)
        reply_status, reply_json = await self._get_page_result(
            f"/user/icon_status.json?type={device_type}"
        )
        if reply_status != 200:
            return STATE_ERROR

        _LOGGER.debug(
            "Device %s[%s] status: %s", device_type, index, reply_json["status"][index]
        )
        return reply_json["status"][index]

    async def login(self) -> bool:
        """Login to Serial Bridge device."""
        payload = {"dom": self.device_pin}
        return await self._login(payload, BRIDGE)

    async def get_all_devices(self) -> dict[str, dict[int, ComelitSerialBridgeObject]]:
        """Get all connected devices."""

        _LOGGER.debug("Getting all devices for host %s", self.host)

        for dev_type in (CLIMATE, COVER, LIGHT, IRRIGATION, OTHER, SCENARIO):
            reply_status, reply_json = await self._get_page_result(
                f"/user/icon_desc.json?type={dev_type}"
            )
            _LOGGER.debug(
                "List of devices of type %s: %s",
                dev_type,
                reply_json,
            )
            reply_counter_json: dict[str, Any] = {}
            if dev_type == OTHER and reply_json["num"] > 0:
                reply_status, reply_counter_json = await self._get_page_result(
                    "/user/counter.json"
                )
            devices = {}
            ureg = pint.UnitRegistry()
            ureg.default_format = "~"
            for i in range(reply_json["num"]):
                # Guard against "scenario", that has 32 devices even if none is configured
                if reply_json["desc"][i] == "":
                    continue
                status = reply_json["status"][i]
                power = 0.0
                if instant_values := reply_counter_json.get("instant"):
                    instant = ureg(instant_values[i])
                    if not instant.dimensionless:
                        power = ureg.convert(
                            instant.magnitude, str(instant.units), WATT
                        )
                dev_info = ComelitSerialBridgeObject(
                    index=i,
                    name=reply_json["desc"][i],
                    status=status,
                    human_status=await self._translate_device_status(dev_type, status),
                    type=dev_type,
                    val=reply_json["val"][i],
                    protected=reply_json["protected"][i],
                    zone=reply_json["env_desc"][reply_json["env"][i]]
                    if not dev_type == SCENARIO
                    else "",
                    power=power,
                )
                devices.update({i: dev_info})
            self._devices.update({dev_type: devices})

        return self._devices


class ComelitVedoApi(ComelitCommonApi):
    """Queries Comelit SimpleHome VEDO alarm."""

    def __init__(self, host: str, port: int, alarm_pin: int) -> None:
        """Initialize the VEDO session."""
        super().__init__(host, port, alarm_pin)
        self._json_desc: dict[str, Any] = {}

    async def _translate_zone_status(self, zone: ComelitVedoObject) -> str:
        """Translate Zone status."""

        for field in ALARM_FIELDS.keys():
            if getattr(zone, field):
                return ALARM_FIELDS[field]

        return "disabled"

    async def set_zone_status(self, index: int, action: str) -> bool:
        """Set zone action.

        action:
            tot = enable
            dis = disable

        index:
            32 = all zones
             n = specific zone

        """
        reply_status = await self._get_page_result(
            f"/action.cgi?vedo=1&{action}={index}", False
        )
        return reply_status == 200

    async def get_zone_status(self, index: int) -> ComelitVedoObject:
        """Get zone status."""
        await asyncio.sleep(SLEEP * 2)
        reply_status, reply_json = await self._get_page_result("/user/area_stat.json")
        if reply_status != 200:
            raise CannotRetrieveData

        _LOGGER.debug("Alarm statistics: %s", reply_json)

        vedo = ComelitVedoObject(
            index=index,
            name=self._json_desc["description"][index],
            p1=self._json_desc["p1_pres"][index],
            p2=self._json_desc["p2_pres"][index],
            ready=reply_json["ready"][index],
            armed=reply_json["armed"][index],
            alarm=reply_json["alarm"][index],
            alarm_memory=reply_json["alarm_memory"][index],
            sabotage=reply_json["sabotage"][index],
            anomaly=reply_json["anomaly"][index],
            in_time=reply_json["in_time"][index],
            out_time=reply_json["out_time"][index],
            human_status="",
        )
        vedo.human_status = await self._translate_zone_status(vedo)
        _LOGGER.debug(vedo)
        return vedo

    async def login(self) -> bool:
        """Login to VEDO system."""
        payload = {"code": self.device_pin}
        return await self._login(payload, VEDO)

    async def get_config_and_status(
        self,
    ) -> dict[str, dict[int, ComelitVedoObject]]:
        """Get VEDO system configuration and status."""
        reply_status, reply_json_desc = await self._get_page_result(
            "/user/area_desc.json"
        )
        _LOGGER.debug("Alarm description: %s", reply_json_desc)
        self._json_desc = reply_json_desc

        alarms = {}
        for i in range(ALARM_MAX_ZONES):
            if not reply_json_desc["present"][i]:
                continue
            vedo = await self.get_zone_status(i)
            alarms.update({i: vedo})

        return {"alarm": alarms}
