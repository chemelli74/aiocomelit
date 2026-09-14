# Copyright 2023 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""Support for Comelit SimpleHome."""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from typing import Any, cast

import orjson
from aiohttp import ClientConnectorError, ClientSession, ContentTypeError
from yarl import URL

from .const import (
    _LOGGER,
    ALARM_AREA,
    ALARM_AREA_STATUS,
    ALARM_ZONE,
    ALARM_ZONE_STATUS,
    BRIDGE,
    DEFAULT_TIMEOUT,
    SLEEP_AFTER_VEDO_LOGIN,
    SLEEP_BETWEEN_VEDO_CALLS,
    VEDO,
    WATT,
    AlarmAreaState,
    AlarmZoneState,
)
from .exceptions import (
    CannotAuthenticate,
    CannotConnect,
    CannotRetrieveData,
    DeviceStorageFailureError,
)


@dataclass
class ComelitDeviceObject:
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


class ComelitCommonApi(ABC):
    """Common interface for Comelit SimpleHome devices, regardless of transport."""

    @abstractmethod
    async def login(self) -> bool:
        """Login to Comelit device."""

    @abstractmethod
    async def logout(self) -> None:
        """Logout from Comelit device."""


class ComelitHttpApi(ComelitCommonApi):
    """Common HTTP API calls for Comelit SimpleHome devices."""

    _vedo_url_suffix: str
    _vedo_url_action: str
    _host_type: str

    def __init__(self, host: str, port: int, pin: str, session: ClientSession) -> None:
        """Initialize the session."""
        self.device_pin = pin
        self.base_url = URL.build(scheme="http", host=host, port=port)
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
        self._is_new_firmware: bool = False

    async def _get_page_result(
        self,
        page: str,
        query: dict[str, Any] | None = None,
        reply_json: bool = True,
        ignore_missing: bool = False,
    ) -> tuple[int, dict[str, Any]]:
        """Return status and data from a GET query."""
        url = URL.joinpath(self.base_url, page)
        url = URL.extend_query(url, query)
        url = URL.extend_query(url, {"_": int(datetime.now(tz=UTC).timestamp() * 1000)})
        _LOGGER.debug("[%s] GET page %s", self._logging, url)
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

        if response.status == HTTPStatus.NOT_FOUND and ignore_missing:
            return response.status, {"page": await response.text()}

        if response.status != HTTPStatus.OK:
            raise CannotRetrieveData(f"GET response status {response.status}")

        if not reply_json:
            _LOGGER.debug("[%s] GET response is empty", self._logging)
            return response.status, {}

        try:
            json_data = await response.json(loads=orjson.loads)
        except (orjson.JSONDecodeError, ContentTypeError) as exc:
            raise DeviceStorageFailureError("Error parsing JSON response") from exc

        return response.status, json_data

    async def _post_page_result(
        self,
        page: str,
        payload: dict[str, Any],
        ignore_missing: bool = False,
    ) -> tuple[int, SimpleCookie]:
        """Return status and cookies from a POST query."""
        url = URL.joinpath(self.base_url, page)
        _LOGGER.debug("[%s] POST page %s with payload %s", self._logging, url, payload)
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

        if response.status == HTTPStatus.NOT_FOUND and ignore_missing:
            return response.status, SimpleCookie()

        if response.status != HTTPStatus.OK:
            raise CannotRetrieveData(f"POST response status {response.status}")

        return response.status, cast("SimpleCookie", response.cookies)

    async def _is_session_active(self) -> bool:
        """Check if aiohttp session is still active."""
        return hasattr(self, "_session") and not self._session.closed

    async def _check_logged_in(self, host_type: str) -> bool:
        """Check if login is active."""
        logged: bool
        if host_type == BRIDGE:
            _, reply_json = await self._get_page_result("login.json")
            _LOGGER.debug("[%s] Login reply: %s", self._logging, reply_json)
            logged = reply_json["domus"] != "000000000000"
        else:
            # For VEDO system with newer firmware, login.json is reporting logged=0
            # even if the session is active, so we check the area_stat.json instead
            _, reply_json = await self._get_page_result(
                f"user/{self._vedo_url_suffix}area_stat.json"
            )
            _LOGGER.debug("[%s] Login reply: %s", self._logging, reply_json)
            logged = reply_json["logged"] == 1

        return logged

    async def _sleep_between_call(self, seconds: float) -> None:
        """Sleep between one call and the next one."""
        _LOGGER.debug(
            "[%s] Sleeping for %s seconds before next call", self._logging, seconds
        )
        await asyncio.sleep(seconds)

    async def _check_new_firmware(self) -> bool:
        """Check if VEDO system is running a new firmware."""
        _, reply_data = await self._get_page_result(
            page=f"{self._vedo_url_suffix}index.shtml",
            ignore_missing=True,
        )
        _LOGGER.debug("[%s] Firmware check reply: %s", self._logging, reply_data)
        status = bool("www.comelitgroup.com" in reply_data.get("page", ""))
        _LOGGER.debug("[%s] New firmware: %s", self._logging, status)
        return status

    async def _login(self, payload: dict[str, Any], host_type: str) -> bool:
        """Login into Comelit device."""
        _LOGGER.debug("[%s] Logging in", self._logging)

        if await self._check_logged_in(host_type):
            return True

        _, cookies = await self._post_page_result("login.cgi", payload)
        _LOGGER.debug("[%s] Cookies: %s", self._logging, cookies)

        if host_type == VEDO:
            _LOGGER.debug("[%s] Waiting for login to complete", self._logging)
            await self._sleep_between_call(SLEEP_AFTER_VEDO_LOGIN)

            self._is_new_firmware = await self._check_new_firmware()

        if not cookies:
            _LOGGER.warning(
                "[%s] Authentication failed: no cookies received", self._logging
            )
            raise CannotAuthenticate

        self._session.cookie_jar.update_cookies(cookies, self.base_url)

        return await self._check_logged_in(host_type)

    async def logout(self) -> None:
        """Comelit Simple Home logout."""
        if await self._is_session_active():
            payload = {"logout": 1}
            await self._post_page_result("login.cgi", payload)
            self._session.cookie_jar.clear()

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
        _, reply_json = await self._get_page_result(page=page)
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
        if self._is_new_firmware:
            # New firmware uses HTTP POST requests with payload parameters.
            # The device always returns HTTP 404, even when the action succeeds.
            reply_status, _ = await self._post_page_result(
                page=self._vedo_url_action,
                payload={
                    "forced": int(force),
                    "vedo_param": 1,
                    "type_param": action,
                    "area_param": index,
                },
                ignore_missing=True,
            )
            return reply_status in (HTTPStatus.OK, HTTPStatus.NOT_FOUND)

        # Previous firmware uses HTTP GET requests with query parameters
        reply_status, _ = await self._get_page_result(
            page=self._vedo_url_action,
            query={
                "vedo": 1,
                action: index,
                "force": int(force),
            },
            reply_json=False,
        )
        return reply_status == HTTPStatus.OK

    async def get_area_status(
        self,
        area: ComelitVedoAreaObject,
    ) -> ComelitVedoAreaObject:
        """Get AREA status."""
        _, reply_json_area_stat = await self._async_get_page_data(
            desc="AREA statistics",
            page=f"user/{self._vedo_url_suffix}area_stat.json",
        )
        description = {
            "description": [area.name],
            "p1_pres": [area.p1],
            "p2_pres": [area.p2],
        }

        return await self._create_area_object(
            description,
            reply_json_area_stat,
            area.index,
        )

    async def get_all_areas_and_zones(
        self,
    ) -> dict[str, Mapping[int, ComelitVedoAreaObject | ComelitVedoZoneObject]]:
        """Get all VEDO system AREA and ZONE."""
        queries: dict[int, dict[str, Any]] = {
            1: {
                "desc": "AREA description",
                "page": f"user/{self._vedo_url_suffix}area_desc.json",
                "present": 1,
            },
            2: {
                "desc": "ZONE description",
                "page": f"user/{self._vedo_url_suffix}zone_desc.json",
                "present": "1",
            },
            3: {
                "desc": "AREA statistics",
                "page": f"user/{self._vedo_url_suffix}area_stat.json",
                "present": None,
            },
            4: {
                "desc": "ZONE statistics",
                "page": f"user/{self._vedo_url_suffix}zone_stat.json",
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

        return {
            ALARM_AREA: areas,
            ALARM_ZONE: zones,
        }
