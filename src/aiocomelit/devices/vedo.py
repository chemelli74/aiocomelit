# Copyright 2023 Simone Chemelli and contributors
# SPDX-License-Identifier: Apache-2.0

"""Support for the Comelit SimpleHome VEDO alarm."""

from aiocomelit.api import ComelitHttpApi
from aiocomelit.const import VEDO


class ComelitVedoApi(ComelitHttpApi):
    """Queries Comelit SimpleHome VEDO alarm."""

    _vedo_url_suffix: str = ""
    _vedo_url_action: str = "action.cgi"
    _host_type = VEDO

    async def login(self) -> bool:
        """Login to VEDO system."""
        payload = {"code": self.device_pin}
        return await self._login(payload, VEDO)
