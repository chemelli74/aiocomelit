"""Support for Comelit SimpleHome."""
import asyncio
import functools
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from http.cookies import SimpleCookie
from typing import Any

import aiohttp
import pint
from yarl import URL

from .const import (
    _LOGGER,
    ALARM_AREA_STATUS,
    ALARM_AREAS,
    ALARM_ZONE_STATUS,
    ALARM_ZONES,
    BRIDGE,
    CLIMATE,
    COVER,
    IRRIGATION,
    LIGHT,
    OTHER,
    SCENARIO,
    SLEEP,
    STATE_COVER,
    STATE_ON,
    VEDO,
    WATT,
    AlarmAreaState,
    AlarmZoneState,
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
class ComelitVedoAreaObject:
    """Comelit SimpleHome VEDO area class."""

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
    human_status: AlarmAreaState


@dataclass
class ComelitVedoZoneObject:
    """Comelit SimpleHome VEDO zone class."""

    index: int
    name: str
    status_api: str
    status: int
    human_status: AlarmZoneState


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
        self._session: aiohttp.ClientSession

    async def _get_page_result(
        self, page: str, reply_json: bool = True
    ) -> tuple[int, dict[str, Any]]:
        """Return status and data from a GET query."""
        _LOGGER.debug("GET page %s [%s]", page, self.host)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        url = f"{self.base_url}{page}&_={timestamp}"
        try:
            response = await self._session.get(
                url,
                headers=self._headers,
                timeout=10,
            )
        except (asyncio.TimeoutError, aiohttp.ClientConnectorError) as exc:
            _LOGGER.warning("Connection error during GET for host %s", self.host)
            raise CannotConnect from exc

        _LOGGER.debug("GET response %s [%s]", await response.text(), self.host)

        if response.status != 200:
            _LOGGER.warning(
                "Response error to GET for host %s: code %s", self.host, response.status
            )
            raise CannotRetrieveData

        if not reply_json:
            _LOGGER.debug("GET response is empty [%s]", self.host)
            return response.status

        return response.status, await response.json()

    async def _post_page_result(
        self, page: str, payload: dict[str, Any]
    ) -> SimpleCookie:
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
        except (asyncio.TimeoutError, aiohttp.ClientConnectorError) as exc:
            _LOGGER.warning("Connection error during POST for host %s", self.host)
            raise CannotConnect from exc

        _LOGGER.debug("POST response %s [%s]", await response.text(), self.host)

        if response.status != 200:
            _LOGGER.warning(
                "Response error to POST for host %s: code %s",
                self.host,
                response.status,
            )
            raise CannotRetrieveData

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

    @abstractmethod
    async def login(self) -> bool:
        """Login to Comelit device."""

    async def _login(self, payload: dict[str, Any], host_type: str) -> bool:
        """Login into Comelit device."""
        _LOGGER.debug("Logging into host %s [%s]", self.host, host_type)

        if not hasattr(self, "_session") or self._session.closed:
            _LOGGER.debug("Creating HTTP ClientSession")
            jar = aiohttp.CookieJar(unsafe=True)
            connector = aiohttp.TCPConnector(force_close=True)
            self._session = aiohttp.ClientSession(cookie_jar=jar, connector=connector)

        if await self._check_logged_in(host_type):
            return True

        cookies = await self._post_page_result("/login.cgi", payload)
        _LOGGER.debug("Cookies for host %s: %s", self.host, cookies)

        if not cookies:
            _LOGGER.warning(
                "Authentication failed for host %s [%s]: no cookies received",
                self.host,
                host_type,
            )
            raise CannotAuthenticate

        self._session.cookie_jar.update_cookies(cookies, URL(self.base_url))

        if await self._check_logged_in(host_type):
            await asyncio.sleep(SLEEP)
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
        if hasattr(self, "_session"):
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
        """Get device status."""
        reply_status, reply_json = await self._get_page_result(
            f"/user/icon_status.json?type={device_type}"
        )
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

        loop = asyncio.get_running_loop()
        ureg = await loop.run_in_executor(
            None, functools.partial(pint.UnitRegistry, cache_folder=":auto:")
        )
        ureg.default_format = "~"

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

    async def _translate_zone_status(
        self, zone: ComelitVedoZoneObject
    ) -> AlarmZoneState:
        """Translate ZONE status."""

        for status in ALARM_ZONE_STATUS:
            if zone.status & status != 0:
                return ALARM_ZONE_STATUS[status]

        return AlarmZoneState.REST

    async def _translate_area_status(
        self, area: ComelitVedoAreaObject
    ) -> AlarmAreaState:
        """Translate AREA status."""

        for field in ALARM_AREA_STATUS:
            if getattr(area, field):
                return ALARM_AREA_STATUS[field]

        return AlarmAreaState.DISARMED

    async def _create_area_object(
        self, json_area_desc: dict[str, Any], json_area_stat: dict[str, Any], index: int
    ) -> ComelitVedoAreaObject:
        """Get area status."""

        area = ComelitVedoAreaObject(
            index=index,
            name=json_area_desc["description"][index],
            p1=json_area_desc["p1_pres"][index],
            p2=json_area_desc["p2_pres"][index],
            ready=json_area_stat["ready"][index],
            armed=json_area_stat["armed"][index],
            alarm=json_area_stat["alarm"][index],
            alarm_memory=json_area_stat["alarm_memory"][index],
            sabotage=json_area_stat["sabotage"][index],
            anomaly=json_area_stat["anomaly"][index],
            in_time=json_area_stat["in_time"][index],
            out_time=json_area_stat["out_time"][index],
            human_status=AlarmAreaState.UNKNOWN,
        )
        area.human_status = await self._translate_area_status(area)
        _LOGGER.debug(area)
        return area

    async def _create_zone_object(
        self, json_zone_desc: dict[str, Any], json_zone_stat: dict[str, Any], index: int
    ) -> ComelitVedoZoneObject:
        """Create zone object."""

        status_api = json_zone_stat["status"].split(",")[index]

        zone = ComelitVedoZoneObject(
            index=index,
            name=json_zone_desc["description"][index],
            status=int(status_api, 16),
            status_api=status_api,
            human_status=AlarmZoneState.UNKNOWN,
        )
        zone.human_status = await self._translate_zone_status(zone)
        _LOGGER.debug(zone)
        return zone

    async def set_zone_status(
        self, index: int, action: str, force: bool = False
    ) -> bool:
        """Set zone action.

        action:
            tot = enable
            dis = disable

        index:
            32 = all zones
             n = specific zone

        force:
            False = don't force action
            True  = force action

        """

        reply_status = await self._get_page_result(
            f"/action.cgi?vedo=1&{action}={index}&force={int(force)}", False
        )
        return reply_status == 200

    async def login(self) -> bool:
        """Login to VEDO system."""
        payload = {"code": self.device_pin}
        return await self._login(payload, VEDO)

    async def get_area_status(
        self, area: ComelitVedoAreaObject
    ) -> ComelitVedoAreaObject:
        """Get AREA status."""
        reply_status, reply_json_area_stat = await self._get_page_result(
            "/user/area_stat.json"
        )
        _LOGGER.debug("Alarm AREA statistics: %s", reply_json_area_stat)

        description = {"description": area.name, "p1_pres": area.p1, "p2_pres": area.p2}

        return await self._create_area_object(
            description, reply_json_area_stat, area.index
        )

    async def get_all_areas_and_zones(
        self,
    ) -> dict[str, dict[int, Any]]:
        """Get all VEDO system AREA and ZONE."""
        reply_status, reply_json_area_desc = await self._get_page_result(
            "/user/area_desc.json"
        )
        _LOGGER.debug("Alarm AREA description: %s", reply_json_area_desc)

        reply_status, reply_json_zone_desc = await self._get_page_result(
            "/user/zone_desc.json"
        )
        _LOGGER.debug("Alarm ZONE description: %s", reply_json_zone_desc)

        reply_status, reply_json_area_stat = await self._get_page_result(
            "/user/area_stat.json"
        )
        _LOGGER.debug("Alarm AREA statistics: %s", reply_json_area_stat)

        reply_status, reply_json_zone_stat = await self._get_page_result(
            "/user/zone_stat.json"
        )
        _LOGGER.debug("Alarm ZONE statistics: %s", reply_json_zone_stat)

        list_areas: list[int] = reply_json_area_desc["present"]
        areas = {}
        for i in range(len(list_areas)):
            if not list_areas[i]:
                _LOGGER.debug("Alarm skipping non present AREA [%i]", i)
                continue
            area = await self._create_area_object(
                reply_json_area_desc, reply_json_area_stat, i
            )
            areas.update({i: area})

        list_zones: list[int] = reply_json_zone_desc["in_area"]
        zones = {}
        for i in range(len(list_zones)):
            if not list_zones[i]:
                _LOGGER.debug("Alarm skipping non present ZONE [%i]", i)
                continue
            zone = await self._create_zone_object(
                reply_json_zone_desc, reply_json_zone_stat, i
            )
            zones.update({i: zone})

        return {ALARM_AREAS: areas, ALARM_ZONES: zones}
