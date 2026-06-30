# South Indian chart renderer.
#
# Signs are FIXED in a 4×4 grid (Aries at top-left-offset, going clockwise).
# Planets are placed with proportional rendering (x ∝ degree-in-sign) when
# more than 3 occupy a cell, otherwise they are centered.  This mirrors the
# `proportionalPlacement=true` path in single-app/src/lib/SouthIndianChart.svelte.

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

ABBR_SIZE = 12
DEG_SIZE  = 9
ENTRY_H   = 25   # pixels between planet rows (showDegrees=true, compact=false)
PAD_Y     = 6    # vertical padding inside a cell


def degree_minute(longitude: float) -> str:
    """Degrees:minutes within the sign, e.g. 10°25′ → '10:25'."""
    within  = longitude % 30
    deg     = int(within)
    minutes = int((within - deg) * 60 + 1e-9)
    return f"{deg}:{minutes:02d}"


def _style_block() -> str:
    return (
        "  <style>\n"
        f"    .planet-abbr {{ font-size:{ABBR_SIZE}px; font-weight:700; font-family:{CHART_FONT}; }}\n"
        f"    .planet-deg  {{ font-size:{DEG_SIZE}px;  font-weight:500; font-family:{CHART_FONT}; }}\n"
        "  </style>\n"
    )


def _placed_planets(px: float, py: float, entries: list) -> list:
    """Return entries with x, y, anchor, dotX, dotY, reducedFont added."""
    if not entries:
        return []

    cx = px + CELL_SIZE / 2
    cy = py + CELL_SIZE / 2
    n  = len(entries)

    # ── Proportional placement (>3 planets) ─────────────────────────────────
    if n > 3:
        sorted_e = sorted(entries, key=lambda e: e["degVal"])

        max_stack_h = CELL_SIZE - PAD_Y * 2
        entry_h     = min(ENTRY_H, max_stack_h // max(n, 1))
        total_h     = n * entry_h
        start_y     = cy - total_h / 2 + entry_h / 2

        # Cluster planets that are within 3° of each other for stagger offsets
        DEG_CLUSTER = 3
        clusters: list[int] = []
        cid = 0
        for i in range(n):
            if i > 0 and abs(sorted_e[i]["degVal"] - sorted_e[i - 1]["degVal"]) > DEG_CLUSTER:
                cid += 1
            clusters.append(cid)

        cluster_counts: dict[int, int] = {}
        for c in clusters:
            cluster_counts[c] = cluster_counts.get(c, 0) + 1
        cluster_pos: dict[int, int] = {}

        result = []
        for i, e in enumerate(sorted_e):
            c = clusters[i]
            cluster_pos[c] = cluster_pos.get(c, 0) + 1
            total_in = cluster_counts[c]

            raw_x  = px + 14 + min(e["degVal"] / 30, 1) * (CELL_SIZE - 28)
            base_y = start_y + i * entry_h

            stagger = 0.0
            if total_in > 1:
                stagger = (cluster_pos[c] - (total_in + 1) / 2) * (entry_h * 0.2)

            y = round(max(py + PAD_Y, min(py + CELL_SIZE - PAD_Y, base_y + stagger)))

            left_third  = px + CELL_SIZE / 3
            right_third = px + 2 * CELL_SIZE / 3
            if raw_x < left_third:
                anchor, x = "start", px + PAD_Y
            elif raw_x > right_third:
                anchor, x = "end", px + CELL_SIZE - PAD_Y
            else:
                anchor, x = "middle", raw_x

            dot_x = round(max(px + 4, min(px + CELL_SIZE - 4, raw_x)))
            dot_y = round(max(py + PAD_Y, min(py + CELL_SIZE - PAD_Y, base_y)))

            result.append({
                **e,
                "x": round(x), "y": y,
                "anchor": anchor,
                "dotX": dot_x, "dotY": dot_y,
                "reducedFont": True,
            })
        return result

    # ── Simple centered stacking (≤3 planets) ────────────────────────────────
    sorted_e = sorted(entries, key=lambda e: 0 if e.get("isAsc") else 1)
    total_h  = n * ENTRY_H
    start_y  = cy - total_h / 2 + ENTRY_H / 2

    return [
        {**e,
         "x": round(cx), "y": round(start_y + i * ENTRY_H),
         "anchor": "middle", "reducedFont": False}
        for i, e in enumerate(sorted_e)
    ]


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
        placed  = _placed_planets(px, py, entries)

        # Dots for proportional-mode planets (mark exact degree position)
        for pt in placed:
            if pt.get("reducedFont") and pt.get("dotX") is not None:
                out.append(
                    f'  <circle cx="{pt["dotX"]}" cy="{pt["dotY"]}" r="3" '
                    f'fill="{pt["color"]}" stroke="{SURFACE}" stroke-width="1" />\n'
                )

        # Planet labels (abbr + degree)
        for pt in placed:
            x, y    = pt["x"], pt["y"]
            anchor  = pt.get("anchor", "middle")
            retro   = '<tspan dy="-4" font-size="7">R</tspan>' if pt["isRetro"] else ""
            out.append(
                f'  <text x="{x}" y="{y - 7}" text-anchor="{anchor}" '
                f'dominant-baseline="middle" class="planet-abbr" fill="{pt["color"]}">'
                f'{pt["label"]}{retro}</text>\n'
            )
            out.append(
                f'  <text x="{x}" y="{y + 9}" text-anchor="{anchor}" '
                f'dominant-baseline="middle" class="planet-deg" fill="{pt["color"]}">'
                f'{pt["deg"]}</text>\n'
            )

    out.append('</svg>\n')
    return "".join(out)
