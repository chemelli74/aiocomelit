"""Tests for Comelit VEDO API."""

from __future__ import annotations

from http import HTTPStatus
from http.cookies import SimpleCookie
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock

import pytest

from aiocomelit.api import ComelitVedoApi, ComelitVedoAreaObject
from aiocomelit.const import (
    ALARM_AREA,
    ALARM_ZONE,
    SLEEP_AFTER_VEDO_LOGIN,
    VEDO,
    AlarmAreaState,
)
from aiocomelit.exceptions import CannotRetrieveData
from tests.conftest import (
    call_private_async,
    get_private_attr,
    set_private_attr,
    set_private_mapping_item,
    setup_api,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    LoginMethod = Callable[[dict[str, Any], str], Awaitable[bool]]
    from aiohttp import ClientSession

AREA_COUNT = 4


async def test_vedo_login_delegates_to_common(mock_session: ClientSession) -> None:
    """Test VEDO login delegates to common login helper."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    login_mock = AsyncMock(return_value=True)
    set_private_attr(api, "_login", login_mock)

    assert await api.login() is True
    login_mock.assert_awaited_once_with({"code": "9999"}, VEDO)


@pytest.mark.parametrize(
    (
        "new_firmware",
        "page_data",
        "http_query",
        "http_call",
        "http_param",
        "success_response",
        "failure_response",
    ),
    [
        (
            False,
            {},
            {"force": 1, "tot": 32, "vedo": 1},
            "_get_page_result",
            "query",
            (HTTPStatus.OK, {}),
            (HTTPStatus.INTERNAL_SERVER_ERROR, {}),
        ),
        (
            True,
            {"page": "<html> www.comelitgroup.com </html>"},
            {"area_param": 32, "forced": 1, "type_param": "tot", "vedo_param": 1},
            "_post_page_result",
            "payload",
            (HTTPStatus.NOT_FOUND, SimpleCookie()),
            (HTTPStatus.INTERNAL_SERVER_ERROR, SimpleCookie()),
        ),
    ],
)
async def test_set_zone_status_success_and_failure(
    mock_session: ClientSession,
    new_firmware: bool,
    page_data: dict[str, str],
    http_query: dict[str, str],
    http_call: str,
    http_param: str,
    success_response: tuple[HTTPStatus, dict[str, object] | SimpleCookie],
    failure_response: tuple[HTTPStatus, dict[str, object] | SimpleCookie],
) -> None:
    """Test set_zone_status URL generation and status handling."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    login_internal: LoginMethod = call_private_async(api, "_login")

    cookies = SimpleCookie()
    cookies["sid"] = "ok"
    sleep_mock = AsyncMock()

    set_private_attr(api, "_check_logged_in", AsyncMock(side_effect=[False, True]))
    set_private_attr(
        api,
        "_post_page_result",
        AsyncMock(return_value=(HTTPStatus.OK, cookies)),
    )
    set_private_attr(api, "_sleep_between_call", sleep_mock)

    get_mock = AsyncMock(return_value=(HTTPStatus.NOT_FOUND, page_data))
    set_private_attr(api, "_get_page_result", get_mock)
    assert await login_internal({"code": "9999"}, VEDO) is True
    sleep_mock.assert_awaited_once_with(SLEEP_AFTER_VEDO_LOGIN)
    assert get_private_attr(api, "_is_new_firmware") is new_firmware

    http_mock = AsyncMock(return_value=success_response)
    set_private_attr(api, http_call, http_mock)
    assert await api.set_zone_status(32, "tot", force=True) is True
    call_args = http_mock.await_args
    assert call_args is not None
    called_query = call_args.kwargs[http_param]
    assert called_query == http_query

    http_fail_mock = AsyncMock(return_value=failure_response)
    set_private_attr(api, http_call, http_fail_mock)
    assert await api.set_zone_status(1, "dis", force=False) is False


async def test_get_area_status(
    mock_session: ClientSession,
    fixture_loader: Callable[[str], dict[str, object]],
) -> None:
    """Test get_area_status delegates with area fields and stats payload."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    area_desc = fixture_loader("vedo/area_desc")
    area_stat = fixture_loader("vedo/area_stat")
    description_list = cast("list[str]", area_desc["description"])
    p1_pres_list = cast("list[bool]", area_desc["p1_pres"])
    p2_pres_list = cast("list[bool]", area_desc["p2_pres"])
    area = ComelitVedoAreaObject(
        index=0,
        name=description_list[0],
        p1=p1_pres_list[0],
        p2=p2_pres_list[0],
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
    set_private_attr(
        api,
        "_async_get_page_data",
        AsyncMock(return_value=(True, area_stat)),
    )
    create_mock = AsyncMock(return_value=area)
    set_private_attr(api, "_create_area_object", create_mock)

    updated = await api.get_area_status(area)
    assert updated is area
    assert updated.name == "Perimetrale"
    create_mock.assert_awaited_once_with(
        {"description": ["Perimetrale"], "p1_pres": [0], "p2_pres": [0]},
        area_stat,
        0,
    )


async def test_get_all_areas_and_zones_success(
    mock_session: ClientSession,
    fixture_loader: Callable[[str], dict[str, object]],
) -> None:
    """Test full successful fetch of area and zone data."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    responses = [
        (True, fixture_loader("vedo/area_desc")),
        (True, fixture_loader("vedo/zone_desc")),
        (True, fixture_loader("vedo/area_stat")),
        (True, fixture_loader("vedo/zone_stat")),
    ]
    set_private_attr(api, "_async_get_page_data", AsyncMock(side_effect=responses))
    set_private_attr(api, "_sleep_between_call", AsyncMock())

    result = await api.get_all_areas_and_zones()

    assert ALARM_AREA in result
    assert ALARM_ZONE in result
    assert len(result[ALARM_AREA]) == AREA_COUNT
    assert result[ALARM_ZONE][12].human_status.value == "open"


async def test_get_all_areas_and_zones_cache_for_desc_pages(
    mock_session: ClientSession,
    fixture_loader: Callable[[str], dict[str, object]],
) -> None:
    """Test cached description pages are reused while stats are refreshed."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    set_private_mapping_item(api, "_json_data", 1, fixture_loader("vedo/area_desc"))
    set_private_mapping_item(api, "_json_data", 2, fixture_loader("vedo/zone_desc"))
    set_private_mapping_item(api, "_json_data", 3, fixture_loader("vedo/area_stat"))
    set_private_mapping_item(api, "_json_data", 4, fixture_loader("vedo/zone_stat"))
    set_private_attr(api, "_sleep_between_call", AsyncMock())

    calls: list[str] = []

    async def fake_async_get(
        desc: str,
        _page: str,
        _present: str = "present",
    ) -> tuple[bool, dict[str, object]]:
        """Return dynamic stats while tracking accessed page descriptions."""
        calls.append(desc)
        if "AREA statistics" in desc:
            return True, fixture_loader("vedo/area_stat")
        return True, fixture_loader("vedo/zone_stat")

    set_private_attr(api, "_async_get_page_data", AsyncMock(side_effect=fake_async_get))

    result = await api.get_all_areas_and_zones()

    assert len(result[ALARM_AREA]) == AREA_COUNT
    assert calls == ["AREA statistics", "ZONE statistics"]


@pytest.mark.parametrize("retry_succeeds", [True, False])
async def test_get_all_areas_and_zones_login_retry(
    mock_session: ClientSession,
    fixture_loader: Callable[[str], dict[str, object]],
    retry_succeeds: bool,
) -> None:
    """Test login retry behavior when first area fetch fails."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    login_mock = AsyncMock(return_value=True)
    set_private_attr(api, "login", login_mock)
    set_private_attr(api, "_sleep_between_call", AsyncMock())

    responses = (
        [
            (False, fixture_loader("vedo/area_desc")),
            (True, fixture_loader("vedo/area_desc")),
            (True, fixture_loader("vedo/zone_desc")),
            (True, fixture_loader("vedo/area_stat")),
            (True, fixture_loader("vedo/zone_stat")),
        ]
        if retry_succeeds
        else [
            (False, fixture_loader("vedo/area_desc")),
            (False, fixture_loader("vedo/area_desc")),
        ]
    )
    set_private_attr(api, "_async_get_page_data", AsyncMock(side_effect=responses))

    if retry_succeeds:
        result = await api.get_all_areas_and_zones()
        assert len(result[ALARM_AREA]) == AREA_COUNT
        login_mock.assert_awaited_once()
        return

    with pytest.raises(CannotRetrieveData):
        await api.get_all_areas_and_zones()

    login_mock.assert_awaited_once()
