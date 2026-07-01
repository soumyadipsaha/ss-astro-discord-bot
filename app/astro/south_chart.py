# South Indian chart renderer.
#
# Signs are FIXED in a 4×4 grid (Aries at top-left-offset, going clockwise).
# Planets within a cell are laid out on a simple grid (1 column for up to 3
# planets, more columns beyond that) with font sizes chosen to fill the cell
# as much as possible without the abbreviation/degree text colliding.

SURFACE  = "#ffffff"
SURFACE2 = "#f4f4f5"
TEXT     = "#09090b"
CHART_FONT = "'Sofia Sans Extra Condensed', sans-serif"

PLANET_STYLE = {
    "Surya":   ("Su", "#f54900"),
    "Chandra": ("Mo", "#0084d1"),
    "Mangala": ("Ma", "#e7000b"),
    "Budha":   ("Me", "#009966"),
    "Guru":    ("Ju", "#d08700"),
    "Shukra":  ("Ve", "#e60076"),
    "Shani":   ("Sa", "#155dfc"),
    "Rahu":    ("Ra", "#45556c"),
    "Ketu":    ("Ke", "#7f22fe"),
}
ASC_LABEL = "As"
ASC_COLOR = "#5ea500"

# ── Geometry ────────────────────────────────────────────────────────────────
# Uniform 4x4 grid of square cells. (A non-uniform grid that shrinks only the
# center box necessarily turns edge cells into rectangles, since each edge
# cell shares a row/column with both an outer and an inner dimension - not
# doable while keeping every cell square.)
CELL_SIZE = 115
ORIGIN    = 10

# sign_index (0 = Aries … 11 = Pisces) → (col, row) in the 4×4 grid
SIGN_CELL = {
    0:  (1, 0),   # Aries
    1:  (2, 0),   # Taurus
    2:  (3, 0),   # Gemini
    3:  (3, 1),   # Cancer
    4:  (3, 2),   # Leo
    5:  (3, 3),   # Virgo
    6:  (2, 3),   # Libra
    7:  (1, 3),   # Scorpio
    8:  (0, 3),   # Sagittarius
    9:  (0, 2),   # Capricorn
    10: (0, 1),   # Aquarius
    11: (0, 0),   # Pisces
}

PAD_X = 6   # horizontal padding inside a cell
PAD_Y = 6   # vertical padding inside a cell

# Adaptive font sizing, same approach as north_chart.py: the degree string
# ("27:04", 5 chars) is wider than the 2-char abbreviation and is usually
# the thing that overlaps, so size both to the space actually available in
# the grid slot and only drop the degree line for genuinely dense cells.
CHAR_WIDTH_RATIO = 0.58  # approx average glyph width as a fraction of font-size
DEG_CHARS = 5    # "DD:MM"
ABBR_CHARS = 2.4  # 2-letter label + retrograde marker headroom
ABBR_SIZE_MAX = 22
DEG_SIZE_MAX = 13
ABBR_SIZE_MIN = 9
DEG_SIZE_MIN = 7


def degree_minute(longitude: float) -> str:
    """Degrees:minutes within the sign, e.g. 10°25′ → '10:25'."""
    within  = longitude % 30
    deg     = int(within)
    minutes = int((within - deg) * 60 + 1e-9)
    return f"{deg}:{minutes:02d}"


def _style_block() -> str:
    return (
        "  <style>\n"
        f"    .planet-abbr {{ font-weight:700; font-family:{CHART_FONT}; }}\n"
        f"    .planet-deg  {{ font-weight:500; font-family:{CHART_FONT}; }}\n"
        "  </style>\n"
    )


def _fit_sizes(cell_w: float, cell_h: float) -> tuple[float, float, bool]:
    """Return (abbr_size, deg_size, show_deg) that fit a cell_w x cell_h slot."""
    abbr_size = min(ABBR_SIZE_MAX, cell_w / (ABBR_CHARS * CHAR_WIDTH_RATIO))
    deg_size = min(DEG_SIZE_MAX, cell_w / (DEG_CHARS * CHAR_WIDTH_RATIO))
    height_needed = (abbr_size + deg_size) * 0.8
    if height_needed > cell_h:
        scale = cell_h / height_needed
        abbr_size *= scale
        deg_size *= scale
    if deg_size < DEG_SIZE_MIN:
        abbr_size = min(ABBR_SIZE_MAX, cell_w / (ABBR_CHARS * CHAR_WIDTH_RATIO), cell_h * 0.8)
        return max(abbr_size, ABBR_SIZE_MIN), 0, False
    return max(abbr_size, ABBR_SIZE_MIN), max(deg_size, DEG_SIZE_MIN), True


def _placed_planets(px: float, py: float, w: float, h: float, entries: list) -> list:
    """Lay out entries on a simple grid within a w x h cell, sized to fit."""
    if not entries:
        return []

    sorted_e = sorted(entries, key=lambda e: (0 if e.get("isAsc") else 1, e["degVal"]))
    n = len(sorted_e)
    cols = 1 if n <= 3 else (2 if n <= 8 else 3)
    rows = -(-n // cols)  # ceil division

    avail_w = w - 2 * PAD_X
    avail_h = h - 2 * PAD_Y
    cell_w = avail_w / cols
    cell_h = avail_h / rows
    abbr_size, deg_size, show_deg = _fit_sizes(cell_w, cell_h)

    cx = px + w / 2
    result = []
    for r in range(rows):
        row_entries = sorted_e[r * cols:(r + 1) * cols]
        row_n = len(row_entries)
        row_y = py + PAD_Y + cell_h * r + cell_h / 2
        start_x = cx - (row_n - 1) / 2 * cell_w
        for j, e in enumerate(row_entries):
            result.append({
                **e,
                "x": round(start_x + j * cell_w), "y": round(row_y),
                "anchor": "middle",
                "abbrSize": abbr_size, "degSize": deg_size, "showDeg": show_deg,
            })
    return result


def render_south_chart(result: dict) -> str:
    """Render a build_chart() result dict as a South Indian SVG chart string."""
    bodies      = result["bodies"]
    asc         = bodies[0]
    asc_sign_idx = asc["sign_index"]   # 0–11

    # ── Group planets by sign (fixed, not by house) ─────────────────────────
    by_sign: dict[int, list] = {
        asc_sign_idx: [{
            "label": ASC_LABEL, "color": ASC_COLOR,
            "deg": degree_minute(asc["longitude"]),
            "degVal": asc["longitude"] % 30,
            "isRetro": False, "isAsc": True,
        }]
    }

    for body in bodies[1:]:
        sanskrit = body["name"].split(" ", 1)[0]
        if sanskrit not in PLANET_STYLE:
            continue
        label, color = PLANET_STYLE[sanskrit]
        si = body["sign_index"]
        by_sign.setdefault(si, []).append({
            "label": label, "color": color,
            "deg": degree_minute(body["longitude"]),
            "degVal": body["longitude"] % 30,
            "isRetro": bool(body.get("retrograde")), "isAsc": False,
        })

    # ── SVG output ──────────────────────────────────────────────────────────
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" '
        'shape-rendering="geometricPrecision">\n',
        _style_block(),
    ]

    # Outer border
    out.append(
        f'  <rect x="10" y="10" width="460" height="460" '
        f'fill="{SURFACE}" stroke="{TEXT}" stroke-width="1.5" />\n'
    )

    # 4×4 grid lines (3 vertical + 3 horizontal inner lines)
    for i in [1, 2, 3]:
        x = ORIGIN + i * CELL_SIZE
        out.append(f'  <line x1="{x}" y1="10" x2="{x}" y2="470" stroke="{TEXT}" stroke-width="1" />\n')
        y = ORIGIN + i * CELL_SIZE
        out.append(f'  <line x1="10" y1="{y}" x2="470" y2="{y}" stroke="{TEXT}" stroke-width="1" />\n')

    # Center 2×2 box (cols 1–2, rows 1–2 → x 125–355, y 125–355)
    out.append(
        f'  <rect x="125" y="125" width="230" height="230" '
        f'fill="{SURFACE2}" stroke="{TEXT}" stroke-width="1" />\n'
    )

    # ── Render each sign cell ────────────────────────────────────────────────
    for si in range(12):
        col, row = SIGN_CELL[si]
        px = ORIGIN + col * CELL_SIZE
        py = ORIGIN + row * CELL_SIZE

        # Lagna corner diagonal
        if si == asc_sign_idx:
            out.append(
                f'  <line x1="{px}" y1="{py + 44}" x2="{px + 44}" y2="{py}" '
                f'stroke="{ASC_COLOR}" stroke-width="2" stroke-linecap="round" />\n'
            )

        entries = by_sign.get(si, [])
        placed  = _placed_planets(px, py, CELL_SIZE, CELL_SIZE, entries)

        # Planet labels (abbr + degree)
        for pt in placed:
            x, y = pt["x"], pt["y"]
            anchor = pt["anchor"]
            abbr_size, deg_size, show_deg = pt["abbrSize"], pt["degSize"], pt["showDeg"]
            retro = (
                f'<tspan dy="{-abbr_size * 0.35:.1f}" font-size="{abbr_size * 0.55:.1f}">R</tspan>'
                if pt["isRetro"] else ""
            )
            if show_deg:
                abbr_y, deg_y = y - deg_size * 0.5 - 1, y + abbr_size * 0.32
            else:
                abbr_y = y
            out.append(
                f'  <text x="{x}" y="{abbr_y:.1f}" text-anchor="{anchor}" '
                f'dominant-baseline="middle" class="planet-abbr" style="font-size:{abbr_size:.1f}px" '
                f'fill="{pt["color"]}">{pt["label"]}{retro}</text>\n'
            )
            if show_deg:
                out.append(
                    f'  <text x="{x}" y="{deg_y:.1f}" text-anchor="{anchor}" '
                    f'dominant-baseline="middle" class="planet-deg" style="font-size:{deg_size:.1f}px" '
                    f'fill="{pt["color"]}">{pt["deg"]}</text>\n'
                )

    out.append('</svg>\n')
    return "".join(out)
