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
    if not _initialized:
        path = _resolve_ephe_path()
        if path:
            swe.set_ephe_path(path)
        _initialized = True
    # Re-assert every call rather than trusting it persists: this is a cheap,
    # side-effect-free C-global set, and in some deployment environments
    # (e.g. Vercel) it has been observed to silently not stick between
    # requests on a reused process, falling back to swisseph's default
    # (Fagan-Bradley) sidereal mode.
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def close() -> None:
    global _initialized
    swe.close()
    _initialized = False
