import resvg_py


def svg_to_png(svg: str, zoom: float = 2.0) -> bytes:
    """Rasterise an SVG string to PNG bytes via the bundled resvg backend (no system deps)."""
    return resvg_py.svg_to_bytes(svg_string=svg, zoom=zoom)
