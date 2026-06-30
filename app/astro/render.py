import os
import resvg_py

_FONT_DIRS = [d for d in [
    "/System/Library/Fonts",
    "/Library/Fonts",
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/Library/Fonts"),
] if os.path.isdir(d)]


def svg_to_png(svg: str, zoom: float = 2.0) -> bytes:
    return resvg_py.svg_to_bytes(svg_string=svg, zoom=zoom, font_dirs=_FONT_DIRS or None)
