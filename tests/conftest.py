"""Shared test fixtures for aiocomelit."""

from __future__ import annotations

from http import HTTPStatus
from http.cookies import SimpleCookie
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import orjson
import pytest
from aiohttp import ClientConnectorError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiohttp import ClientSession

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class MockCookieJar:
    """Minimal cookie jar API used by the library."""

    def __init__(self) -> None:
        """Initialize empty cookie storage."""
        self.cookies: SimpleCookie = SimpleCookie()
        self.cleared = False

    def update_cookies(self, cookies: SimpleCookie, _url: object) -> None:
        """Store cookies set by the API."""
        self.cookies = cookies

    def clear(self) -> None:
        """Clear all stored cookies."""
        self.cleared = True
        self.cookies = SimpleCookie()


class MockResponse:
    """Mock aiohttp response object."""

    def __init__(
        self,
        *,
        status: HTTPStatus = HTTPStatus.OK,
        json_data: JsonValue | None = None,
        text_data: str | None = None,
        cookies: SimpleCookie | None = None,
        json_exc: Exception | None = None,
    ) -> None:
        """Initialize response payload and behavior for tests."""
        self.status = status
        self._json_data = json_data
        self._text_data = text_data
        self.cookies = cookies or SimpleCookie()
        self._json_exc = json_exc

    async def text(self) -> str:
        """Return textual response body."""
        if self._text_data is not None:
            return self._text_data
        if self._json_data is None:
            return ""
        json_bytes = orjson.dumps(self._json_data)
        if isinstance(json_bytes, (bytes, bytearray)):
            return json_bytes.decode()
        return str(json_bytes)

    async def json(
        self,
        loads: Callable[[str | bytes | bytearray], JsonValue] | None = None,
    ) -> JsonValue | None:
        """Return parsed JSON body."""
        if self._json_exc:
            raise self._json_exc
        if loads and isinstance(self._json_data, (str, bytes, bytearray)):
            return loads(self._json_data)
        return self._json_data


class MockSession:
    """Mock aiohttp ClientSession."""

    def __init__(self) -> None:
        """Initialize request queues and call tracking."""
        self.closed = False
        self.cookie_jar = MockCookieJar()
        self.get_calls: list[str] = []
        self.post_calls: list[str] = []
        self._get_queue: list[MockResponse | Exception] = []
        self._post_queue: list[MockResponse | Exception] = []

    def queue_get(self, *responses: MockResponse | Exception) -> None:
        """Queue GET responses or exceptions."""
        self._get_queue.extend(responses)

    def queue_post(self, *responses: MockResponse | Exception) -> None:
        """Queue POST responses or exceptions."""
        self._post_queue.extend(responses)

    async def get(self, url: str, **_kwargs: object) -> MockResponse:
        """Return queued GET response."""
        self.get_calls.append(url)
        item = self._get_queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def post(self, url: str, **_kwargs: object) -> MockResponse:
        """Return queued POST response."""
        self.post_calls.append(url)
        item = self._post_queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def setup_api[ApiType](
    api_factory: Callable[[str, int, str, ClientSession], ApiType],
    host: str,
    port: int,
    pin: str,
    mock_session: MockSession,
) -> ApiType:
    """Build a production API instance backed by mock session."""
    return api_factory(host, port, pin, cast("ClientSession", mock_session))


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


def connector_error() -> ClientConnectorError:
    """Create a synthetic connector error for connection failure tests."""
    conn_key = SimpleNamespace(ssl=False, host="127.0.0.1", port=80)
    return ClientConnectorError(cast("Any", conn_key), OSError("boom"))


@pytest.fixture
def mock_session() -> MockSession:
    """Return a reusable mocked aiohttp session."""
    return MockSession()


@pytest.fixture
def fixture_loader() -> Callable[[str], dict[str, JsonValue]]:
    """Load JSON fixtures from tests/fixtures."""

    def _load(name: str) -> dict[str, JsonValue]:
        fixture_path = Path("tests/fixtures") / f"{name}.json"
        return cast("dict[str, JsonValue]", orjson.loads(fixture_path.read_bytes()))

    return _load
