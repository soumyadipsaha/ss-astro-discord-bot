from datetime import datetime, timezone

from .dasha import compute_vimshottari, compute_antardashas

SIGN_SHORT = ["Ar", "Ta", "Ge", "Ca", "Le", "Vi", "Li", "Sc", "Sg", "Cp", "Aq", "Pi"]

PLANET_ABBR = {
    "Lagna":   "As",
    "Surya":   "Su", "Chandra": "Mo", "Mangala": "Ma", "Budha": "Me",
    "Guru":    "Ju", "Shukra":  "Ve", "Shani":   "Sa",
    "Rahu":    "Ra", "Ketu":    "Ke",
}


def _nak_short(name: str) -> str:
    parts = name.strip().split()
    if len(parts) > 1:
        return parts[0][0] + parts[1][:2]
    return name[:3]


def _fmt_dms(longitude: float) -> str:
    within  = longitude % 30
    deg     = int(within)
    rem     = (within - deg) * 60
    minutes = int(rem)
    seconds = int((rem - minutes) * 60)
    return f"{deg:02d}:{minutes:02d}:{seconds:02d}"


def _body_line(body: dict) -> str:
    sanskrit = body["name"].split(" ", 1)[0]
    abbr     = PLANET_ABBR.get(sanskrit, sanskrit[:2])
    retro    = "R" if body.get("retrograde") else " "
    sign     = SIGN_SHORT[body["sign_index"]]
    dms      = _fmt_dms(body["longitude"])
    nak      = _nak_short(body["nakshatra"])
    return f"{abbr}{retro} {sign}  {dms}  {nak}  {body['pada']}"


def _dasha_block(result: dict) -> str:
    moon  = next(b for b in result["bodies"] if b["name"].startswith("Chandra"))
    birth = datetime.fromisoformat(result["ut"]).replace(tzinfo=timezone.utc)
    today = datetime.now(timezone.utc)
    mds   = compute_vimshottari(moon["longitude"], birth)

    active_md = next((m for m in mds if m["start"] <= today < m["end"]), None)

    lines = ["Dasha  Vimshottari"]
    for md in mds:
        marker = "  *" if md is active_md else ""
        lines.append(f"{md['lord']}  {md['start']:%d-%m-%Y}  {md['end']:%d-%m-%Y}{marker}")
        if md is active_md:
            ads       = compute_antardashas(md)
            active_ad = next((a for a in ads if a["start"] <= today < a["end"]), None)
            for ad in ads:
                am = "  *" if ad is active_ad else ""
                lines.append(f"  {ad['lord']}  {ad['start']:%d-%m-%Y}  {ad['end']:%d-%m-%Y}{am}")
    return "\n".join(lines)


def format_text(result: dict) -> str:
    """Plain-text version for the debug HTTP endpoint."""
    return format_discord(result)["description"]


def format_discord(result: dict) -> dict:
    city    = result.get("city") or f"{result['lat']}, {result['lon']}"
    tz      = result.get("tz_name") or f"UTC{result['tz']:+g}"
    y, m, d = result["ut"][:10].split("-")
    date    = f"{d}-{m}-{y}"
    label   = result.get("ayanamsa_label", "Lahiri")
    chalit  = " · Chalit" if result["chalit"] else ""
    header  = f"{city} · {date} · {tz} · {label}{chalit}"

    planet_lines = "\n".join(
        _body_line(b) for b in result["bodies"]
        if b["name"].split(" ", 1)[0] in PLANET_ABBR
    )
    dasha_block = _dasha_block(result)

    body = f"{header}\n\n{planet_lines}\n\n{dasha_block}"

    return {
        "title":       "Vedic Chart",
        "description": f"```\n{body}\n```",
        "color":       0x6A5ACD,
    }
