"""Fixtures for testing purposes."""

from pathlib import Path

import anyio
import orjson

from .const import _LOGGER

ENABLE_FIXTURES = True


async def load_fixture(schema: str) -> dict:
    """Load a fixture from the out/ folder."""
    reply_json = {}
    file = f"./src/fixtures/{schema}.json"
    _LOGGER.info("Current working directory: %s", Path.cwd())
    if Path(file).exists():
        _LOGGER.info("Loading fixture from %s", file)
        async with await anyio.open_file(file) as fp:
            reply_json = orjson.loads(await fp.read())
    else:
        _LOGGER.warning("No fixture found for %s", schema)
    return reply_json
