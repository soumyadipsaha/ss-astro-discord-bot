# Vedic Discord Bot

A Discord slash-command bot that returns **sidereal (Lahiri) positions of the Ascendant and the Hindu Navagraha**, powered by the official [Swiss Ephemeris](https://github.com/aloistr/swisseph) via its Python bindings ([`pysweph`](https://pypi.org/project/pysweph/)). Runs on **Vercel** (free Hobby tier) as a FastAPI app, managed with **uv**.

## What it computes

`/vedic date time lat lon tz [chalit]` →

- **Ascendant (Lagna)** sidereal longitude, rasi (sign), nakshatra + pada
- **Navagraha**: Surya, Chandra, Mangala, Budha, Guru, Shukra, Shani, Rahu (mean node), Ketu (= Rahu + 180°) — each with sidereal longitude, sign, nakshatra/pada, retrograde flag
- **Ayanamsa**: Lahiri (Chitrapaksha), `SE_SIDM_LAHIRI`
- **`chalit` option**: Porphyry (`'O'`) house cusps are used as bhava *madhya* (centers); bhava boundaries are the midpoints between consecutive cusps — the standard **Sripati** convention used for bhava-chalit. Each graha is then assigned to its bhava (1–12). This is **Porphyry/Sripati, not Placidus.**

Data files: `ephe/sepl_18.se1` (planets) + `semo_18.se1` (Moon) cover **1800–2399** at full Swiss Ephemeris (DE441-based) precision (~0.001″). Calculations beyond that range fall back to the built-in Moshier model.

## Project layout

```
app/
  main.py            FastAPI app: /interactions, /health, /cron
  verify.py          Ed25519 signature verification (PyNaCl)
  interactions.py    Discord interaction dispatch (PING + /vedic)
  commands.py        Slash-command schema for /vedic
  config.py          Env-var settings
  astro/
    ephemeris.py     pysweph init (ephe path + Lahiri sidereal mode)
    chart.py         Core: julian day, sidereal calc, houses, Sripati bhavas
    format.py        Discord embed / text formatting
    constants.py     Rasi, nakshatra, and graha tables
ephe/                sepl_18.se1, semo_18.se1  (bundled into the function)
register.py          Registers /vedic with Discord
tests/               Astronomy + HTTP/signing tests
pyproject.toml       uv-managed deps; Vercel entrypoint = app.main:app
vercel.json          Keep-warm cron (every 10 min) -> /cron
```

## Local development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13.

```bash
uv sync
cp .env.example .env     # then fill in your Discord credentials
uv run pytest            # 10 tests: astronomy + signed interaction flow
uv run uvicorn app.main:app --reload --port 8787
```

Expose the local server over HTTPS for Discord (e.g. `cloudflared tunnel --url http://localhost:8787` or `ngrok http 8787`), then set that URL as the application's Interactions Endpoint.

## Discord setup

1. Create an application at <https://discord.com/developers/applications>.
2. From **General Information**, copy the **Public Key** and **Application ID**.
3. From **Bot**, reset and copy the **Token**.
4. Put them in `.env`:

   ```
   DISCORD_APP_ID=...
   DISCORD_PUBLIC_KEY=...
   DISCORD_TOKEN=...
   ```

5. Register the slash command (run once):

   ```bash
   uv run python register.py
   ```

6. Deploy (below), then set the deployed URL `https://<project>.vercel.app/interactions` as the **Interactions Endpoint URL** in the Discord developer portal.

## Deploy to Vercel

This project uses `pyproject.toml` + `uv.lock` (Vercel's Python runtime reads them natively) and pins Python 3.13 via `.python-version`. The FastAPI app is exposed through `[tool.vercel] entrypoint = "app.main:app"`.

```bash
npm i -g vercel
vercel               # link / create project
vercel env add DISCORD_APP_ID
vercel env add DISCORD_PUBLIC_KEY
vercel env add DISCORD_TOKEN
vercel --prod
```

The `ephe/*.se1` files (~1.7 MB total) are bundled into the function automatically.

### Keeping it warm (free tier)

Vercel Functions scale to zero; a cold start after idle can exceed Discord's 3-second ACK. `vercel.json` defines a cron hitting `/cron` every 10 minutes. If the Hobby-plan cron frequency is insufficient, point a free external cron (e.g. cron-job.org) at `https://<project>.vercel.app/cron`.

## Notes

- **Time input**: `time` is the local clock time at the birth place; `tz` is the UTC offset (e.g. `5.5` IST, `-4` EDT). The bot converts to UT before computing.
- **Rahu/Ketu**: uses the mean lunar node (`SE_MEAN_NODE`); Ketu is exactly 180° from Rahu.
- **License**: Swiss Ephemeris is dual-licensed **AGPL** or a paid Professional license from Astrodienst. Public hosting of an AGPL-derived bot carries source-disclosure obligations; acquire a Professional license otherwise.
