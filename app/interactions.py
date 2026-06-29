import asyncio
import logging

from .astro.chart import build_chart
from .astro.format import format_discord
from .config import settings

log = logging.getLogger("vedic_bot")

EPHEMERAL = 1 << 6


def _options(data: dict) -> dict:
    out = {}
    for o in data.get("data", {}).get("options", []):
        out[o["name"]] = o["value"]
    return out


async def handle_interaction(data: dict) -> dict:
    itype = data.get("type")

    if itype == 1:
        return {"type": 1}

    if itype == 2:
        name = data.get("data", {}).get("name", "")
        if name == "vedic":
            return await _vedic(data)
        return _error("Unknown command.")

    return _error("Unsupported interaction type.")


async def _vedic(data: dict) -> dict:
    opts = _options(data)
    try:
        result = await asyncio.to_thread(
            build_chart,
            opts["date"],
            opts["time"],
            float(opts["lat"]),
            float(opts["lon"]),
            float(opts["tz"]),
            bool(opts.get("chalit", False)),
            settings.ayanamsa_offset_arcmin,
        )
    except KeyError as e:
        return _error(f"Missing required option: {e.args[0]}")
    except Exception as e:
        log.exception("chart computation failed")
        return _error(f"Could not compute chart: {e}")

    embed = format_discord(result)
    return {"type": 4, "data": {"embeds": [embed]}}


def _error(message: str) -> dict:
    return {"type": 4, "data": {"content": f"\u26a0\ufe0f {message}", "flags": EPHEMERAL}}
