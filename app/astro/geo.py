import re
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


_DECIMAL_OFFSET_RE = re.compile(r"^[+-]?\d+(\.\d+)?$")
_HM_OFFSET_RE = re.compile(r"^([+-]?)(\d{1,2}):(\d{2})$")


def parse_offset_hours(value: str) -> float | None:
    """Parse a numeric UTC offset string to fractional hours.

    Accepts decimal forms ('5.5', '-4', '+5.5') and hour:minute forms ('5:30', '-5:30').
    Returns None if `value` is not a valid numeric offset.
    """
    s = value.strip()
    hm = _HM_OFFSET_RE.match(s)
    if hm:
        sign, hh, mm = hm.groups()
        hours = int(hh) + int(mm) / 60
        return -hours if sign == "-" else hours
    if _DECIMAL_OFFSET_RE.match(s):
        return float(s)
    return None


def _coord_display(lat: float, lon: float) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.4f}°{ns}, {abs(lon):.4f}°{ew}"


def resolve_location(
    *,
    city: str | None,
    lat_override: float | None,
    lon_override: float | None,
    tz_override: str | None,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
) -> dict:
    """Resolve a birth location to coordinates, UTC offset, display name, and timezone label.

    `city`, the `lat_override`/`lon_override` pair, and `tz_override` are all optional, but a
    location source (city or coordinates) is required, and a timezone must be determinable
    (from the override, the city, or an error if neither).

    Returns: {"lat", "lon", "tz", "tz_label", "display"}
    """
    if (lat_override is None) != (lon_override is None):
        raise ValueError(
            "Provide both latitude and longitude, or neither. Using only one is ambiguous."
        )

    # Geocode the city (soft): powers the display name, default coords, and default tz.
    # An unknown city is tolerated when coordinates are supplied; otherwise it's fatal.
    geo = None
    if city:
        try:
            geo = lookup_city(city)
        except ValueError:
            if lat_override is None:
                raise

    if lat_override is not None:
        lat, lon = lat_override, lon_override
    elif geo is not None:
        lat, lon = geo["lat"], geo["lon"]
    else:
        raise ValueError("Provide a city, or latitude and longitude.")

    if tz_override:
        tz = parse_offset_hours(tz_override)
        if tz is None:
            raise ValueError(
                f"Invalid timezone override {tz_override!r}. "
                "Use a numeric UTC offset, e.g. 5.5, -4, or 5:30."
            )
        tz_label = tz_override
    elif geo is not None:
        tz = utc_offset(geo["tz_name"], year, month, day, hour, minute)
        tz_label = geo["tz_name"]
    else:
        raise ValueError(
            "Provide a numeric UTC offset (e.g. 5.5) when using coordinates without a city."
        )

    if geo is not None:
        display = geo["display"]
    elif city:
        display = city
    else:
        display = _coord_display(lat, lon)

    return {"lat": lat, "lon": lon, "tz": tz, "tz_label": tz_label, "display": display}
