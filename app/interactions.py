import asyncio
import logging

from starlette.background import BackgroundTask
from starlette.responses import JSONResponse

from .astro.chart import build_chart
from .astro.format import format_discord
from .astro.geo import lookup_city, utc_offset
from .astro.north_chart import render_north_chart
from .astro.render import svg_to_png
from .config import settings
from .discord import edit_original_text, edit_original_with_file

log = logging.getLogger("vedic_bot")

EPHEMERAL = 1 << 6
CHART_FILENAME = "chart.png"


def _options(data: dict) -> dict:
    out = {}
    for o in data.get("data", {}).get("options", []):
        out[o["name"]] = o["value"]
    return out


async def handle_interaction(data: dict):
    itype = data.get("type")

    if itype == 1:
        return {"type": 1}

    if itype == 2:
        name = data.get("data", {}).get("name", "")
        if name == "vedic":
            return await _vedic(data)
        return _error("Unknown command.")

    return _error("Unsupported interaction type.")


async def _vedic(data: dict):
    token = data.get("token")
    app_id = data.get("application_id") or settings.discord_app_id
    if not token or not app_id:
        return _error("Missing interaction token/application id.")

    task = BackgroundTask(_finalize_vedic, app_id, token, data)
    return JSONResponse({"type": 5}, background=task)


async def _finalize_vedic(app_id: str, token: str, data: dict) -> None:
    opts = _options(data)
    try:
        year, month, day = int(opts["year"]), int(opts["month"]), int(opts["day"])
        hour, minute = int(opts["hour"]), int(opts["minute"])
        date_str = f"{year}-{month:02d}-{day:02d}"
        time_str = f"{hour:02d}:{minute:02d}"

        geo = await asyncio.to_thread(lookup_city, opts["city"])
        tz = utc_offset(geo["tz_name"], year, month, day, hour, minute)

        result = await asyncio.to_thread(
            build_chart,
            date_str,
            time_str,
            geo["lat"],
            geo["lon"],
            tz,
            bool(opts.get("chalit", False)),
            settings.ayanamsa_offset_arcmin,
        )
        result["city"] = geo["display"]
        result["tz_name"] = geo["tz_name"]
        svg = await asyncio.to_thread(render_north_chart, result)
        png = await asyncio.to_thread(svg_to_png, svg)
    except KeyError as e:
        await _respond_error(app_id, token, f"Missing required option: {e.args[0]}")
        return
    except Exception as e:
        log.exception("chart computation failed")
        await _respond_error(app_id, token, f"Could not compute chart: {e}")
        return

    embed = format_discord(result)
    embed["image"] = {"url": f"attachment://{CHART_FILENAME}"}

    try:
        resp = await edit_original_with_file(
            app_id, token, embed, CHART_FILENAME, png
        )
        if not resp.is_success:
            log.error("discord rejected chart (%s): %s", resp.status_code, resp.text)
            return
    except Exception:
        log.exception("failed to post chart to discord")


async def _respond_error(app_id: str, token: str, message: str) -> None:
    try:
        await edit_original_text(app_id, token, f"\u26a0\ufe0f {message}", ephemeral=True)
    except Exception:
        log.exception("failed to post error to discord")


def _error(message: str) -> dict:
    return {"type": 4, "data": {"content": f"\u26a0\ufe0f {message}", "flags": EPHEMERAL}}
