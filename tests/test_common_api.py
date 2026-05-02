"""Tests for shared Comelit API code paths."""

from __future__ import annotations

from http import HTTPStatus
from http.cookies import SimpleCookie
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import orjson
import pytest
from aiohttp import ContentTypeError, RequestInfo
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

from aiocomelit.api import (
    ComeliteSerialBridgeApi,
    ComelitVedoApi,
    ComelitVedoAreaObject,
    ComelitVedoZoneObject,
)
from aiocomelit.const import BRIDGE, VEDO, AlarmAreaState, AlarmZoneState
from aiocomelit.exceptions import (
    CannotAuthenticate,
    CannotConnect,
    CannotRetrieveData,
    DeviceStorageFailureError,
)
from tests.conftest import (
    MockResponse,
    call_private_async,
    connector_error,
    set_private_attr,
    setup_api,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from tests.conftest import MockSession

    GetPageResultMethod = Callable[[str, bool], Awaitable[tuple[int, dict[str, Any]]]]
    PostPageResultMethod = Callable[[str, dict[str, Any]], Awaitable[SimpleCookie]]
    CheckLoggedInMethod = Callable[[str], Awaitable[bool]]
    IsSessionActiveMethod = Callable[[], Awaitable[bool]]
    SleepMethod = Callable[[float], Awaitable[None]]
    LoginMethod = Callable[[dict[str, Any], str], Awaitable[bool]]
    TranslateZoneMethod = Callable[[ComelitVedoZoneObject], Awaitable[AlarmZoneState]]
    TranslateAreaMethod = Callable[[ComelitVedoAreaObject], Awaitable[AlarmAreaState]]
    CreateAreaMethod = Callable[
        [dict[str, Any], dict[str, Any], int], Awaitable[ComelitVedoAreaObject]
    ]
    CreateZoneMethod = Callable[
        [dict[str, Any], dict[str, Any], int], Awaitable[ComelitVedoZoneObject]
    ]
    AsyncGetPageDataMethod = Callable[
        [str, str, str | int | None], Awaitable[tuple[bool, dict[str, Any]]]
    ]


async def test_get_page_result_success(mock_session: MockSession) -> None:
    """Test successful GET with JSON parsing."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    get_page_result: GetPageResultMethod = call_private_async(api, "_get_page_result")
    mock_session.queue_get(MockResponse(json_data={"ok": True}))

    status, data = await get_page_result("/status.json", True)

    assert status == HTTPStatus.OK
    assert data == {"ok": True}


async def test_get_page_result_no_json_reply(mock_session: MockSession) -> None:
    """Test GET path that skips JSON parsing."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    get_page_result: GetPageResultMethod = call_private_async(api, "_get_page_result")
    mock_session.queue_get(MockResponse(json_data={"ignored": True}))

    status, data = await get_page_result("/empty.json", False)

    assert status == HTTPStatus.OK
    assert data == {}


@pytest.mark.parametrize(
    ("queued_response", "expected_exception"),
    [
        (TimeoutError(), CannotConnect),
        (connector_error(), CannotConnect),
        (
            MockResponse(
                status=HTTPStatus.INTERNAL_SERVER_ERROR, json_data={"error": True}
            ),
            CannotRetrieveData,
        ),
        (
            MockResponse(json_exc=orjson.JSONDecodeError("bad json", "{}", 0)),
            DeviceStorageFailureError,
        ),
        (
            MockResponse(
                json_exc=ContentTypeError(
                    request_info=RequestInfo(
                        url=URL("http://127.0.0.1"),
                        method="GET",
                        headers=CIMultiDictProxy(CIMultiDict()),
                        real_url=URL("http://127.0.0.1"),
                    ),
                    history=(),
                    message="wrong type",
                )
            ),
            DeviceStorageFailureError,
        ),
    ],
)
async def test_get_page_result_raises_on_connection_and_status_errors(
    mock_session: MockSession,
    queued_response: Exception | MockResponse,
    expected_exception: type[Exception],
) -> None:
    """Test GET error handling for connection failures and non-200 statuses."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    get_page_result: GetPageResultMethod = call_private_async(api, "_get_page_result")
    mock_session.queue_get(queued_response)

    with pytest.raises(expected_exception):
        await get_page_result("/status.json", True)


async def test_post_page_result_success_and_errors(
    mock_session: MockSession,
) -> None:
    """Test POST happy-path and error handling."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    post_page_result: PostPageResultMethod = call_private_async(
        api, "_post_page_result"
    )

    cookies = SimpleCookie()
    cookies["sid"] = "abc"
    mock_session.queue_post(MockResponse(status=HTTPStatus.OK, cookies=cookies))
    result = await post_page_result("/login.cgi", {"dom": "1234"})
    assert "sid" in result

    mock_session.queue_post(TimeoutError())
    with pytest.raises(CannotConnect):
        await post_page_result("/login.cgi", {})

    mock_session.queue_post(connector_error())
    with pytest.raises(CannotConnect):
        await post_page_result("/login.cgi", {})

    mock_session.queue_post(MockResponse(status=HTTPStatus.FORBIDDEN))
    with pytest.raises(CannotRetrieveData):
        await post_page_result("/login.cgi", {})


async def test_session_state_and_logout(mock_session: MockSession) -> None:
    """Test session state and logout behavior."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    is_session_active: IsSessionActiveMethod = call_private_async(
        api, "_is_session_active"
    )

    assert await is_session_active() is True

    mock_session.queue_post(MockResponse(status=HTTPStatus.OK, cookies=SimpleCookie()))
    await api.logout()
    assert mock_session.cookie_jar.cleared is True

    mock_session.closed = True
    await api.logout()


async def test_check_logged_in_bridge_and_vedo(mock_session: MockSession) -> None:
    """Test login-state parsing for bridge and vedo."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    check_logged_in: CheckLoggedInMethod = call_private_async(api, "_check_logged_in")

    set_private_attr(
        api,
        "_get_page_result",
        AsyncMock(return_value=(HTTPStatus.OK, {"domus": "111111111111"})),
    )
    assert await check_logged_in(BRIDGE) is True

    set_private_attr(
        api,
        "_get_page_result",
        AsyncMock(return_value=(HTTPStatus.OK, {"logged": 1})),
    )
    assert await check_logged_in(VEDO) is True


async def test_sleep_between_call(mock_session: MockSession) -> None:
    """Test sleep helper delegates to asyncio.sleep."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    sleep_between_call: SleepMethod = call_private_async(api, "_sleep_between_call")
    sleep_mock = AsyncMock()
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr("aiocomelit.api.asyncio.sleep", sleep_mock)
        await sleep_between_call(0.01)
    sleep_mock.assert_awaited_once_with(0.01)


async def test_login_happy_path_and_failure(mock_session: MockSession) -> None:
    """Test internal login success and failure paths."""
    api = setup_api(ComeliteSerialBridgeApi, "127.0.0.1", 80, "1234", mock_session)
    login_internal: LoginMethod = call_private_async(api, "_login")

    post_mock = AsyncMock()
    set_private_attr(api, "_check_logged_in", AsyncMock(side_effect=[True]))
    set_private_attr(api, "_post_page_result", post_mock)
    assert await login_internal({"dom": "1234"}, BRIDGE) is True
    post_mock.assert_not_awaited()

    set_private_attr(api, "_check_logged_in", AsyncMock(side_effect=[False]))
    set_private_attr(api, "_post_page_result", AsyncMock(return_value=SimpleCookie()))
    with pytest.raises(CannotAuthenticate):
        await login_internal({"dom": "1234"}, BRIDGE)

    cookies = SimpleCookie()
    cookies["sid"] = "ok"
    set_private_attr(api, "_check_logged_in", AsyncMock(side_effect=[False, False]))
    set_private_attr(api, "_post_page_result", AsyncMock(return_value=cookies))
    assert await login_internal({"dom": "1234"}, BRIDGE) is False


@pytest.mark.parametrize(
    ("zone_status", "expected"),
    [
        (2, AlarmZoneState.ALARM),
        (1, AlarmZoneState.OPEN),
        (4, AlarmZoneState.FAULTY),
        (8, AlarmZoneState.SABOTATED),
        (32, AlarmZoneState.ARMED),
        (128, AlarmZoneState.EXCLUDED),
        (256, AlarmZoneState.ISOLATED),
        (512, AlarmZoneState.UNAVAILABLE),
        (32768, AlarmZoneState.INHIBITED),
        (0, AlarmZoneState.REST),
        (99999, AlarmZoneState.ALARM),
    ],
)
async def test_translate_zone_status(
    mock_session: MockSession,
    zone_status: int,
    expected: AlarmZoneState,
) -> None:
    """Test zone status translations."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    translate_zone_status: TranslateZoneMethod = call_private_async(
        api, "_translate_zone_status"
    )
    zone = ComelitVedoZoneObject(
        index=0,
        name="Zone",
        status_api=f"{zone_status:04x}",
        status=zone_status,
        human_status=AlarmZoneState.UNKNOWN,
    )

    assert await translate_zone_status(zone) == expected


@pytest.mark.parametrize(
    ("area_updates", "expected"),
    [
        ({"out_time": True}, AlarmAreaState.EXIT_DELAY),
        ({"in_time": True}, AlarmAreaState.ENTRY_DELAY),
        ({"sabotage": True}, AlarmAreaState.SABOTAGE),
        ({"alarm": True, "armed": 1}, AlarmAreaState.TRIGGERED),
        ({"armed": 1}, AlarmAreaState.ARMED),
        ({"ready": True}, AlarmAreaState.DISARMED),
        ({}, AlarmAreaState.DISARMED),
    ],
)
async def test_translate_area_status(
    mock_session: MockSession,
    area_updates: dict[str, bool | int],
    expected: AlarmAreaState,
) -> None:
    """Test area status translations."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    translate_area_status: TranslateAreaMethod = call_private_async(
        api, "_translate_area_status"
    )
    area = ComelitVedoAreaObject(
        index=0,
        name="Area",
        p1=False,
        p2=False,
        ready=False,
        armed=0,
        alarm=False,
        alarm_memory=False,
        sabotage=False,
        anomaly=False,
        in_time=False,
        out_time=False,
        human_status=AlarmAreaState.UNKNOWN,
    )
    for key, value in area_updates.items():
        setattr(area, key, value)

    assert await translate_area_status(area) == expected


async def test_create_area_and_zone_objects(mock_session: MockSession) -> None:
    """Test creation of area and zone objects."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    create_area_object: CreateAreaMethod = call_private_async(
        api, "_create_area_object"
    )
    create_zone_object: CreateZoneMethod = call_private_async(
        api, "_create_zone_object"
    )

    area = await create_area_object(
        {
            "description": ["Perimeter"],
            "p1_pres": [False],
            "p2_pres": [True],
        },
        {
            "ready": [True],
            "armed": [0],
            "alarm": [False],
            "alarm_memory": [False],
            "sabotage": [False],
            "anomaly": [False],
            "in_time": [False],
            "out_time": [False],
        },
        0,
    )
    assert area.name == "Perimeter"
    assert area.human_status == AlarmAreaState.DISARMED

    zone = await create_zone_object(
        {"description": ["Front Door"]},
        {"status": "0020"},
        0,
    )
    assert zone.status == int("0x20", 16)
    assert zone.human_status == AlarmZoneState.ARMED


async def test_async_get_page_data_present_check(mock_session: MockSession) -> None:
    """Test async page data helper present-check behavior."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    async_get_page_data: AsyncGetPageDataMethod = call_private_async(
        api, "_async_get_page_data"
    )
    set_private_attr(
        api,
        "_get_page_result",
        AsyncMock(
            return_value=(
                HTTPStatus.OK,
                {
                    "logged": 1,
                    "present": [1, 0],
                },
            )
        ),
    )

    reply_status, _ = await async_get_page_data(
        "AREA description",
        "/user/area_desc.json",
        1,
    )
    assert reply_status is True

    set_private_attr(
        api,
        "_get_page_result",
        AsyncMock(
            return_value=(
                HTTPStatus.OK,
                {
                    "logged": 1,
                    "present": [0, 0],
                },
            )
        ),
    )
    reply_status, _ = await async_get_page_data(
        "AREA description",
        "/user/area_desc.json",
        1,
    )
    assert reply_status is False

    set_private_attr(
        api,
        "_get_page_result",
        AsyncMock(return_value=(HTTPStatus.OK, {"logged": 1, "ready": [1]})),
    )
    reply_status, _ = await async_get_page_data(
        "AREA statistics",
        "/user/area_stat.json",
        None,
    )
    assert reply_status is True
