"""Support for Comelit SimpleHome."""

import asyncio
import functools
from abc import abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from typing import Any, TypedDict, cast

import pint
from aiohttp import ClientConnectorError, ClientSession
from yarl import URL

from .const import (
    _LOGGER,
    ALARM_AREA_STATUS,
    ALARM_ZONE_STATUS,
    BRIDGE,
    CLIMATE,
    COVER,
    DEFAULT_TIMEOUT,
    IRRIGATION,
    LIGHT,
    OTHER,
    SCENARIO,
    SLEEP_BETWEEN_BRIDGE_CALLS,
    SLEEP_BETWEEN_VEDO_CALLS,
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
    val: int | list[list[Any]]  # Temperature or Humidity (CLIMATE)
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
    armed: int
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


class AlarmDataObject(TypedDict):
    """TypedDict for Alarm data objects."""

    alarm_areas: dict[int, ComelitVedoAreaObject]
    alarm_zones: dict[int, ComelitVedoZoneObject]


class ComelitCommonApi:
    """Common API calls for Comelit SimpleHome devices."""

    _vedo_url_suffix: str
    _vedo_url_action: str
    _host_type: str

    def __init__(self, host: str, port: int, pin: int, session: ClientSession) -> None:
        """Initialize the session."""
        self.device_pin = pin
        self.base_url = f"http://{host}:{port}"
        self._headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:78.0"
                "Gecko/20100101 Firefox/78.0"
            ),
            "Accept-Language": "en-GB,en;q=0.5",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
        }
        self._logging = f"{self._host_type} ({host}:{port})"
        self._session = session
        self._json_data: list[dict[Any, Any]] = [{}, {}, {}, {}, {}]

    async def _get_page_result(
        self,
        page: str,
        reply_json: bool = True,
    ) -> tuple[int, dict[str, Any]]:
        """Return status and data from a GET query."""
        _LOGGER.debug("[%s] GET page %s", self._logging, page)
        timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
        url = f"{self.base_url}{page}&_={timestamp}"
        try:
            response = await self._session.get(
                url,
                headers=self._headers,
                timeout=DEFAULT_TIMEOUT,
            )
        except (TimeoutError, ClientConnectorError) as exc:
            raise CannotConnect("Connection error during GET") from exc

        _LOGGER.debug(
            "[%s] GET response %s",
            self._logging,
            await response.text(),
        )

        if response.status != HTTPStatus.OK:
            raise CannotRetrieveData(f"GET response status {response.status}")

        if not reply_json:
            _LOGGER.debug("[%s] GET response is empty", self._logging)
            return response.status, {}

        return response.status, await response.json()

    async def _post_page_result(
        self,
        page: str,
        payload: dict[str, Any],
    ) -> SimpleCookie:
        """Return status and data from a POST query."""
        _LOGGER.debug("[%s] POST page %s", self._logging, page)
        url = f"{self.base_url}{page}"
        try:
            response = await self._session.post(
                url,
                data=payload,
                headers=self._headers,
                timeout=DEFAULT_TIMEOUT,
            )
        except (TimeoutError, ClientConnectorError) as exc:
            raise CannotConnect("Connection error during POST") from exc

        _LOGGER.debug("[%s] POST response %s", self._logging, await response.text())

        if response.status != HTTPStatus.OK:
            raise CannotRetrieveData(f"POST response status {response.status}")

        return cast("SimpleCookie", response.cookies)

    async def _is_session_active(self) -> bool:
        """Check if aiohttp session is still active."""
        return hasattr(self, "_session") and not self._session.closed

    async def _check_logged_in(self, host_type: str) -> bool:
        """Check if login is active."""
        reply_status, reply_json = await self._get_page_result("/login.json")

        logged: bool
        _LOGGER.debug("[%s] Login reply: %s", self._logging, reply_json)
        if host_type == BRIDGE:
            logged = reply_json["domus"] != "000000000000"
        else:
            logged = reply_json["logged"] == 1

        return logged

    async def _sleep_between_call(self, seconds: float) -> None:
        """Sleep between one call and the next one."""
        _LOGGER.debug(
            "[%s] Sleeping for %s seconds before next call", self._logging, seconds
        )
        await asyncio.sleep(seconds)

    @abstractmethod
    async def login(self) -> bool:
        """Login to Comelit device."""

    async def _login(self, payload: dict[str, Any], host_type: str) -> bool:
        """Login into Comelit device."""
        _LOGGER.debug("[%s] Logging in", self._logging)

        if await self._check_logged_in(host_type):
            return True

        cookies = await self._post_page_result("/login.cgi", payload)
        _LOGGER.debug("[%s] Cookies: %s", self._logging, cookies)

        if not cookies:
            _LOGGER.warning(
                "[%s] Authentication failed: no cookies received", self._logging
            )
            raise CannotAuthenticate

        self._session.cookie_jar.update_cookies(cookies, URL(self.base_url))

        return await self._check_logged_in(host_type)

    async def logout(self) -> None:
        """Comelit Simple Home logout."""
        if await self._is_session_active():
            payload = {"logout": 1}
            await self._post_page_result("/login.cgi", payload)
            self._session.cookie_jar.clear()

    async def close(self) -> None:
        """Comelit Simple Home close session."""
        if await self._is_session_active():
            await self._session.close()

    async def _translate_zone_status(
        self,
        zone: ComelitVedoZoneObject,
    ) -> AlarmZoneState:
        """Translate ZONE status."""
        for status in ALARM_ZONE_STATUS:
            if zone.status & status != 0:
                return ALARM_ZONE_STATUS[status]

        return AlarmZoneState.REST

    async def _translate_area_status(
        self,
        area: ComelitVedoAreaObject,
    ) -> AlarmAreaState:
        """Translate AREA status."""
        for field in ALARM_AREA_STATUS:
            if getattr(area, field):
                return ALARM_AREA_STATUS[field]

        return AlarmAreaState.DISARMED

    async def _create_area_object(
        self,
        json_area_desc: dict[str, Any],
        json_area_stat: dict[str, Any],
        index: int,
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
        _LOGGER.debug("[%s] Area: %s", self._logging, area)
        return area

    async def _create_zone_object(
        self,
        json_zone_desc: dict[str, Any],
        json_zone_stat: dict[str, Any],
        index: int,
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
        _LOGGER.debug("[%s] Zone: %s", self._logging, zone)
        return zone

    async def _async_get_page_data(
        self,
        desc: str,
        page: str,
        present_check: str | int | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Return status and data from a specific GET query."""
        reply_status, reply_json = await self._get_page_result(page)
        _LOGGER.debug("[%s] Alarm %s: %s", self._logging, desc, reply_json)
        present = present_check in reply_json["present"] if "_desc" in page else True
        return (reply_json["logged"] and present), reply_json

    async def set_zone_status(
        self,
        index: int,
        action: str,
        force: bool = False,
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
        reply_status, reply_json = await self._get_page_result(
            f"{self._vedo_url_action}{action}={index}&force={int(force)}",
            False,
        )
        return reply_status == HTTPStatus.OK

    async def get_area_status(
        self,
        area: ComelitVedoAreaObject,
    ) -> ComelitVedoAreaObject:
        """Get AREA status."""
        reply_status, reply_json_area_stat = await self._async_get_page_data(
            "AREA statistics",
            f"/user/{self._vedo_url_suffix}area_stat.json",
        )
        description = {"description": area.name, "p1_pres": area.p1, "p2_pres": area.p2}

        return await self._create_area_object(
            description,
            reply_json_area_stat,
            area.index,
        )

    async def get_all_areas_and_zones(
        self,
    ) -> AlarmDataObject:
        """Get all VEDO system AREA and ZONE."""
        queries: dict[int, dict[str, Any]] = {
            1: {
                "desc": "AREA description",
                "page": f"/user/{self._vedo_url_suffix}area_desc.json",
                "present": 1,
            },
            2: {
                "desc": "ZONE description",
                "page": f"/user/{self._vedo_url_suffix}zone_desc.json",
                "present": "1",
            },
            3: {
                "desc": "AREA statistics",
                "page": f"/user/{self._vedo_url_suffix}area_stat.json",
                "present": None,
            },
            4: {
                "desc": "ZONE statistics",
                "page": f"/user/{self._vedo_url_suffix}zone_stat.json",
                "present": None,
            },
        }

        for index, info in queries.items():
            desc = info["desc"]
            page = info["page"]
            present = info["present"]
            if "_desc" in page and self._json_data[index]:
                _LOGGER.debug(
                    "[%s] Data for %s already retrieved, skipping", self._logging, desc
                )
                continue
            await self._sleep_between_call(SLEEP_BETWEEN_VEDO_CALLS)
            reply_status, reply_json = await self._async_get_page_data(
                desc,
                page,
                present,
            )
            if not reply_status:
                _LOGGER.debug(
                    "[%s] Login expired accessing %s, re-login attempt",
                    self._logging,
                    desc,
                )
                await self.login()
                await self._sleep_between_call(SLEEP_BETWEEN_VEDO_CALLS)
                reply_status, reply_json = await self._async_get_page_data(
                    desc,
                    page,
                    present,
                )
                if not reply_status:
                    raise CannotRetrieveData(
                        "Login expired and not working after a retry",
                    )
                _LOGGER.debug("[%s] Re-login successful", self._logging)
            self._json_data.insert(index, reply_json)

        list_areas: list[int] = self._json_data[1]["present"]
        areas: dict[int, ComelitVedoAreaObject] = {}
        for i in range(len(list_areas)):
            if not list_areas[i]:
                _LOGGER.debug(
                    "[%s] Alarm skipping non present AREA [%i]", self._logging, i
                )
                continue
            area = await self._create_area_object(
                self._json_data[1],
                self._json_data[3],
                i,
            )
            areas.update({i: area})

        list_zones: list[int] = self._json_data[2]["present"]
        zones: dict[int, ComelitVedoZoneObject] = {}
        for i in range(len(list_zones)):
            if not int(list_zones[i]):
                _LOGGER.debug(
                    "[%s] Alarm skipping non present ZONE [%i]", self._logging, i
                )
                continue
            zone = await self._create_zone_object(
                self._json_data[2],
                self._json_data[4],
                i,
            )
            zones.update({i: zone})

        return AlarmDataObject(alarm_areas=areas, alarm_zones=zones)


class ComeliteSerialBridgeApi(ComelitCommonApi):
    """Queries Comelit SimpleHome Serial bridge."""

    _vedo_url_suffix: str = "vedo_"
    _vedo_url_action: str = "/user/action.cgi?"
    _host_type = BRIDGE

    def __init__(
        self, host: str, port: int, bridge_pin: int, session: ClientSession
    ) -> None:
        """Initialize the session."""
        super().__init__(host, port, bridge_pin, session)
        self._devices: dict[str, dict[int, ComelitSerialBridgeObject]] = {}
        self._last_clima_command: datetime | None = None
        self._semaphore = asyncio.Semaphore()
        self._initialized = False

    async def _translate_device_status(self, dev_type: str, dev_status: int) -> str:
        """Make status human readable."""
        if dev_type == COVER:
            return STATE_COVER[dev_status]

        return "on" if dev_status == STATE_ON else "off"

    async def _set_thermo_humi_status(
        self,
        index: int,
        mode: str,
        action: str,
        value: float = 0,
    ) -> bool:
        """Set clima or humidity status.

        action:
            auto, man, on, off, set

        """
        await self._semaphore.acquire()
        if self._last_clima_command:
            delta_seconds = SLEEP_BETWEEN_BRIDGE_CALLS - round(
                (datetime.now(tz=UTC) - self._last_clima_command).total_seconds(),
                2,
            )
            if delta_seconds > 0:
                _LOGGER.debug(
                    "[%s] Climate calls needs to be queued (%ss) for proper execution",
                    self._logging,
                    delta_seconds,
                )
                await self._sleep_between_call(delta_seconds)

        reply_status, reply_json = await self._get_page_result(
            f"/user/action.cgi?clima={index}&{mode}={action}&val={int(value * 10)}",
            False,
        )
        self._last_clima_command = datetime.now(tz=UTC)
        self._semaphore.release()
        return reply_status == HTTPStatus.OK

    async def set_clima_status(self, index: int, action: str, temp: float = 0) -> bool:
        """Set clima status."""
        return await self._set_thermo_humi_status(index, "thermo", action, temp)

    async def set_humidity_status(
        self,
        index: int,
        action: str,
        humidity: float = 0,
    ) -> bool:
        """Set humidity status."""
        return await self._set_thermo_humi_status(index, "humi", action, humidity)

    async def set_device_status(
        self,
        device_type: str,
        index: int,
        action: int,
    ) -> bool:
        """Set device action.

        action:
            0 = off/close
            1 = on/open

        """
        reply_status, reply_json = await self._get_page_result(
            f"/user/action.cgi?type={device_type}&num{action}={index}",
            False,
        )
        return reply_status == HTTPStatus.OK

    async def get_device_status(self, device_type: str, index: int) -> int:
        """Get device status."""
        reply_status, reply_json = await self._get_page_result(
            f"/user/icon_status.json?type={device_type}",
        )
        _LOGGER.debug(
            "[%s] Device %s[%s] status: %s",
            self._logging,
            device_type,
            index,
            reply_json["status"][index],
        )
        return cast("int", reply_json["status"][index])

    async def login(self) -> bool:
        """Login to Serial Bridge device."""
        payload = {"dom": self.device_pin}
        return await self._login(payload, BRIDGE)

    async def get_all_devices(self) -> dict[str, dict[int, ComelitSerialBridgeObject]]:
        """Get all connected devices."""
        _LOGGER.debug("[%s] Getting all devices", self._logging)

        loop = asyncio.get_running_loop()
        ureg = await loop.run_in_executor(
            None,
            functools.partial(pint.UnitRegistry, cache_folder=":auto:"),
        )
        ureg.formatter.default_format = "~"

        for dev_type in (CLIMATE, COVER, LIGHT, IRRIGATION, OTHER, SCENARIO):
            reply_status, reply_json = await self._get_page_result(
                f"/user/icon_desc.json?type={dev_type}",
            )
            _LOGGER.debug(
                "[%s] List of devices of type %s: %s",
                self._logging,
                dev_type,
                reply_json,
            )
            reply_counter_json: dict[str, Any] = {}
            num_devices = reply_json["num"]
            if dev_type == OTHER and num_devices > 0:
                reply_status, reply_counter_json = await self._get_page_result(
                    "/user/counter.json",
                )
            devices: dict[int, ComelitSerialBridgeObject] = {}
            desc = reply_json["desc"]
            # Guard against some old bridges: sporadically return no data
            if desc == [] and num_devices > 0:
                if self._initialized:
                    _LOGGER.debug(
                        "[%s] Skipping '%s': empty data description",
                        self._logging,
                        dev_type,
                    )
                    continue
                raise CannotRetrieveData("Empty reply during initialization")
            for i in range(num_devices):
                # Guard against "scenario": list 32 devices even if none is configured
                if desc[i] == "":
                    continue
                status = reply_json["status"][i]
                power = 0.0
                if instant_values := reply_counter_json.get("instant"):
                    instant = ureg(instant_values[i])
                    if not instant.dimensionless:
                        power = ureg.convert(
                            instant.magnitude,
                            str(instant.units),
                            WATT,
                        )
                dev_info = ComelitSerialBridgeObject(
                    index=i,
                    name=reply_json["desc"][i],
                    status=status,
                    human_status=await self._translate_device_status(dev_type, status),
                    type=dev_type,
                    val=reply_json["val"][i],
                    protected=reply_json["protected"][i],
                    zone=(
                        reply_json["env_desc"][reply_json["env"][i]]
                        if dev_type != SCENARIO
                        else ""
                    ),
                    power=power,
                )
                devices.update({i: dev_info})
            self._devices.update({dev_type: devices})

        self._initialized = True
        return self._devices

    async def vedo_enabled(self, vedo_pin: int) -> bool:
        """Check if Serial bridge has VEDO alarm feature."""
        payload = {"alm": vedo_pin}
        try:
            await self._login(payload, VEDO)
            await self._get_page_result(f"/user/{self._vedo_url_suffix}area_desc.json")
        except (CannotAuthenticate, CannotRetrieveData):
            return False

        return True


class ComelitVedoApi(ComelitCommonApi):
    """Queries Comelit SimpleHome VEDO alarm."""

    _vedo_url_suffix: str = ""
    _vedo_url_action: str = "/action.cgi?vedo=1&"
    _host_type = VEDO

    async def login(self) -> bool:
        """Login to VEDO system."""
        payload = {"code": self.device_pin}
        return await self._login(payload, VEDO)
