# Copyright 2023 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""Support for the Comelit SimpleHome Serial bridge."""

import asyncio
import functools
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any, cast

import pint
from aiohttp import ClientSession

from aiocomelit.api import ComelitDeviceObject, ComelitHttpApi
from aiocomelit.const import (
    _LOGGER,
    BRIDGE,
    CLIMATE,
    COVER,
    IRRIGATION,
    LIGHT,
    OTHER,
    SCENARIO,
    SLEEP_BETWEEN_BRIDGE_CALLS,
    STATE_COVER,
    STATE_ON,
    VEDO,
    WATT,
)
from aiocomelit.exceptions import (
    CannotAuthenticate,
    CannotRetrieveData,
    DeviceStorageFailureError,
)


class ComeliteSerialBridgeApi(ComelitHttpApi):
    """Queries Comelit SimpleHome Serial bridge."""

    _vedo_url_suffix: str = "vedo_"
    _vedo_url_action: str = "user/action.cgi"
    _host_type = BRIDGE

    def __init__(
        self, host: str, port: int, bridge_pin: str, session: ClientSession
    ) -> None:
        """Initialize the session."""
        super().__init__(host, port, bridge_pin, session)
        self._devices: dict[str, dict[int, ComelitDeviceObject]] = {}
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
        async with self._semaphore:
            if self._last_clima_command:
                delta_seconds = SLEEP_BETWEEN_BRIDGE_CALLS - round(
                    (datetime.now(tz=UTC) - self._last_clima_command).total_seconds(),
                    2,
                )
                if delta_seconds > 0:
                    _LOGGER.debug(
                        "[%s] Climate calls needs to be queued (%ss) for proper"
                        " execution",
                        self._logging,
                        delta_seconds,
                    )
                    await self._sleep_between_call(delta_seconds)

            try:
                reply_status, _ = await self._get_page_result(
                    page="user/action.cgi",
                    query={
                        "clima": index,
                        mode: action,
                        "val": int(value * 10),
                    },
                    reply_json=False,
                )
            finally:
                self._last_clima_command = datetime.now(tz=UTC)
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
        reply_status, _ = await self._get_page_result(
            page="user/action.cgi",
            query={
                "type": device_type,
                f"num{action}": index,
            },
            reply_json=False,
        )
        return reply_status == HTTPStatus.OK

    async def get_device_status(self, device_type: str, index: int) -> int:
        """Get device status."""
        _, reply_json = await self._get_page_result(
            page="user/icon_status.json",
            query={"type": device_type},
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

    async def get_all_devices(self) -> dict[str, dict[int, ComelitDeviceObject]]:
        """Get all connected devices."""
        _LOGGER.debug("[%s] Getting all devices", self._logging)

        loop = asyncio.get_running_loop()
        ureg = await loop.run_in_executor(
            None,
            functools.partial(pint.UnitRegistry, cache_folder=":auto:"),
        )
        ureg.formatter.default_format = "~"

        for dev_type in (CLIMATE, COVER, LIGHT, IRRIGATION, OTHER, SCENARIO):
            _, reply_json = await self._get_page_result(
                page="user/icon_desc.json",
                query={"type": dev_type},
            )
            _LOGGER.debug(
                "[%s] List of devices of type %s: %s",
                self._logging,
                dev_type,
                reply_json,
            )
            if not reply_json:
                raise DeviceStorageFailureError(
                    f"No data received for device type {dev_type}"
                )

            reply_counter_json: dict[str, Any] = {}
            num_devices = reply_json["num"]
            if dev_type == OTHER and num_devices > 0:
                _, reply_counter_json = await self._get_page_result(
                    page="user/counter.json",
                )
            devices: dict[int, ComelitDeviceObject] = {}
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
                dev_info = ComelitDeviceObject(
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

    async def vedo_enabled(self, vedo_pin: str) -> bool:
        """Check if Serial bridge has VEDO alarm feature."""
        payload = {"alm": vedo_pin}
        try:
            if vedo_pin != self.device_pin:
                await self._login(payload, VEDO)
            await self._get_page_result(
                page=f"user/{self._vedo_url_suffix}area_desc.json"
            )
        except (CannotAuthenticate, CannotRetrieveData):
            return False

        return True
