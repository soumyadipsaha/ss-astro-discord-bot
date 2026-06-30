from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import geonamescache

_gc = geonamescache.GeonamesCache()


def _cities():
    return _gc.get_cities().values()


def lookup_city(query: str) -> dict:
    """
    Find a city by name (case-insensitive). Returns the most populous match.

    Returns dict: {lat, lon, tz_name, display}
    Raises ValueError if nothing matches.
    """
    q = query.strip().lower()

    # Exact name match first, then starts-with, then contains.
    for predicate in (
        lambda name: name == q,
        lambda name: name.startswith(q),
        lambda name: q in name,
    ):
        matches = [c for c in _cities() if predicate(c["name"].lower())]
        if matches:
            break

    if not matches:
        raise ValueError(
            f"City \"{query}\" not found. Try a major city name (e.g. \"Mumbai\", \"London\")."
        )

    best = max(matches, key=lambda c: c.get("population", 0))
    return {
        "lat": float(best["latitude"]),
        "lon": float(best["longitude"]),
        "tz_name": best["timezone"],
        "display": f"{best['name']}, {best['countrycode']}",
    }


def utc_offset(tz_name: str, year: int, month: int, day: int, hour: int, minute: int) -> float:
    """UTC offset in fractional hours for the given IANA timezone at a specific local datetime."""
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Unknown timezone: {tz_name!r}")
    dt = datetime(year, month, day, hour, minute, tzinfo=tz)
    return dt.utcoffset().total_seconds() / 3600
