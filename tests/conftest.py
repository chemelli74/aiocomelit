"""Shared test fixtures for aiocomelit."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import orjson
import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def setup_api[ApiType](
    api_factory: Callable[[str, int, str, ClientSession], ApiType],
    host: str,
    port: int,
    pin: str,
    session: ClientSession,
) -> ApiType:
    """Build a production API instance backed by a real session."""
    return api_factory(host, port, pin, session)


def set_private_attr(api: object, name: str, value: object) -> None:
    """Set private API attribute for controlled test setup."""
    object.__setattr__(api, name, value)


def set_private_mapping_item(
    api: object,
    name: str,
    key: object,
    value: object,
) -> None:
    """Set one item inside a private mapping attribute."""
    mapping = cast("dict[object, object]", object.__getattribute__(api, name))
    mapping[key] = value


def call_private_async[ReturnType](
    api: object,
    name: str,
) -> Callable[..., Awaitable[ReturnType]]:
    """Get a private async method with a typed callable signature."""
    return cast(
        "Callable[..., Awaitable[ReturnType]]",
        object.__getattribute__(api, name),
    )


@pytest.fixture
async def mock_session() -> ClientSession:
    """Return a real ClientSession for testing."""
    session = ClientSession()
    yield session
    await session.close()


@pytest.fixture
def aiohttp_mock() -> aioresponses:
    """Return aioresponses mock for HTTP calls."""
    return aioresponses()


@pytest.fixture
def fixture_loader() -> Callable[[str], dict[str, JsonValue]]:
    """Load JSON fixtures from tests/fixtures."""

    def _load(name: str) -> dict[str, JsonValue]:
        fixture_path = Path("tests/fixtures") / f"{name}.json"
        return cast("dict[str, JsonValue]", orjson.loads(fixture_path.read_bytes()))

    return _load
