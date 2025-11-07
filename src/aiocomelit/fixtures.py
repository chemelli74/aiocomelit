"""Fixtures for testing purposes."""

from pathlib import Path

import anyio
import orjson

from .const import _LOGGER


async def load_fixture(dev_type: str) -> dict:
    """Load a fixture from the out/ folder."""
    reply_json = {}
    file = f"./json/{dev_type}.json"
    _LOGGER.warning("Current working directory: %s", Path.cwd())
    if Path(file).exists():
        _LOGGER.warning("Loading fixture from %s", file)
        async with await anyio.open_file(file) as fp:
            reply_json = orjson.loads(await fp.read())
    else:
        _LOGGER.warning("No fixture found for %s", dev_type)
    return reply_json
