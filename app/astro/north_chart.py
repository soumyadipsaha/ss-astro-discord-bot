# North Indian chart renderer.
#
# Geometry, placement and styling are ported from
# single-app/src/lib/NewNIChart.svelte. Color tokens come from
# single-app/src/app.css (:root) and planet colors from
# single-app/src/lib/colors.ts. There is no jyotichart dependency.

# ── Theme tokens (single-app/src/app.css, :root defaults) ──────────────────
SURFACE = "#ffffff"
TEXT = "#09090b"
CHART_FONT = "'JetBrains Mono', 'Fira Mono', ui-monospace, monospace"

# ── Planet styles (single-app/src/lib/{colors,planets}.ts) ──────────────────
# sanskrit prefix -> (short label, color)
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

# ── Geometry (viewBox 480x480) ──────────────────────────────────────────────
POLYGONS = {
    1: "240,10 355,125 240,240 125,125",
    2: "10,10 240,10 125,125",
    3: "10,10 125,125 10,240",
    4: "10,240 125,125 240,240 125,355",
    5: "10,240 125,355 10,470",
    6: "10,470 125,355 240,470",
    7: "240,240 355,355 240,470 125,355",
    8: "240,470 355,355 470,470",
    9: "470,470 355,355 470,240",
    10: "240,240 355,125 470,240 355,355",
    11: "470,240 355,125 470,10",
    12: "470,10 355,125 240,10",
}


def _parse_polygon(s):
    return [tuple(float(n) for n in pt.split(",")) for pt in s.split()]


POLYGON_PTS = {h: _parse_polygon(s) for h, s in POLYGONS.items()}

LABEL_POS = {
    1: (240, 215), 2: (123, 104), 3: (102, 120), 4: (215, 240),
    5: (102, 360), 6: (123, 376), 7: (240, 265), 8: (357, 376),
    9: (378, 360), 10: (265, 240), 11: (378, 120), 12: (357, 104),
}

PLANET_SPACING = 30
OVERFLOW_H = 21

KENDRA_ROWS = {
    1: [
        {"y": 141, "xMin": 141, "xMax": 339, "max": 6},
        {"y": 102, "xMin": 148, "xMax": 332, "max": 6},
        {"y": 165, "xMin": 165, "xMax": 315, "max": 5},
        {"y": 192, "xMin": 196, "xMax": 284, "max": 3},
    ],
    4: [
        {"y": 240, "xMin": 15, "xMax": 195, "max": 6},
        {"y": 209, "xMin": 41, "xMax": 203, "max": 5},
        {"y": 269, "xMin": 41, "xMax": 203, "max": 5},
    ],
    7: [
        {"y": 345, "xMin": 141, "xMax": 339, "max": 7},
        {"y": 381, "xMin": 149, "xMax": 331, "max": 6},
        {"y": 301, "xMin": 165, "xMax": 315, "max": 4},
        {"y": 288, "xMin": 196, "xMax": 284, "max": 3},
    ],
    10: [
        {"y": 240, "xMin": 285, "xMax": 465, "max": 6},
        {"y": 209, "xMin": 277, "xMax": 439, "max": 5},
        {"y": 269, "xMin": 277, "xMax": 439, "max": 5},
    ],
}

SLOTS = {
    2: [(107, 39), (144, 39), (71, 39), (180, 39), (104, 68), (146, 68)],
    6: [(104, 454), (146, 454), (71, 454), (180, 454), (94, 426), (154, 426)],
    8: [(318, 454), (360, 454), (277, 454), (402, 454), (313, 426), (395, 426)],
    12: [(329, 39), (365, 39), (292, 39), (402, 39), (324, 68), (381, 68)],
    3: [(31, 110), (31, 140), (31, 81), (31, 169), (57, 115), (57, 83), (57, 148)],
    5: [(31, 314), (31, 344), (31, 285), (31, 373), (57, 355), (57, 315), (57, 390)],
    9: [(449, 335), (449, 364), (449, 306), (449, 394), (423, 355), (423, 315), (423, 381)],
    11: [(449, 105), (449, 134), (449, 76), (449, 164), (423, 113), (423, 83), (423, 139)],
}


def point_in_convex_polygon(x, y, pts):
    pos = neg = 0
    n = len(pts)
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        cross = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
        if cross > 0:
            pos += 1
        elif cross < 0:
            neg += 1
    return pos == 0 or neg == 0


def clamp_to_polygon(x, y, pts):
    if point_in_convex_polygon(x, y, pts):
        return (round(x), round(y))
    bx, by, best = x, y, float("inf")
    n = len(pts)
    for i in range(n):
        ax, ay = pts[i]
        bx2, by2 = pts[(i + 1) % n]
        dx, dy = bx2 - ax, by2 - ay
        len2 = dx * dx + dy * dy
        if len2 == 0:
            continue
        t = ((x - ax) * dx + (y - ay) * dy) / len2
        t = max(0.0, min(1.0, t))
        cx, cy = ax + t * dx, ay + t * dy
        d = (cx - x) ** 2 + (cy - y) ** 2
        if d < best:
            best, bx, by = d, cx, cy
    return (round(bx), round(by))


def _asc_first(entries):
    if any(e.get("isAsc") for e in entries):
        return sorted(entries, key=lambda e: 0 if e.get("isAsc") else 1)
    return list(entries)


def placed_kendra(h, entries):
    rows = KENDRA_ROWS[h]
    sorted_e = _asc_first(entries)
    result = []
    i = 0
    for row in rows:
        if i >= len(sorted_e):
            break
        count = min(row["max"], len(sorted_e) - i)
        cx = (row["xMin"] + row["xMax"]) / 2
        start_x = cx - ((count - 1) / 2) * PLANET_SPACING
        for j in range(count):
            result.append({**sorted_e[i], "x": round(start_x + j * PLANET_SPACING), "y": row["y"]})
            i += 1
    if i < len(sorted_e):
        last = rows[-1]
        cx = round((last["xMin"] + last["xMax"]) / 2)
        oy = last["y"]
        while i < len(sorted_e):
            oy += OVERFLOW_H
            result.append({**sorted_e[i], "x": cx, "y": oy})
            i += 1
    return result


def placed_planets(h, entries):
    if not entries:
        return []
    if h in (1, 4, 7, 10):
        return placed_kendra(h, entries)
    sorted_e = _asc_first(entries)
    slots = SLOTS[h]
    result = []
    for i, e in enumerate(sorted_e):
        if i < len(slots):
            x, y = slots[i]
            result.append({**e, "x": x, "y": y})
        else:
            lx, ly = slots[-1]
            result.append({**e, "x": lx, "y": ly + (i - len(slots) + 1) * OVERFLOW_H})
    return result


# ── Data helpers ────────────────────────────────────────────────────────────
def degree_minute(longitude: float) -> str:
    """Within-sign degrees/minutes, truncated (not rounded): 10°25'37" -> 10°25′."""
    within = longitude % 30
    deg = int(within)
    minutes = int((within - deg) * 60 + 1e-9)
    return f"{deg}\N{DEGREE SIGN}{minutes:02d}\N{PRIME}"


def _house_of(body: dict, asc_sign_index: int, chalit: bool) -> int:
    if chalit and body.get("bhava"):
        return body["bhava"]
    return ((body["sign_index"] - asc_sign_index) % 12) + 1


def _style_block() -> str:
    return (
        "  <style>\n"
        f"    .sign-num {{ font-size:22px; font-weight:700; font-family:{CHART_FONT}; fill:{TEXT}; }}\n"
        f"    .planet-abbr {{ font-size:11px; font-weight:400; font-family:{CHART_FONT}; fill:#ffffff; }}\n"
        f"    .planet-deg {{ font-size:7px; font-weight:500; font-family:{CHART_FONT}; fill:#ffffff; }}\n"
        "  </style>\n"
    )


def render_north_chart(result: dict) -> str:
    """Render a build_chart() result dict as a North Indian SVG chart string."""
    bodies = result["bodies"]
    asc = bodies[0]
    asc_idx = asc["sign_index"]
    chalit = result["chalit"]

    by_house = {1: [{
        "label": ASC_LABEL, "color": ASC_COLOR,
        "degree": degree_minute(asc["longitude"]),
        "isRetro": False, "isAsc": True,
    }]}
    for body in bodies[1:]:
        sanskrit = body["name"].split(" ", 1)[0]
        if sanskrit not in PLANET_STYLE:
            continue
        label, color = PLANET_STYLE[sanskrit]
        by_house.setdefault(_house_of(body, asc_idx, chalit), []).append({
            "label": label, "color": color,
            "degree": degree_minute(body["longitude"]),
            "isRetro": bool(body.get("retrograde")), "isAsc": False,
        })

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" '
        'shape-rendering="geometricPrecision">\n',
        _style_block(),
    ]

    for h in range(1, 13):
        out.append(f'  <polygon points="{POLYGONS[h]}" fill="{SURFACE}" stroke="none" />\n')
    out.append(f'  <g fill="none" stroke="{TEXT}" stroke-width="1.5" stroke-linejoin="round">\n')
    out.append('    <rect x="10" y="10" width="460" height="460" />\n')
    out.append('    <path d="M240,10 L470,240 L240,470 L10,240 Z" />\n')
    out.append('    <path d="M10,10 L240,240 L470,470" />\n')
    out.append('    <path d="M470,10 L240,240 L10,470" />\n')
    out.append('  </g>\n')

    for h in range(1, 13):
        lx, ly = LABEL_POS[h]
        signnum = ((asc_idx + h - 1) % 12) + 1
        out.append(
            f'  <text x="{lx}" y="{ly}" text-anchor="middle" dominant-baseline="middle" '
            f'class="sign-num">{signnum}</text>\n'
        )
        for pt in placed_planets(h, by_house.get(h, [])):
            x, y = clamp_to_polygon(pt["x"], pt["y"], POLYGON_PTS[h])
            out.append(
                f'  <rect x="{x - 13}" y="{y - 12}" width="26" height="24" rx="3" '
                f'fill="{pt["color"]}" opacity="0.75" />\n'
            )
            retro = '<tspan dy="-4" font-size="7">R</tspan>' if pt["isRetro"] else ""
            out.append(
                f'  <text x="{x}" y="{y - 4}" text-anchor="middle" dominant-baseline="middle" '
                f'class="planet-abbr">{pt["label"]}{retro}</text>\n'
            )
            out.append(
                f'  <text x="{x}" y="{y + 5}" text-anchor="middle" dominant-baseline="middle" '
                f'class="planet-deg">{pt["degree"]}</text>\n'
            )

    out.append('</svg>\n')
    return "".join(out)
