"""Tests for Comelit VEDO API."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock

import pytest

from aiocomelit.api import ComelitVedoApi, ComelitVedoAreaObject
from aiocomelit.const import ALARM_AREA, ALARM_ZONE, VEDO, AlarmAreaState
from aiocomelit.exceptions import CannotRetrieveData
from tests.conftest import set_private_attr, set_private_mapping_item, setup_api

if TYPE_CHECKING:
    from collections.abc import Callable

    from aiohttp import ClientSession

AREA_COUNT = 4


async def test_vedo_login_delegates_to_common(mock_session: ClientSession) -> None:
    """Test VEDO login delegates to common login helper."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    login_mock = AsyncMock(return_value=True)
    set_private_attr(api, "_login", login_mock)

    assert await api.login() is True
    login_mock.assert_awaited_once_with({"code": "9999"}, VEDO)


async def test_set_zone_status_success_and_failure(mock_session: ClientSession) -> None:
    """Test set_zone_status URL generation and status handling."""
    api = setup_api(ComelitVedoApi, "127.0.0.1", 80, "9999", mock_session)
    get_mock = AsyncMock(return_value=(HTTPStatus.OK, {}))
    set_private_attr(api, "_get_page_result", get_mock)

    assert await api.set_zone_status(32, "tot", force=True) is True
    call_args = get_mock.await_args
    assert call_args is not None
    called_url = call_args.args[0]
    assert "tot=32" in called_url
    assert "force=1" in called_url

    set_private_attr(
        api,
        "_get_page_result",
        AsyncMock(return_value=(HTTPStatus.INTERNAL_SERVER_ERROR, {})),
    )
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
        {"description": "Perimetrale", "p1_pres": 0, "p2_pres": 0},
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
