"""API Client for Airplanes.Live."""

import logging
import aiohttp
import asyncio
from typing import Optional
from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)


class AirplanesLiveAPI:
    """Async API Client for Airplanes.Live."""

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._lock = asyncio.Lock()

    async def _request(self, endpoint: str) -> Optional[dict]:
        url = f"{API_BASE_URL}{endpoint}"

        async with self._lock:
            try:
                await asyncio.sleep(1.1)
                async with self._session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("ac", [])
                    return []
            except Exception as err:
                _LOGGER.error("Airplanes.Live API Error: %s", err)
                return []

    async def get_aircraft_by_hex(self, hex_code: str):
        return await self._request(f"/hex/{hex_code.strip().lower()}")

    async def get_aircraft_by_callsign(self, callsign: str):
        return await self._request(f"/callsign/{callsign.strip().upper()}")

    async def get_aircraft_by_reg(self, reg: str):
        return await self._request(f"/reg/{reg.strip().upper()}")

    async def get_aircraft_in_zone(self, lat: float, lon: float, radius: int):
        return await self._request(f"/point/{lat}/{lon}/{radius}")
