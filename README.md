# Vedic Discord Bot

A Discord slash-command bot that returns a **sidereal (Lahiri) Vedic chart** — a North-Indian chart image rendered inline, plus the Ascendant and Navagraha positions. Powered by the official [Swiss Ephemeris](https://github.com/aloistr/swisseph) via [`pysweph`](https://pypi.org/project/pysweph/). Runs on **Vercel** (free tier) as a FastAPI app, managed with **uv**.

## What `/vedic` returns

`/vedic date time lat lon tz [chalit]` → a "Bot is thinking…" reply that resolves into:

- A **North-Indian chart image** (SVG → PNG, shown inline in Discord)
- **Lagna (Ascendant)** + **Navagraha** (Surya…Shani, Rahu, Ketu) — sidereal longitude, sign, nakshatra + pada, retrograde flag
- With `chalit: true` — Sripati (Porphyry) bhava placements for each graha

Ayanamsa: Lahiri (`SE_SIDM_LAHIRI`), adjustable via `AYANAMSA_OFFSET_ARCMIN`.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) and Python 3.13
- A [Discord](https://discord.com) account

## 1. Create the Discord app

1. Go to <https://discord.com/developers/applications> → **New Application**.
2. Copy three values:
   - **General Information** → **Application ID**
   - **General Information** → **Public Key**
   - **Bot** → **Reset Token** → **Token**

## 2. Configure environment

```bash
cp .env.example .env
```

Fill in your `.env`:

```
DISCORD_APP_ID=...
DISCORD_PUBLIC_KEY=...
DISCORD_TOKEN=...
AYANAMSA_OFFSET_ARCMIN=6
```

> The project does **not** auto-load `.env`, so pass `--env-file .env` to every `uv run` command below.

## 3. Register the slash command (once)

```bash
uv run --env-file .env python register.py
```

You should see `registered /vedic (id ...)`.

## 4. Test it locally

1. Start the server:
   ```bash
   uv run --env-file .env uvicorn app.main:app --reload --port 8787
   ```
2. Expose it over HTTPS (Discord requires it), in another terminal:
   ```bash
   cloudflared tunnel --url http://localhost:8787
   # or: ngrok http 8787
   ```
3. Copy the HTTPS URL. In the Discord portal: **General Information → Interactions Endpoint URL** → set `https://<that-url>/interactions` → Save. (Save fails if the server isn't running — Discord pings it on save.)
4. Invite the bot: **OAuth2 → URL Generator** → scopes `bot` + `applications.commands` → open the URL → pick a test server.
5. In Discord, type `/vedic` and fill in the fields. You'll see "Bot is thinking…" then the chart + embed.

## 5. Deploy to Vercel (production)

```bash
npm i -g vercel
vercel                       # link / create project
vercel env add DISCORD_APP_ID
vercel env add DISCORD_PUBLIC_KEY
vercel env add DISCORD_TOKEN
vercel env add AYANAMSA_OFFSET_ARCMIN
vercel --prod
```

Then switch the **Interactions Endpoint URL** to `https://<project>.vercel.app/interactions` → Save. You can now close the local tunnel from step 4.

Vercel reads `pyproject.toml` + `uv.lock` natively; the FastAPI app is exposed via `[tool.vercel] entrypoint = "app.main:app"`, and the `ephe/*.se1` files (~1.7 MB) are bundled automatically.

### Keep it warm

Vercel Functions scale to zero; a cold start can exceed Discord's 3-second ACK. `vercel.json` defines a cron hitting `/cron` every 10 minutes. If that's not enough, point a free external cron (e.g. cron-job.org) at `https://<project>.vercel.app/cron`.

## Tests

```bash
uv run pytest
```

## Notes

- **Time input**: `time` is the local clock time at the birth place; `tz` is the UTC offset (e.g. `5.5` IST, `-4` EDT).
- **Rahu/Ketu**: mean lunar node; Ketu is exactly 180° from Rahu.
- **Data files**: `ephe/*.se1` cover **1800–2399** at full Swiss Ephemeris precision.
- **License**: Swiss Ephemeris is dual-licensed **AGPL** or a paid Professional license from Astrodienst.
