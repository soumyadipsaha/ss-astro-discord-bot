import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from .astro.chart import build_chart
from .astro.ephemeris import close, init_ephe
from .astro.format import format_discord, format_text
from .config import settings
from .interactions import handle_interaction
from .verify import verify_signature

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("vedic_bot")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_ephe()
    log.info("ephemeris initialised")
    yield
    close()


app = FastAPI(title="Vedic Discord Bot", lifespan=lifespan)

init_ephe()


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/cron")
async def cron():
    return {"ok": True}


@app.get("/chart")
async def chart(
    date: str,
    time: str,
    lat: float,
    lon: float,
    tz: float,
    chalit: bool = False,
    text: bool = False,
    ayanamsa_offset: float | None = None,
):
    offset = settings.ayanamsa_offset_arcmin if ayanamsa_offset is None else ayanamsa_offset
    result = await asyncio.to_thread(
        build_chart, date, time, lat, lon, tz, chalit, offset
    )
    if text:
        return Response(format_text(result), media_type="text/plain")
    return {**result, "discord_embed": format_discord(result)}


@app.post("/interactions")
async def interactions(request: Request):
    signature = request.headers.get("X-Signature-Ed25519", "")
    timestamp = request.headers.get("X-Signature-Timestamp", "")
    raw = await request.body()

    if not verify_signature(raw, signature, timestamp, settings.discord_public_key):
        return Response(status_code=401, content="invalid request signature")

    data = json.loads(raw)
    return await handle_interaction(data)
