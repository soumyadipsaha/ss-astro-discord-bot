from pathlib import Path

import swisseph as swe

from ..config import settings

EPHE_DIR = Path(__file__).resolve().parents[2] / "ephe"

_initialized = False


def _resolve_ephe_path() -> str | None:
    if settings.ephe_path:
        return settings.ephe_path
    candidates = [
        EPHE_DIR,
        Path.cwd() / "ephe",
        Path("/var/task/ephe"),
    ]
    for c in candidates:
        if c.is_dir() and any(c.glob("*.se1")):
            return str(c)
    return None


def init_ephe() -> None:
    global _initialized
    if _initialized:
        return
    path = _resolve_ephe_path()
    if path:
        swe.set_ephe_path(path)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _initialized = True


def close() -> None:
    global _initialized
    swe.close()
    _initialized = False
