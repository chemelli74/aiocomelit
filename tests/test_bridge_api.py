"""Tests for Comelit serial bridge API."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from aiocomelit.api import ComeliteSerialBridgeApi
from aiocomelit.const import BRIDGE, CLIMATE, COVER, LIGHT, OTHER, SCENARIO
from aiocomelit.exceptions import (
    CannotAuthenticate,
    CannotRetrieveData,
    DeviceStorageFailureError,
)
from tests.conftest import call_private_async, set_private_attr, setup_api

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from tests.conftest import MockSession

SCENARIO_COUNT = 3


async def test_bridge_login_delegates_to_common(mock_session: MockSession) -> None:
    """Test bridge login delegates to common internal login."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    login_mock = AsyncMock(return_value=True)
    set_private_attr(api, "_login", login_mock)

    assert await api.login() is True
    login_mock.assert_awaited_once_with({"dom": "1234"}, BRIDGE)


@pytest.mark.parametrize(
    ("dev_type", "status", "expected"),
    [
        (COVER, 0, "stopped"),
        (COVER, 1, "opening"),
        (COVER, 2, "closing"),
        (LIGHT, 1, "on"),
        (LIGHT, 0, "off"),
    ],
)
async def test_translate_device_status(
    mock_session: MockSession,
    dev_type: str,
    status: int,
    expected: str,
) -> None:
    """Test device status translation for cover and non-cover devices."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    method: Callable[[str, int], Awaitable[str]] = call_private_async(
        api, "_translate_device_status"
    )
    assert await method(dev_type, status) == expected


async def test_set_thermo_humi_status_waits_and_scales(
    mock_session: MockSession,
) -> None:
    """Test thermo/humidity helper queueing and value scaling."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    set_private_attr(api, "_last_clima_command", datetime.now(tz=UTC))
    sleep_mock = AsyncMock()
    get_mock = AsyncMock(return_value=(HTTPStatus.OK, {}))
    set_private_attr(api, "_sleep_between_call", sleep_mock)
    set_private_attr(api, "_get_page_result", get_mock)

    result = await api.set_clima_status(3, "set", 22.5)

    assert result is True
    sleep_mock.assert_awaited_once()
    get_mock.assert_awaited_once()
    called_url = get_mock.await_args_list[0].args[0]
    assert "clima=3" in called_url
    assert "thermo=set" in called_url
    assert "val=225" in called_url


async def test_set_clima_and_humidity_wrappers(mock_session: MockSession) -> None:
    """Test climate/humidity wrapper methods delegate correctly."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    thermo_humi_mock = AsyncMock(return_value=True)
    set_private_attr(api, "_set_thermo_humi_status", thermo_humi_mock)

    assert await api.set_clima_status(1, "set", 19.0) is True
    assert await api.set_humidity_status(2, "set", 61.0) is True

    assert thermo_humi_mock.await_args_list[0].args == (1, "thermo", "set", 19.0)
    assert thermo_humi_mock.await_args_list[1].args == (2, "humi", "set", 61.0)


@pytest.mark.parametrize(
    ("action", "expected_fragment", "status_code", "expected_result"),
    [
        (1, "num1=2", HTTPStatus.OK, True),
        (0, "num0=2", HTTPStatus.INTERNAL_SERVER_ERROR, False),
    ],
)
async def test_set_device_status(
    mock_session: MockSession,
    action: int,
    expected_fragment: str,
    status_code: HTTPStatus,
    expected_result: bool,
) -> None:
    """Test set_device_status for on/off actions and response handling."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    get_mock = AsyncMock(return_value=(status_code, {}))
    set_private_attr(api, "_get_page_result", get_mock)

    assert await api.set_device_status(LIGHT, 2, action) is expected_result
    call_args = get_mock.await_args
    assert call_args is not None
    assert expected_fragment in call_args.args[0]


async def test_get_device_status(mock_session: MockSession) -> None:
    """Test reading a single device status index."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    set_private_attr(
        api,
        "_get_page_result",
        AsyncMock(return_value=(HTTPStatus.OK, {"status": [0, 1, 0]})),
    )

    assert await api.get_device_status(LIGHT, 1) == 1


@pytest.mark.parametrize(
    ("counter_payload", "expected_power"),
    [
        ({"instant": ["1 kW"], "logged": 1}, 1000.0),
        ({"logged": 1}, 0.0),
    ],
)
async def test_get_all_devices_with_real_fixtures(
    mock_session: MockSession,
    fixture_loader: Callable[[str], dict[str, object]],
    counter_payload: dict[str, object],
    expected_power: float,
) -> None:
    """Test full device retrieval and power parsing from fixture payloads."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)

    responses: dict[str, dict[str, object]] = {
        "/user/icon_desc.json?type=clima": fixture_loader("bridge/clima"),
        "/user/icon_desc.json?type=shutter": fixture_loader("bridge/shutter"),
        "/user/icon_desc.json?type=light": fixture_loader("bridge/light"),
        "/user/icon_desc.json?type=irrigation": fixture_loader("bridge/irrigation"),
        "/user/icon_desc.json?type=other": fixture_loader("bridge/other"),
        "/user/icon_desc.json?type=scenario": fixture_loader("bridge/scenario"),
        "/user/counter.json": counter_payload,
    }

    async def fake_get(
        path: str, _reply_json: bool = True
    ) -> tuple[int, dict[str, object]]:
        """Return response payloads by request path."""
        for key, value in responses.items():
            if path.startswith(key):
                return HTTPStatus.OK, value
        raise AssertionError(path)

    set_private_attr(api, "_get_page_result", AsyncMock(side_effect=fake_get))
    devices = await api.get_all_devices()

    assert CLIMATE in devices
    assert SCENARIO in devices
    assert len(devices[SCENARIO]) == SCENARIO_COUNT
    assert devices[OTHER][0].power == pytest.approx(expected_power)
    assert bool(object.__getattribute__(api, "_initialized")) is True


async def test_get_all_devices_empty_payload_raises_storage_error(
    mock_session: MockSession,
) -> None:
    """Test empty payload handling while loading all devices."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    set_private_attr(
        api, "_get_page_result", AsyncMock(return_value=(HTTPStatus.OK, {}))
    )

    with pytest.raises(DeviceStorageFailureError):
        await api.get_all_devices()


async def test_get_all_devices_empty_desc_raises_when_not_initialized(
    mock_session: MockSession,
) -> None:
    """Test empty climate descriptions raise when bridge is not initialized."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    set_private_attr(api, "_initialized", False)

    async def fake_get(
        path: str, _reply_json: bool = True
    ) -> tuple[int, dict[str, object]]:
        """Return empty device descriptions for climate."""
        if path.endswith("type=clima"):
            return HTTPStatus.OK, {
                "num": 1,
                "desc": [],
                "status": [0],
                "val": [0],
                "protected": [0],
                "env": [0],
                "env_desc": [""],
            }
        return HTTPStatus.OK, {
            "num": 0,
            "desc": [],
            "status": [],
            "val": [],
            "protected": [],
            "env": [],
            "env_desc": [""],
        }

    set_private_attr(api, "_get_page_result", AsyncMock(side_effect=fake_get))

    with pytest.raises(CannotRetrieveData):
        await api.get_all_devices()


async def test_get_all_devices_empty_desc_skips_climate_when_initialized(
    mock_session: MockSession,
) -> None:
    """Test empty climate descriptions are skipped once bridge is initialized."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    set_private_attr(api, "_initialized", True)

    async def fake_get(
        path: str, _reply_json: bool = True
    ) -> tuple[int, dict[str, object]]:
        """Return empty device descriptions for climate."""
        if path.endswith("type=clima"):
            return HTTPStatus.OK, {
                "num": 1,
                "desc": [],
                "status": [0],
                "val": [0],
                "protected": [0],
                "env": [0],
                "env_desc": [""],
            }
        return HTTPStatus.OK, {
            "num": 0,
            "desc": [],
            "status": [],
            "val": [],
            "protected": [],
            "env": [],
            "env_desc": [""],
        }

    set_private_attr(api, "_get_page_result", AsyncMock(side_effect=fake_get))

    devices = await api.get_all_devices()
    assert CLIMATE not in devices


@pytest.mark.parametrize(
    ("vedo_pin", "login_side_effect", "get_side_effect", "expected"),
    [
        ("1234", None, (HTTPStatus.OK, {"present": [1]}), True),
        ("9999", None, (HTTPStatus.OK, {"present": [1]}), True),
        ("9999", CannotAuthenticate(), (HTTPStatus.OK, {"present": [1]}), False),
        ("1234", None, CannotRetrieveData(), False),
    ],
)
async def test_vedo_enabled_paths(
    mock_session: MockSession,
    vedo_pin: str,
    login_side_effect: Exception | None,
    get_side_effect: tuple[int, dict[str, object]] | Exception,
    expected: bool,
) -> None:
    """Test VEDO feature availability checks for success and failure cases."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)

    login_mock = AsyncMock(return_value=True)
    if login_side_effect is not None:
        login_mock = AsyncMock(side_effect=login_side_effect)
    set_private_attr(api, "_login", login_mock)

    if isinstance(get_side_effect, Exception):
        set_private_attr(
            api,
            "_get_page_result",
            AsyncMock(side_effect=get_side_effect),
        )
    else:
        set_private_attr(
            api,
            "_get_page_result",
            AsyncMock(return_value=get_side_effect),
        )

    assert await api.vedo_enabled(vedo_pin) is expected

    if vedo_pin == "9999" and login_side_effect is None:
        login_mock.assert_awaited_once_with({"alm": "9999"}, "Vedo system")
