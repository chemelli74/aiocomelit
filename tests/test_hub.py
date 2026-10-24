# Copyright 2023 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""Tests for Comelit Hub (MQTT) API."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Self

import aiomqtt
import orjson
import pytest

from aiocomelit.const import CLIMATE, COVER, IRRIGATION, LIGHT, OTHER, SCENARIO
from aiocomelit.devices.hub import ComelitHubApi
from aiocomelit.exceptions import (
    CannotAuthenticate,
    CannotConnect,
    CannotRetrieveData,
)
from tests.conftest import call_private_async, get_private_attr

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable


class _Disconnect:
    """Sentinel signaling a simulated broker disconnect."""


_DISCONNECT = _Disconnect()


class FakeMessage:
    """Fake aiomqtt.Message."""

    def __init__(self, data: dict[str, Any] | None = None, raw: bytes = b"") -> None:
        """Encode a payload dict (or raw bytes) as it would arrive over MQTT."""
        self.payload = orjson.dumps(data) if data is not None else raw


class FakeMqttClient:
    """Fake aiomqtt.Client simulating a Comelit Hub MQTT broker."""

    def __init__(self, **kwargs: object) -> None:
        """Record connection kwargs and set up in-memory queues."""
        self.kwargs = kwargs
        self.fail_connect = False
        self.fail_publish = False
        self.auto_respond = True
        self.status_elements: list[dict[str, Any]] = []
        self.published: list[tuple[str, dict[str, Any]]] = []
        self.subscribed: list[str] = []
        self.exited = False
        self._queue: asyncio.Queue[FakeMessage | _Disconnect] = asyncio.Queue()

    async def __aenter__(self) -> Self:
        """Simulate connecting to the broker."""
        if self.fail_connect:
            raise aiomqtt.MqttError("Connection refused")
        return self

    async def __aexit__(self, *_exc: object) -> None:
        """Simulate disconnecting from the broker."""
        self.exited = True

    async def subscribe(self, topic: str, *_args: object, **_kwargs: object) -> None:
        """Record a subscription."""
        self.subscribed.append(topic)

    async def publish(
        self, topic: str, payload: bytes, *_args: object, **_kwargs: object
    ) -> None:
        """Record a publish and simulate the Hub's reply."""
        if self.fail_publish:
            raise aiomqtt.MqttError("Publish failed")

        data: dict[str, Any] = orjson.loads(payload)
        self.published.append((topic, data))
        if not self.auto_respond:
            return

        req_type = data.get("req_type")
        if req_type == 13:  # ANNOUNCE
            await self._queue.put(
                FakeMessage({"req_type": 13, "out_data": [{"agent_id": 42}]})
            )
        elif req_type == 5:  # LOGIN
            await self._queue.put(
                FakeMessage({"req_type": 5, "sessiontoken": "test-token"})
            )
        elif req_type == 0:  # STATUS
            await self._queue.put(
                FakeMessage(
                    {"req_type": 0, "out_data": [{"elements": self.status_elements}]}
                )
            )

    async def simulate_disconnect(self) -> None:
        """Simulate the broker connection dropping."""
        await self._queue.put(_DISCONNECT)

    async def push_raw(self, payload: bytes) -> None:
        """Push a raw (possibly malformed) message onto the queue."""
        await self._queue.put(FakeMessage(raw=payload))

    @property
    def messages(self) -> AsyncIterator[FakeMessage]:
        """Return the fake message async iterator."""
        return self._message_iter()

    async def _message_iter(self) -> AsyncIterator[FakeMessage]:
        while True:
            item = await self._queue.get()
            if isinstance(item, _Disconnect):
                raise aiomqtt.MqttError("Disconnected")
            yield item


@pytest.fixture
def mqtt_clients(monkeypatch: pytest.MonkeyPatch) -> list[FakeMqttClient]:
    """Patch aiomqtt.Client, recording every fake instance created."""
    created: list[FakeMqttClient] = []

    def _factory(**kwargs: object) -> FakeMqttClient:
        client = FakeMqttClient(**kwargs)
        created.append(client)
        return client

    monkeypatch.setattr("aiocomelit.devices.hub.aiomqtt.Client", _factory)
    return created


def _make_api() -> ComelitHubApi:
    return ComelitHubApi(
        host="127.0.0.1",
        mqtt_port=1883,
        hub_serial="SERIAL123",
        mqtt_user="mqttuser",
        mqtt_password="mqttpass",  # noqa: S106
        hub_user="hubuser",
        hub_password="hubpass",  # noqa: S106
    )


async def test_login_success(mqtt_clients: list[FakeMqttClient]) -> None:
    """Test a successful login connects, announces and stores the token."""
    api = _make_api()

    assert await api.login() is True
    client = mqtt_clients[0]
    assert client.subscribed == ["HSrv/SERIAL123/tx/aiocomelit"]
    req_types = [data["req_type"] for _topic, data in client.published]
    assert req_types == [13, 5]
    assert get_private_attr(api, "_session_token") == "test-token"


async def test_login_is_idempotent(mqtt_clients: list[FakeMqttClient]) -> None:
    """Test a second login call does not reconnect while already logged in."""
    api = _make_api()

    assert await api.login() is True
    assert await api.login() is True
    assert len(mqtt_clients) == 1


async def test_login_connect_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a broker connection failure raises CannotConnect."""
    api = _make_api()

    def _factory(**kwargs: object) -> FakeMqttClient:
        client = FakeMqttClient(**kwargs)
        client.fail_connect = True
        return client

    monkeypatch.setattr("aiocomelit.devices.hub.aiomqtt.Client", _factory)

    with pytest.raises(CannotConnect):
        await api.login()


async def test_login_timeout_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test login raises CannotAuthenticate if no token ever arrives."""
    monkeypatch.setattr("aiocomelit.devices.hub.HUB_REQUEST_TIMEOUT", 0.05)
    api = _make_api()

    def _factory(**kwargs: object) -> FakeMqttClient:
        client = FakeMqttClient(**kwargs)
        client.auto_respond = False
        return client

    monkeypatch.setattr("aiocomelit.devices.hub.aiomqtt.Client", _factory)

    with pytest.raises(CannotAuthenticate):
        await api.login()


async def test_get_all_devices(
    mqtt_clients: list[FakeMqttClient],
    fixture_loader: Callable[[str], dict[str, Any]],
) -> None:
    """Test get_all_devices builds every device type from the element tree."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].status_elements = fixture_loader("hub/status_elements")["elements"]

    devices = await api.get_all_devices()

    assert set(devices) == {CLIMATE, COVER, LIGHT, IRRIGATION, OTHER, SCENARIO}
    assert devices[IRRIGATION] == {}

    light = devices[LIGHT][0]
    assert light.name == "Living Room Light"
    assert light.status == 1
    assert light.human_status == "on"
    assert light.type == LIGHT

    cover = devices[COVER][0]
    assert cover.status == 1
    assert cover.human_status == "opening"

    other = devices[OTHER][0]
    assert other.name == "Garage Socket"
    assert other.status == 1

    scenario = devices[SCENARIO][0]
    assert scenario.name == "Good Night Scene"

    clima = devices[CLIMATE][0]
    assert clima.status == 1
    assert clima.val == [
        [227, 1, "U", "M", 220, 0, 0, "B"],
        [0, 0, "O", "A", 0, 0, 0, "N"],
        [0, 0],
    ]


async def test_get_all_devices_timeout(
    mqtt_clients: list[FakeMqttClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test get_all_devices raises CannotRetrieveData if no status arrives."""
    monkeypatch.setattr("aiocomelit.devices.hub.HUB_REQUEST_TIMEOUT", 0.05)
    api = _make_api()
    await api.login()
    mqtt_clients[0].auto_respond = False

    with pytest.raises(CannotRetrieveData):
        await api.get_all_devices()


@pytest.mark.parametrize(
    ("device_type", "expected_obj_id"),
    [
        (LIGHT, "DOM#LT#1#1"),
        (COVER, "DOM#BL#1#2"),
        (OTHER, "DOM#LD#1#4"),
    ],
    ids=["light", "cover", "other"],
)
async def test_set_device_status_on_off(
    mqtt_clients: list[FakeMqttClient],
    fixture_loader: Callable[[str], dict[str, Any]],
    device_type: str,
    expected_obj_id: str,
) -> None:
    """Test set_device_status publishes the expected on/off action."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].status_elements = fixture_loader("hub/status_elements")["elements"]
    await api.get_all_devices()
    mqtt_clients[0].published.clear()

    assert await api.set_device_status(device_type, 0, 1) is True

    _topic, data = mqtt_clients[0].published[-1]
    assert data["obj_id"] == expected_obj_id
    assert data["act_type"] == 0
    assert data["act_params"] == [1]


async def test_set_device_status_scenario(
    mqtt_clients: list[FakeMqttClient],
    fixture_loader: Callable[[str], dict[str, Any]],
) -> None:
    """Test set_device_status activates a scenario regardless of action."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].status_elements = fixture_loader("hub/status_elements")["elements"]
    await api.get_all_devices()
    mqtt_clients[0].published.clear()

    assert await api.set_device_status(SCENARIO, 0, 0) is True

    _topic, data = mqtt_clients[0].published[-1]
    assert data["obj_id"] == "GEN#SC#1#5"
    assert data["act_type"] == 1000
    assert data["act_params"] == []


async def test_set_device_status_irrigation_is_noop(
    mqtt_clients: list[FakeMqttClient],
) -> None:
    """Test set_device_status no-ops for the unsupported IRRIGATION type."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].published.clear()

    assert await api.set_device_status(IRRIGATION, 0, 1) is True
    assert mqtt_clients[0].published == []


@pytest.mark.parametrize(
    ("action", "expected_act_type", "expected_act_params"),
    [
        ("upper", 4, [1]),
        ("lower", 4, [0]),
        ("off", 0, [0]),
    ],
)
async def test_set_clima_status_state(
    mqtt_clients: list[FakeMqttClient],
    fixture_loader: Callable[[str], dict[str, Any]],
    action: str,
    expected_act_type: int,
    expected_act_params: list[int],
) -> None:
    """Test set_clima_status maps HVAC actions to the right act_type/params."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].status_elements = fixture_loader("hub/status_elements")["elements"]
    await api.get_all_devices()
    mqtt_clients[0].published.clear()

    assert await api.set_clima_status(0, action) is True

    _topic, data = mqtt_clients[0].published[-1]
    assert data["obj_id"] == "DOM#CL#1#3"
    assert data["act_type"] == expected_act_type
    assert data["act_params"] == expected_act_params


async def test_set_clima_status_set_temperature(
    mqtt_clients: list[FakeMqttClient],
    fixture_loader: Callable[[str], dict[str, Any]],
) -> None:
    """Test set_clima_status "set" scales the target temperature by 10."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].status_elements = fixture_loader("hub/status_elements")["elements"]
    await api.get_all_devices()
    mqtt_clients[0].published.clear()

    assert await api.set_clima_status(0, "set", 21.5) is True

    _topic, data = mqtt_clients[0].published[-1]
    assert data["act_type"] == 2
    assert data["act_params"] == [215]


@pytest.mark.parametrize("action", ["auto", "man", "on"])
async def test_set_clima_status_unsupported_actions_are_noop(
    mqtt_clients: list[FakeMqttClient],
    fixture_loader: Callable[[str], dict[str, Any]],
    action: str,
) -> None:
    """Test auto/manual/on clima actions no-op (unsupported by the Hub)."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].status_elements = fixture_loader("hub/status_elements")["elements"]
    await api.get_all_devices()
    mqtt_clients[0].published.clear()

    assert await api.set_clima_status(0, action) is True
    assert mqtt_clients[0].published == []


async def test_set_humidity_status_is_always_noop(
    mqtt_clients: list[FakeMqttClient],
) -> None:
    """Test set_humidity_status always no-ops (unsupported by the Hub)."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].published.clear()

    assert await api.set_humidity_status(0, "set", 45) is True
    assert mqtt_clients[0].published == []


async def test_get_device_status(
    mqtt_clients: list[FakeMqttClient],
    fixture_loader: Callable[[str], dict[str, Any]],
) -> None:
    """Test get_device_status reads from the last cached snapshot."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].status_elements = fixture_loader("hub/status_elements")["elements"]
    await api.get_all_devices()

    assert await api.get_device_status(LIGHT, 0) == 1

    with pytest.raises(CannotRetrieveData):
        await api.get_device_status(LIGHT, 99)


async def test_logout_disconnects(mqtt_clients: list[FakeMqttClient]) -> None:
    """Test logout cancels the listener task and exits the MQTT client."""
    api = _make_api()
    await api.login()
    client = mqtt_clients[0]

    await api.logout()

    assert client.exited is True
    assert get_private_attr(api, "_client") is None
    assert get_private_attr(api, "_session_token") == ""


async def test_relogin_after_disconnect(mqtt_clients: list[FakeMqttClient]) -> None:
    """Test a dropped connection is transparently reconnected on next login."""
    api = _make_api()
    await api.login()
    first_client = mqtt_clients[0]

    await first_client.simulate_disconnect()
    listener_task = get_private_attr(api, "_listener_task")
    assert isinstance(listener_task, asyncio.Task)
    await asyncio.wait_for(listener_task, timeout=1)
    assert get_private_attr(api, "_session_token") == ""

    assert await api.login() is True
    assert len(mqtt_clients) == 2
    assert mqtt_clients[1] is not first_client


async def test_publish_without_connection_raises() -> None:
    """Test _publish raises CannotConnect when not connected."""
    api = _make_api()
    publish: Callable[..., Any] = call_private_async(api, "_publish")

    with pytest.raises(CannotConnect):
        await publish({"req_type": 0})


async def test_publish_mqtt_error_raises_cannot_connect(
    mqtt_clients: list[FakeMqttClient],
) -> None:
    """Test a broker publish failure raises CannotConnect."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].fail_publish = True

    with pytest.raises(CannotConnect):
        await api.get_all_devices()


async def test_message_loop_without_client_returns() -> None:
    """Test _message_loop returns immediately if never connected."""
    api = _make_api()
    message_loop: Callable[..., Any] = call_private_async(api, "_message_loop")

    await message_loop()


async def test_message_loop_ignores_invalid_json(
    mqtt_clients: list[FakeMqttClient],
) -> None:
    """Test a malformed payload is logged and skipped, not fatal."""
    api = _make_api()
    await api.login()
    client = mqtt_clients[0]

    await client.push_raw(b"not json")
    client.status_elements = []
    devices = await api.get_all_devices()

    assert devices[LIGHT] == {}


async def test_set_device_status_unknown_index_raises(
    mqtt_clients: list[FakeMqttClient],
    fixture_loader: Callable[[str], dict[str, Any]],
) -> None:
    """Test set_device_status raises for an index that was never seen."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].status_elements = fixture_loader("hub/status_elements")["elements"]
    await api.get_all_devices()

    with pytest.raises(CannotRetrieveData):
        await api.set_device_status(LIGHT, 99, 1)


async def test_get_all_devices_handles_nested_groups_and_odd_status(
    mqtt_clients: list[FakeMqttClient],
    fixture_loader: Callable[[str], dict[str, Any]],
) -> None:
    """Test nested logical groups recurse and out-of-range status normalizes."""
    api = _make_api()
    await api.login()
    mqtt_clients[0].status_elements = fixture_loader("hub/status_elements_nested")[
        "elements"
    ]

    devices = await api.get_all_devices()

    assert devices[LIGHT][0].name == "Nested Light"
    assert devices[COVER][0].status == 0
    assert devices[COVER][0].human_status == "stopped"
