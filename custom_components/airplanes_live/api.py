"""API Client for Airplanes.Live."""
import logging
import aiohttp
import asyncio
from typing import Optional

from .const import API_BASE_URL

_LOGGER = logging.getLogger(__name__)

class AirplanesLiveAPI:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._lock = asyncio.Lock()

    async def _request(self, url: str) -> Optional[dict]:
        """Algemene request handler."""
        try:
            async with self._session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as err:
            _LOGGER.debug(f"Fout bij aanroep {url}: {err}")
            return None

    async def get_aircraft_by_hex(self, hex_code: str):
        res = await self._request(f"{API_BASE_URL}/hex/{hex_code.strip().lower()}")
        return res.get("ac", []) if res else []

    async def get_aircraft_by_callsign(self, callsign: str):
        res = await self._request(f"{API_BASE_URL}/callsign/{callsign.strip().upper()}")
        return res.get("ac", []) if res else []

    async def get_aircraft_by_reg(self, registration: str):
        res = await self._request(f"{API_BASE_URL}/reg/{registration.strip().upper()}")
        return res.get("ac", []) if res else []

    async def get_aircraft_in_zone(self, lat: float, lon: float, radius: int):
        res = await self._request(f"{API_BASE_URL}/point/{lat}/{lon}/{radius}")
        return res.get("ac", []) if res else []

    async def get_global_emergencies(self):
        res = await self._request(f"{API_BASE_URL}/squawk/7700")
        return res.get("ac", []) if res else []

    async def get_global_military(self):
        res = await self._request(f"{API_BASE_URL}/mil")
        return res.get("ac", []) if res else []

    async def get_planespotters_photo(self, registration: str, hex_code: str = None) -> Optional[str]:
        """Haal de live fotolink op via Registratie of Hex."""
        
        async def fetch_photo_from_url(url: str):
            data = await self._request(url)
            if data and "photos" in data and len(data["photos"]) > 0:
                photo = data["photos"][0]
                # Planespotters gebruikt thumbnail_large voor de beste kleine resolutie!
                return photo.get("thumbnail_large", {}).get("src") or photo.get("thumbnail", {}).get("src")
            return None

        if registration and registration != "Unknown":
            url = f"https://api.planespotters.net/pub/photos/reg/{registration.strip()}"
            photo_url = await fetch_photo_from_url(url)
            if photo_url: 
                return photo_url

        if hex_code and hex_code != "Unknown":
            url = f"https://api.planespotters.net/pub/photos/hex/{hex_code.strip()}"
            photo_url = await fetch_photo_from_url(url)
            if photo_url: 
                return photo_url
            
        return None
