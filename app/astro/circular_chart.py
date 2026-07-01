# Circular (Chakra/wheel) chart renderer.
#
# Geometry, angle math and styling are ported from
# single-app/src/lib/CircularChart.svelte. Color tokens come from
# single-app/src/app.css (:root) and planet colors from
# single-app/src/lib/colors.ts, matching north_chart.py/south_chart.py.
#
# Zodiac signs are labelled with 2-letter abbreviations instead of the
# Svelte source's unicode glyphs (♈♉♊…), since resvg + the bundled
# condensed font don't reliably render those glyphs.

import math

SURFACE = "#ffffff"
SURFACE2 = "#f4f4f5"
TEXT = "#09090b"
CHART_FONT = "'Sofia Sans Extra Condensed', sans-serif"

PLANET_STYLE = {
    "Surya": ("Su", "#f54900"),
    "Chandra": ("Mo", "#0084d1"),
    "Mangala": ("Ma", "#e7000b"),
    "Budha": ("Me", "#009966"),
    "Guru": ("Ju", "#d08700"),
    "Shukra": ("Ve", "#e60076"),
    "Shani": ("Sa", "#155dfc"),
    "Rahu": ("Ra", "#45556c"),
    "Ketu": ("Ke", "#7f22fe"),
}
ASC_LABEL = "As"
ASC_COLOR = "#5ea500"

SIGN_ABBR = ["Ar", "Ta", "Ge", "Cn", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

# ── Geometry (viewBox 480x480, center 240,240) ───────────────────────────────
CX = CY = 240
R_OUTER = 238
R_SIGN_IN = 192
R_BHAVA_IN = 85
R_DOT = 183
R_BHAVA_NUM = 172
R_PLANET = 140
R_PLANET_ALT = 110
R_CENTER = 62

ABBR_SIZE = 14
DEG_SIZE = 10
RETRO_SIZE = 9
CROWD_THRESHOLD_DEG = 14.0


def degree_minute(longitude: float) -> str:
    """Within-sign degrees:minutes, e.g. 10°25' -> '10:25'."""
    within = longitude % 30
    deg = int(within)
    minutes = int((within - deg) * 60 + 1e-9)
    return f"{deg}:{minutes:02d}"


def _circ_diff(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _circ_mid(a: float, b: float) -> float:
    span = (b - a) % 360
    return (a + span / 2) % 360


def _lon_to_angle(lon: float, asc_lon: float) -> float:
    """Ecliptic longitude -> SVG angle, clockwise from 12 o'clock.

    Ascendant sits at 270° (9 o'clock/left); increasing longitude runs
    counterclockwise, matching standard astrological wheel convention.
    """
    return ((270 + asc_lon - lon) % 360 + 360) % 360


def _lon_to_xy(lon: float, r: float, asc_lon: float) -> tuple[float, float]:
    rad = math.radians(_lon_to_angle(lon, asc_lon))
    return CX + r * math.sin(rad), CY - r * math.cos(rad)


def _sector_path(start_lon: float, end_lon: float, r_out: float, r_in: float, asc_lon: float) -> str:
    span = (end_lon - start_lon) % 360
    large = 1 if span > 180 else 0
    p1o = _lon_to_xy(start_lon, r_out, asc_lon)
    p2o = _lon_to_xy(end_lon, r_out, asc_lon)
    p2i = _lon_to_xy(end_lon, r_in, asc_lon)
    p1i = _lon_to_xy(start_lon, r_in, asc_lon)
    return (
        f"M {p1o[0]:.2f} {p1o[1]:.2f} "
        f"A {r_out} {r_out} 0 {large} 0 {p2o[0]:.2f} {p2o[1]:.2f} "
        f"L {p2i[0]:.2f} {p2i[1]:.2f} "
        f"A {r_in} {r_in} 0 {large} 1 {p1i[0]:.2f} {p1i[1]:.2f} Z"
    )


def _style_block() -> str:
    return (
        "  <style>\n"
        f"    .sign-abbr {{ font-size:15px; font-weight:700; font-family:{CHART_FONT}; fill:{TEXT}; }}\n"
        f"    .bhava-num {{ font-size:13px; font-weight:700; font-family:{CHART_FONT}; fill:{TEXT}; }}\n"
        f"    .planet-label {{ font-size:{ABBR_SIZE}px; font-weight:400; font-family:{CHART_FONT}; }}\n"
        f"    .planet-deg {{ font-size:{DEG_SIZE}px; font-weight:500; font-family:{CHART_FONT}; }}\n"
        f"    .angle-label {{ font-size:9px; font-weight:700; font-family:{CHART_FONT}; letter-spacing:0.03em; }}\n"
        "  </style>\n"
    )


def _bhava_segments(result: dict, lagna_sign_idx: int) -> list[dict]:
    starts = result.get("bhava_starts")
    if result.get("chalit") and starts:
        segs = []
        for i in range(12):
            s, e = starts[i], starts[(i + 1) % 12]
            segs.append({"start": s, "end": e, "mid": _circ_mid(s, e), "bhava": i + 1})
        return segs
    segs = []
    for k in range(1, 13):
        sidx = (lagna_sign_idx + k - 1) % 12
        s = sidx * 30.0
        segs.append({"start": s, "end": s + 30.0, "mid": s + 15.0, "bhava": k})
    return segs


def render_circular_chart(result: dict) -> str:
    """Render a build_chart() result dict as a circular (wheel) SVG chart string."""
    bodies = result["bodies"]
    asc_body = bodies[0]
    asc_lon = asc_body["longitude"]
    lagna_sign_idx = asc_body["sign_index"]
    chalit = result["chalit"]

    def xy(lon, r):
        return _lon_to_xy(lon, r, asc_lon)

    rashi_segs = [{"start": i * 30.0, "end": (i + 1) * 30.0, "mid": i * 30.0 + 15.0, "sign": i} for i in range(12)]
    bhava_segs = _bhava_segments(result, lagna_sign_idx)

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" '
        'shape-rendering="geometricPrecision">\n',
        _style_block(),
    ]

    # Opaque background for the whole canvas (corners outside the wheel,
    # plus everything inside the sign ring), so the chart doesn't show a
    # transparent/dark hole or corners on dark backgrounds (e.g. Discord's
    # dark theme) - matches north_chart.py/south_chart.py, which are fully
    # opaque squares.
    out.append(f'  <rect x="0" y="0" width="480" height="480" fill="{SURFACE}" stroke="none" />\n')

    # Sign ring wedges (alternating fill)
    for seg in rashi_segs:
        fill = SURFACE if seg["sign"] % 2 == 0 else SURFACE2
        path = _sector_path(seg["start"], seg["end"], R_OUTER, R_SIGN_IN, asc_lon)
        out.append(f'  <path d="{path}" fill="{fill}" stroke="none" />\n')

    # Bhava ring + center background
    out.append(f'  <circle cx="{CX}" cy="{CY}" r="{R_BHAVA_IN - 1.5}" fill="{SURFACE}" stroke="none" />\n')
    out.append(f'  <circle cx="{CX}" cy="{CY}" r="{R_CENTER}" fill="{SURFACE2}" stroke="{TEXT}" stroke-width="1" />\n')

    # Ring borders
    out.append(f'  <circle cx="{CX}" cy="{CY}" r="{R_OUTER}" fill="none" stroke="{TEXT}" stroke-width="1.5" />\n')
    out.append(f'  <circle cx="{CX}" cy="{CY}" r="{R_SIGN_IN}" fill="none" stroke="{TEXT}" stroke-width="1" />\n')
    out.append(f'  <circle cx="{CX}" cy="{CY}" r="{R_BHAVA_IN}" fill="none" stroke="{TEXT}" stroke-width="1.5" />\n')

    # Degree tick marks (every 5°, skipping sign boundaries)
    for lon in range(0, 360, 5):
        if lon % 30 == 0:
            continue
        major = lon % 10 == 0
        tick_r = R_OUTER - 9 if major else R_OUTER - 5
        width = 1 if major else 0.6
        p1 = xy(lon, R_OUTER)
        p2 = xy(lon, tick_r)
        out.append(
            f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="{TEXT}" stroke-width="{width}" opacity="0.55" />\n'
        )

    # Sign boundary radial lines
    for seg in rashi_segs:
        p1 = xy(seg["start"], R_SIGN_IN - 1)
        p2 = xy(seg["start"], R_OUTER + 1)
        out.append(
            f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="{TEXT}" stroke-width="1.5" />\n'
        )

    # Bhava boundary radial lines. Whole-sign houses share their boundaries
    # with sign cusps (already drawn above), so only the short segment
    # within the bhava ring itself is needed; Porphyry cusps differ from
    # sign boundaries and so are drawn full-length, crossing the sign ring.
    for seg in bhava_segs:
        if chalit:
            p1 = xy(seg["start"], R_BHAVA_IN - 4)
            p2 = xy(seg["start"], R_OUTER + 1)
        else:
            p1 = xy(seg["start"], R_BHAVA_IN - 4)
            p2 = xy(seg["start"], R_SIGN_IN + 1)
        out.append(
            f'  <line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="{TEXT}" stroke-width="1" />\n'
        )

    # Sign abbreviations
    for seg in rashi_segs:
        pos = xy(seg["mid"], (R_OUTER + R_SIGN_IN) / 2)
        out.append(
            f'  <text x="{pos[0]:.2f}" y="{pos[1]:.2f}" text-anchor="middle" '
            f'dominant-baseline="middle" class="sign-abbr">{SIGN_ABBR[seg["sign"]]}</text>\n'
        )

    # Bhava numbers
    for seg in bhava_segs:
        pos = xy(seg["mid"], R_BHAVA_NUM)
        out.append(
            f'  <text x="{pos[0]:.2f}" y="{pos[1]:.2f}" text-anchor="middle" '
            f'dominant-baseline="middle" class="bhava-num">{seg["bhava"]}</text>\n'
        )

    # Ascendant marker
    if chalit:
        mc = result["midheaven"]
        ic = (mc + 180) % 360
        dsc = (asc_lon + 180) % 360
        for lon_val, label in ((asc_lon, "ASC"), (dsc, "DSC"), (mc, "MC"), (ic, "IC")):
            p1 = (CX, CY)
            p2 = xy(lon_val, R_OUTER + 1)
            out.append(
                f'  <line x1="{p1[0]}" y1="{p1[1]}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
                f'stroke="{ASC_COLOR}" stroke-width="1.5" opacity="0.75" />\n'
            )
            lp = xy(lon_val, R_CENTER + 14)
            out.append(
                f'  <text x="{lp[0]:.2f}" y="{lp[1]:.2f}" text-anchor="middle" dominant-baseline="middle" '
                f'class="angle-label" fill="{ASC_COLOR}">{label}</text>\n'
            )
    else:
        p2 = xy(asc_lon, R_OUTER + 1)
        out.append(
            f'  <line x1="{CX}" y1="{CY}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="{ASC_COLOR}" stroke-width="1.5" opacity="0.75" />\n'
        )

    # Planets (+ ascendant): sort by longitude, toggling label radius when
    # two consecutive entries fall within CROWD_THRESHOLD_DEG of each other
    # so their labels don't overlap.
    planets = [{
        "lon": asc_lon, "label": ASC_LABEL, "color": ASC_COLOR,
        "isRetro": False, "deg": degree_minute(asc_lon),
    }]
    for body in bodies[1:]:
        sanskrit = body["name"].split(" ", 1)[0]
        if sanskrit not in PLANET_STYLE:
            continue
        label, color = PLANET_STYLE[sanskrit]
        planets.append({
            "lon": body["longitude"], "label": label, "color": color,
            "isRetro": bool(body.get("retrograde")),
            "deg": degree_minute(body["longitude"]),
        })
    planets.sort(key=lambda p: p["lon"])

    alt = False
    for i, p in enumerate(planets):
        if i > 0 and _circ_diff(p["lon"], planets[i - 1]["lon"]) < CROWD_THRESHOLD_DEG:
            alt = not alt
        else:
            alt = False
        p["r"] = R_PLANET_ALT if alt else R_PLANET

    for p in planets:
        dot = xy(p["lon"], R_DOT)
        label_pos = xy(p["lon"], p["r"])
        conn = xy(p["lon"], p["r"] + 4)
        out.append(
            f'  <line x1="{dot[0]:.2f}" y1="{dot[1]:.2f}" x2="{conn[0]:.2f}" y2="{conn[1]:.2f}" '
            f'stroke="{p["color"]}" stroke-width="0.6" opacity="0.35" />\n'
        )
        out.append(f'  <circle cx="{dot[0]:.2f}" cy="{dot[1]:.2f}" r="3" fill="{p["color"]}" stroke="{SURFACE}" stroke-width="1" />\n')
        retro = f'<tspan dy="-4" font-size="{RETRO_SIZE}">R</tspan>' if p["isRetro"] else ""
        out.append(
            f'  <text x="{label_pos[0]:.2f}" y="{label_pos[1] - 5:.2f}" text-anchor="middle" '
            f'dominant-baseline="middle" class="planet-label" fill="{p["color"]}">{p["label"]}{retro}</text>\n'
        )
        out.append(
            f'  <text x="{label_pos[0]:.2f}" y="{label_pos[1] + 8:.2f}" text-anchor="middle" '
            f'dominant-baseline="middle" class="planet-deg" fill="{p["color"]}" opacity="0.75">{p["deg"]}</text>\n'
        )

    out.append('</svg>\n')
    return "".join(out)
