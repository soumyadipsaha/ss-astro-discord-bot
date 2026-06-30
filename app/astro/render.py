from pathlib import Path

import resvg_py

# Serverless runtimes (e.g. Vercel) ship with no system fonts, so resvg would
# silently drop every <text> element. We bundle a font with the function and
# point resvg at it explicitly. Family name must match CHART_FONT in
# north_chart.py.
FONT_FAMILY = "Sofia Sans Extra Condensed"
_FONT_NAME = "SofiaSansExtraCondensed.ttf"


def _resolve_font() -> str | None:
    candidates = [
        Path(__file__).resolve().parents[1] / "fonts" / _FONT_NAME,
        Path.cwd() / "app" / "fonts" / _FONT_NAME,
        Path("/var/task/app/fonts") / _FONT_NAME,
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


_FONT_FILE = _resolve_font()


def svg_to_png(svg: str, zoom: float = 2.0) -> bytes:
    """Rasterise an SVG string to PNG bytes via the bundled resvg backend.

    The bundled font is loaded explicitly and set as the default + sans-serif
    family so text renders even when no system fonts are present.
    """
    return resvg_py.svg_to_bytes(
        svg_string=svg,
        zoom=zoom,
        font_files=[_FONT_FILE] if _FONT_FILE else None,
        font_family=FONT_FAMILY,
        sans_serif_family=FONT_FAMILY,
    )
