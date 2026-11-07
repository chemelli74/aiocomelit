# Copyright 2023 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""Support for Comelit Hub (MQTT)."""

import asyncio
import contextlib
from typing import Any, cast

import aiomqtt
import orjson

from aiocomelit.api import ComelitCommonApi, ComelitDeviceObject
from aiocomelit.const import (
    _LOGGER,
    CLIMATE,
    COVER,
    DEFAULT_HUB_MQTT_PASSWORD,
    DEFAULT_HUB_MQTT_USER,
    HUB,
    HUB_REQUEST_TIMEOUT,
    HUB_STATUS_OBJ_ID,
    HUB_TOPIC_PREFIX,
    IRRIGATION,
    LIGHT,
    OTHER,
    SCENARIO,
    STATE_COVER,
    STATE_OFF,
    STATE_ON,
    HubElementClass,
    HubRequestType,
)
from aiocomelit.exceptions import CannotAuthenticate, CannotConnect, CannotRetrieveData

_DEVICE_TYPES = (CLIMATE, COVER, LIGHT, IRRIGATION, OTHER, SCENARIO)


class ComelitHubApi(ComelitCommonApi):
    """Queries a Comelit Hub over MQTT."""

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        host: str,
        mqtt_port: int,
        hub_serial: str,
        hub_user: str,
        hub_password: str,
        mqtt_user: str = DEFAULT_HUB_MQTT_USER,
        mqtt_password: str = DEFAULT_HUB_MQTT_PASSWORD,
        client_id: str = "aiocomelit",
    ) -> None:
        """Initialize the Hub client."""
        self._host = host
        self._mqtt_port = mqtt_port
        self._hub_serial = hub_serial
        self._mqtt_user = mqtt_user
        self._mqtt_password = mqtt_password
        self._hub_user = hub_user
        self._hub_password = hub_password
        self._client_id = client_id
        self._logging = f"{HUB} ({host}:{mqtt_port})"
        self._topic_tx = f"{HUB_TOPIC_PREFIX}/{hub_serial}/tx/{client_id}"
        self._topic_rx = f"{HUB_TOPIC_PREFIX}/{hub_serial}/rx/{client_id}"

        self._client: aiomqtt.Client | None = None
        self._listener_task: asyncio.Task[None] | None = None
        self._sequence_id = 1
        self._agent_id = 10
        self._session_token = ""
        self._login_event = asyncio.Event()
        self._status_event = asyncio.Event()
        self._devices: dict[str, dict[int, ComelitDeviceObject]] = {
            dev_type: {} for dev_type in _DEVICE_TYPES
        }
        self._element_index: dict[str, dict[str, int]] = {
            dev_type: {} for dev_type in _DEVICE_TYPES if dev_type != IRRIGATION
        }

    async def _publish(self, data: dict[str, Any]) -> None:
        """Publish a request to the Hub."""
        if self._client is None:
            raise CannotConnect("Not connected to Hub")

        payload = {
            **data,
            "seq_id": self._sequence_id,
            "agent_id": self._agent_id,
            "sessiontoken": self._session_token,
        }
        _LOGGER.debug("[%s] Publishing %s", self._logging, payload)
        try:
            await self._client.publish(self._topic_rx, orjson.dumps(payload))
        except aiomqtt.MqttError as exc:
            raise CannotConnect("Error publishing to Hub") from exc
        self._sequence_id += 1

    async def _message_loop(self) -> None:
        """Consume incoming Hub messages until the connection drops."""
        client = self._client
        if client is None:
            return

        try:
            async for message in client.messages:
                try:
                    payload = cast("dict[str, Any]", orjson.loads(message.payload))
                except orjson.JSONDecodeError:
                    _LOGGER.warning("[%s] Invalid JSON payload received", self._logging)
                    continue
                await self._dispatch(payload)
        except aiomqtt.MqttError:
            _LOGGER.warning("[%s] Disconnected from Hub", self._logging)
        finally:
            self._session_token = ""
            self._login_event.clear()

    async def _dispatch(self, payload: dict[str, Any]) -> None:
        """Route an incoming Hub message to the matching handler."""
        req_type = payload.get("req_type")

        if req_type == HubRequestType.ANNOUNCE:
            out_data = payload.get("out_data") or [{}]
            self._agent_id = out_data[0].get("agent_id", self._agent_id)
            await self._publish(
                {
                    "req_type": HubRequestType.LOGIN,
                    "req_sub_type": -1,
                    "agent_type": 0,
                    "user_name": self._hub_user,
                    "password": self._hub_password,
                }
            )
        elif req_type == HubRequestType.LOGIN:
            token = payload.get("sessiontoken", "")
            if token:
                self._session_token = token
                self._login_event.set()
        elif req_type == HubRequestType.STATUS:
            out_data = payload.get("out_data") or [{}]
            elements = out_data[0].get("elements", [])
            self._devices = {dev_type: {} for dev_type in _DEVICE_TYPES}
            self._update_devices(elements)
            self._status_event.set()

    def _get_index(self, device_type: str, element_id: str) -> int:
        """Return the stable integer index assigned to a Hub element id."""
        mapping = self._element_index[device_type]
        if element_id not in mapping:
            mapping[element_id] = len(mapping)
        return mapping[element_id]

    def _id_for_index(self, device_type: str, index: int) -> str:
        """Return the Hub element id assigned to an integer index."""
        for element_id, idx in self._element_index[device_type].items():
            if idx == index:
                return element_id
        raise CannotRetrieveData(f"Unknown {device_type} device index {index}")

    def _update_devices(self, elements: list[dict[str, Any]]) -> None:
        """Walk the Hub's logical element tree, populating self._devices."""
        for item in elements:
            entity_id = item["id"]

            if HubElementClass.LOGICAL in entity_id:
                for logical_element in item["data"]["elements"]:
                    logical_data = logical_element["data"]
                    if HubElementClass.LOGICAL in logical_data["id"]:
                        self._update_devices(logical_data["elements"])
                    else:
                        self._update_devices([logical_data])
                continue

            data = item.get("data", item)

            if HubElementClass.TEMPERATURE in entity_id:
                if data.get("sub_type") in (12, 16):
                    self._update_climate(entity_id, data)
            elif HubElementClass.LIGHT in entity_id:
                self._update_light(entity_id, data)
            elif (
                HubElementClass.COVER in entity_id
                or HubElementClass.AUTOMATION in entity_id
            ):
                self._update_cover(entity_id, data)
            elif HubElementClass.SCENARIO in entity_id:
                self._update_scenario(entity_id, data)
            elif HubElementClass.OTHER in entity_id:
                self._update_switch(entity_id, data)

    def _update_light(self, element_id: str, data: dict[str, Any]) -> None:
        """Add or update a light device."""
        index = self._get_index(LIGHT, element_id)
        status = int(data.get("status", STATE_OFF))
        self._devices[LIGHT][index] = ComelitDeviceObject(
            index=index,
            name=data.get("descrizione", ""),
            status=status,
            human_status="on" if status == STATE_ON else "off",
            type=LIGHT,
            val=0,
            protected=0,
            zone="",
            power=0.0,
        )

    def _update_cover(self, element_id: str, data: dict[str, Any]) -> None:
        """Add or update a cover (or Hub 'automation') device."""
        index = self._get_index(COVER, element_id)
        status = int(data.get("status", 0))
        if status not in (0, 1, 2):
            status = 0
        self._devices[COVER][index] = ComelitDeviceObject(
            index=index,
            name=data.get("descrizione", ""),
            status=status,
            human_status=STATE_COVER[status],
            type=COVER,
            val=0,
            protected=0,
            zone="",
            power=0.0,
        )

    def _update_switch(self, element_id: str, data: dict[str, Any]) -> None:
        """Add or update a switch device."""
        index = self._get_index(OTHER, element_id)
        status = int(data.get("status", STATE_OFF))
        self._devices[OTHER][index] = ComelitDeviceObject(
            index=index,
            name=data.get("descrizione", ""),
            status=status,
            human_status="on" if status == STATE_ON else "off",
            type=OTHER,
            val=0,
            protected=0,
            zone="",
            power=0.0,
        )

    def _update_climate(self, element_id: str, data: dict[str, Any]) -> None:
        """Add or update a climate device."""
        index = self._get_index(CLIMATE, element_id)
        active = bool(int(data.get("status", 0)))
        is_winter = bool(int(data.get("est_inv", 0)))
        mode_char = "O" if not active else ("U" if is_winter else "L")
        raw_temp = data.get("temperatura")
        raw_target = data.get("soglia_attiva")

        # Auto/manual preset switching isn't supported by the Hub protocol
        # (see set_clima_status), so always report "manual" here too.
        clima_val = [
            round(float(raw_temp)) if raw_temp is not None else 0,
            int(active),
            mode_char,
            "M",
            round(float(raw_target)) if raw_target is not None else 0,
            0,
            0,
            "B",
        ]
        humi_val = [0, 0, "O", "A", 0, 0, 0, "N"]

        self._devices[CLIMATE][index] = ComelitDeviceObject(
            index=index,
            name=data.get("descrizione", ""),
            status=int(active),
            human_status="on" if active else "off",
            type=CLIMATE,
            val=[clima_val, humi_val, [0, 0]],
            protected=0,
            zone="",
            power=0.0,
        )

    def _update_scenario(self, element_id: str, data: dict[str, Any]) -> None:
        """Add or update a scenario."""
        index = self._get_index(SCENARIO, element_id)
        self._devices[SCENARIO][index] = ComelitDeviceObject(
            index=index,
            name=data.get("descrizione", ""),
            status=0,
            human_status="",
            type=SCENARIO,
            val=0,
            protected=0,
            zone="",
            power=0.0,
        )

    async def _disconnect(self) -> None:
        """Tear down the listener task and the MQTT connection."""
        if self._listener_task is not None:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None
        if self._client is not None:
            with contextlib.suppress(aiomqtt.MqttError):
                await self._client.__aexit__(None, None, None)
            self._client = None
        self._session_token = ""
        self._login_event.clear()

    async def login(self) -> bool:
        """Login to the Hub, connecting over MQTT if needed."""
        if self._client is not None and self._session_token:
            return True
        if self._client is not None:
            await self._disconnect()

        _LOGGER.debug("[%s] Logging in", self._logging)
        self._login_event.clear()
        client = aiomqtt.Client(
            hostname=self._host,
            port=self._mqtt_port,
            username=self._mqtt_user,
            password=self._mqtt_password,
            identifier=self._client_id,
        )
        try:
            await client.__aenter__()
            self._client = client
            self._listener_task = asyncio.create_task(self._message_loop())
            await self._client.subscribe(self._topic_tx)
            await self._publish(
                {
                    "req_type": HubRequestType.ANNOUNCE,
                    "req_sub_type": -1,
                    "agent_type": 0,
                }
            )
            await asyncio.wait_for(
                self._login_event.wait(), timeout=HUB_REQUEST_TIMEOUT
            )
        except aiomqtt.MqttError as exc:
            await self._disconnect()
            raise CannotConnect("Error connecting to Hub") from exc
        except TimeoutError as exc:
            await self._disconnect()
            raise CannotAuthenticate("Timed out waiting for Hub login") from exc

        return True

    async def logout(self) -> None:
        """Disconnect from the Hub."""
        await self._disconnect()

    async def get_all_devices(self) -> dict[str, dict[int, ComelitDeviceObject]]:
        """Get all connected devices."""
        await self.login()

        self._status_event.clear()
        await self._publish(
            {
                "req_type": HubRequestType.STATUS,
                "req_sub_type": -1,
                "obj_id": HUB_STATUS_OBJ_ID,
                "detail_level": 1,
            }
        )
        try:
            await asyncio.wait_for(
                self._status_event.wait(), timeout=HUB_REQUEST_TIMEOUT
            )
        except TimeoutError as exc:
            raise CannotRetrieveData("Timed out waiting for Hub status") from exc

        return self._devices

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
        if device_type not in self._element_index:
            _LOGGER.debug(
                "[%s] %s devices are not supported by the Hub protocol, ignoring",
                self._logging,
                device_type,
            )
            return True

        element_id = self._id_for_index(device_type, index)

        if device_type == SCENARIO:
            await self._publish(
                {
                    "req_type": HubRequestType.ACTION,
                    "req_sub_type": 3,
                    "obj_id": element_id,
                    "act_type": 1000,
                    "act_params": [],
                }
            )
            return True

        await self._publish(
            {
                "req_type": HubRequestType.ACTION,
                "req_sub_type": 3,
                "obj_id": element_id,
                "act_type": 0,
                "act_params": [1 if action == STATE_ON else 0],
            }
        )
        return True

    async def get_device_status(self, device_type: str, index: int) -> int:
        """Get device status from the last known Hub status snapshot."""
        try:
            return self._devices[device_type][index].status
        except KeyError as exc:
            raise CannotRetrieveData(
                f"No cached status for {device_type}[{index}]"
            ) from exc

    async def set_clima_status(self, index: int, action: str, temp: float = 0) -> bool:
        """Set clima status."""
        element_id = self._id_for_index(CLIMATE, index)

        if action in ("auto", "man", "on"):
            _LOGGER.debug(
                "[%s] Clima action '%s' is not supported by the Hub protocol, ignoring",
                self._logging,
                action,
            )
            return True

        if action == "set":
            await self._publish(
                {
                    "req_type": HubRequestType.ACTION,
                    "req_sub_type": 3,
                    "obj_id": element_id,
                    "act_type": 2,
                    "act_params": [int(temp * 10)],
                }
            )
            return True

        act_type, act_params = {
            "upper": (4, [1]),
            "lower": (4, [0]),
            "off": (0, [0]),
        }[action]
        await self._publish(
            {
                "req_type": HubRequestType.ACTION,
                "req_sub_type": 3,
                "obj_id": element_id,
                "act_type": act_type,
                "act_params": act_params,
            }
        )
        return True

    async def set_humidity_status(
        self,
        index: int,  # noqa: ARG002
        action: str,  # noqa: ARG002
        humidity: float = 0,  # noqa: ARG002
    ) -> bool:
        """Set humidity status.

        Not supported by the Hub protocol: always a no-op.
        """
        _LOGGER.debug(
            "[%s] Humidity control is not supported by the Hub protocol, ignoring",
            self._logging,
        )
        return True
