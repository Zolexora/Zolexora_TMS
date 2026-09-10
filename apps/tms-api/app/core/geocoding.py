from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger("zolexora.geocoding")


@dataclass
class GeocodingLocation:
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    place_id: Optional[str] = None
    display_name: Optional[str] = None


class BaseGeocodingProvider:
    async def geocode(self, address: str) -> Optional[GeocodingLocation]:
        raise NotImplementedError

    async def reverse_geocode(self, lat: float, lng: float) -> Optional[GeocodingLocation]:
        raise NotImplementedError


class DefaultGeocodingProvider(BaseGeocodingProvider):
    """
    Default pluggable provider.
    Ensures that booking creation and location workflows are decoupled
    from any third-party geocoding service, allowing manual coordinate entry
    and graceful offline operation.
    """

    async def geocode(self, address: str) -> Optional[GeocodingLocation]:
        if not address or not address.strip():
            return None
        # Return fallback coordinate envelope or pass-through
        return GeocodingLocation(
            address=address.strip(),
            latitude=None,
            longitude=None,
            display_name=address.strip(),
        )

    async def reverse_geocode(self, lat: float, lng: float) -> Optional[GeocodingLocation]:
        return GeocodingLocation(
            address=f"Location ({lat:.4f}, {lng:.4f})",
            latitude=lat,
            longitude=lng,
        )


geocoding_service = DefaultGeocodingProvider()
