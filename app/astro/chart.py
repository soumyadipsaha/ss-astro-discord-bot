from datetime import datetime, timedelta

import swisseph as swe

from .constants import GRAHAS, NAKSHATRAS, SIGNS
from .ephemeris import init_ephe

NAK_WIDTH = 360.0 / 27.0


def local_to_jd(date_str: str, time_str: str, tz: float):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    ut = dt - timedelta(hours=tz)
    ut_hour = ut.hour + ut.minute / 60.0 + ut.second / 3600.0
    jd = swe.julday(ut.year, ut.month, ut.day, ut_hour, swe.GREG_CAL)
    return jd, ut


def ayanamsa(jd: float) -> float:
    return swe.get_ayanamsa_ex_ut(jd, swe.FLG_SWIEPH)[1]


def sign_of(lon: float) -> int:
    return int((lon % 360) // 30)


def nak_of(lon: float) -> tuple[int, int]:
    lon = lon % 360
    idx = int(lon // NAK_WIDTH)
    pada = int((lon % NAK_WIDTH) / (NAK_WIDTH / 4.0)) + 1
    return idx, pada


def fmt_degree(lon: float) -> str:
    lon = lon % 360
    sign_idx = sign_of(lon)
    within = lon - sign_idx * 30
    deg = int(within)
    rem = (within - deg) * 60
    minutes = int(rem)
    seconds = int(round((rem - minutes) * 60))
    if seconds == 60:
        seconds = 0
        minutes += 1
    if minutes == 60:
        minutes = 0
        deg += 1
    return f"{deg:02d}\N{DEGREE SIGN}{minutes:02d}'{seconds:02d}\""


def graha_positions(jd: float) -> list[dict]:
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH
    out: list[dict] = []
    for sanskrit, english, pid in GRAHAS:
        xx, _flag, serr = swe.calc_ut(jd, pid, flags)
        lon, _lat, _dist, lon_speed = xx[0], xx[1], xx[2], xx[3]
        out.append({
            "sanskrit": sanskrit,
            "english": english,
            "longitude": lon % 360,
            "speed": lon_speed,
            "retrograde": lon_speed < 0,
            "error": serr,
        })
    rahu = out[-1]
    out.append({
        "sanskrit": "Ketu",
        "english": "South Node",
        "longitude": (rahu["longitude"] + 180.0) % 360,
        "speed": rahu["speed"],
        "retrograde": rahu["speed"] < 0,
        "error": None,
    })
    return out


def houses(jd: float, lat: float, lon: float, chalit: bool) -> dict:
    cusps, ascmc = swe.houses(jd, lat, lon, b"O")
    ayan = ayanamsa(jd)
    cusps_sid = [(c - ayan) % 360 for c in cusps[1:13]]
    asc = (ascmc[0] - ayan) % 360
    mc = (ascmc[1] - ayan) % 360
    result = {"ascendant": asc, "midheaven": mc, "cusps": cusps_sid}
    if chalit:
        result["bhava_starts"] = sripati_starts(cusps_sid)
    return result


def circ_mid(a: float, b: float) -> float:
    diff = ((b - a + 180) % 360) - 180
    return (a + diff / 2.0) % 360


def sripati_starts(cusps: list[float]) -> list[float]:
    n = len(cusps)
    return [circ_mid(cusps[(i - 1) % n], cusps[i]) for i in range(n)]


def bhava_of(longitude: float, starts: list[float]) -> int:
    lon = longitude % 360
    n = len(starts)
    for i in range(n):
        s = starts[i]
        e = starts[(i + 1) % n]
        if s <= e:
            if s <= lon < e:
                return i + 1
        elif lon >= s or lon < e:
            return i + 1
    return n


def build_chart(
    date_str: str,
    time_str: str,
    lat: float,
    lon: float,
    tz: float,
    chalit: bool = False,
    ayanamsa_offset_arcmin: float = 0.0,
) -> dict:
    if not (-90.0 <= lat <= 90.0):
        raise ValueError("Latitude must be between -90 and 90.")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError("Longitude must be between -180 and 180.")
    if not (-12.0 <= tz <= 14.0):
        raise ValueError("Timezone offset must be between -12 and 14.")

    init_ephe()
    offset_deg = ayanamsa_offset_arcmin / 60.0
    jd, ut = local_to_jd(date_str, time_str, tz)
    ayan_lahiri = ayanamsa(jd)
    ayan_custom = ayan_lahiri + offset_deg
    h = houses(jd, lat, lon, chalit)
    grahas = graha_positions(jd)

    def shift(longitude: float) -> float:
        return (longitude - offset_deg) % 360

    asc = shift(h["ascendant"])
    cusps = [shift(c) for c in h["cusps"]]
    mc = shift(h["midheaven"])
    starts = [shift(s) for s in h["bhava_starts"]] if h.get("bhava_starts") else None

    def describe(name: str, longitude: float, retrograde: bool | None = None):
        sign_idx = sign_of(longitude)
        nak_idx, pada = nak_of(longitude)
        return {
            "name": name,
            "longitude": longitude,
            "sign_index": sign_idx,
            "sign": SIGNS[sign_idx][0],
            "sign_sanskrit": SIGNS[sign_idx][1],
            "symbol": SIGNS[sign_idx][2],
            "nakshatra": NAKSHATRAS[nak_idx],
            "nakshatra_index": nak_idx,
            "pada": pada,
            "retrograde": retrograde,
        }

    bodies = [describe("Lagna (Ascendant)", asc)]
    for g in grahas:
        glong = shift(g["longitude"])
        body = describe(f"{g['sanskrit']} ({g['english']})", glong, g["retrograde"])
        if chalit and starts is not None:
            body["bhava"] = bhava_of(glong, starts)
        bodies.append(body)
    if chalit and starts is not None:
        bodies[0]["bhava"] = bhava_of(asc, starts)

    label = "Lahiri" if offset_deg == 0 else f"Lahiri {ayanamsa_offset_arcmin:+g}\u2032"

    return {
        "julian_day": jd,
        "ut": ut.isoformat(),
        "ayanamsa": ayan_custom,
        "ayanamsa_label": label,
        "lat": lat,
        "lon": lon,
        "tz": tz,
        "ascendant": asc,
        "midheaven": mc,
        "cusps": cusps,
        "bhava_starts": starts,
        "chalit": chalit,
        "bodies": bodies,
    }
