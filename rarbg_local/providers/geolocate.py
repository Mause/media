from datetime import datetime, timezone

import geoip2.database
import geoip_api
from fastapi import Request
from geoip2.models import City
from geoip_api.core.lookup import get_database_path


def resolve_location(request: Request) -> City | None:
    api = geoip_api.GeoIPLookup(download_if_missing=True)

    with geoip2.database.Reader(api.city_db_path) as city_reader:
        return city_reader.city(request.client.host) if request.client else None


def get_age() -> datetime:
    with geoip2.database.Reader(get_database_path()) as city_reader:
        m = city_reader.metadata()
        return datetime.fromtimestamp(m.build_epoch, timezone.utc)
