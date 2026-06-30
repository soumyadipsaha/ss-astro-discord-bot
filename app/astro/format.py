from .chart import fmt_degree
from .constants import NAKSHATRAS


def _body_line(body: dict, show_bhava: bool) -> str:
    name = body["name"]
    sym = body["symbol"]
    rashi = f"{body['sign']} ({body['sign_sanskrit']})"
    deg = fmt_degree(body["longitude"])
    nak = f"{body['nakshatra']} {body['pada']}"
    retro = " \u211e" if body.get("retrograde") else ""
    bhava = f" \u00b7 B{body['bhava']}" if show_bhava and body.get("bhava") else ""
    return f"**{name}**{retro}\n{sym} {rashi} {deg} \u00b7 {nak}{bhava}"


def _description(result: dict) -> str:
    city = result.get("city")
    tz_name = result.get("tz_name")
    if city and tz_name:
        location = f"{city} · {tz_name}"
    else:
        location = f"{result['lat']}, {result['lon']} (UTC{result['tz']:+g})"
    label = result.get("ayanamsa_label", "Lahiri")
    return (
        f"**UT:** {result['ut']}\n"
        f"**Location:** {location}\n"
        f"**Ayanamsa ({label}):** {result['ayanamsa']:.4f}\N{DEGREE SIGN}"
    )


def format_discord(result: dict) -> dict:
    bodies = result["bodies"]
    asc = bodies[0]
    grahas = bodies[1:]
    show_bhava = result["chalit"]

    fields = [
        {
            "name": "\U0001f31c Lagna (Ascendant)",
            "value": _body_line(asc, show_bhava),
            "inline": False,
        },
        {
            "name": "\U0001fa90 Navagraha",
            "value": "\n".join(_body_line(b, show_bhava) for b in grahas),
            "inline": False,
        },
    ]

    footer = (
        f"Chalit: Sripati bhavas (Porphyry madhya) \u00b7 {result.get('ayanamsa_label', 'Lahiri')} ayanamsa"
        if result["chalit"]
        else f"Rasi chart (sidereal) \u00b7 {result.get('ayanamsa_label', 'Lahiri')} ayanamsa \u00b7 no chalit"
    )

    return {
        "title": "\U0001f549\ufe0f Vedic Chart \u00b7 Sidereal",
        "description": _description(result),
        "fields": fields,
        "footer": {"text": footer},
        "color": 0x6A5ACD,
    }


def format_text(result: dict) -> str:
    show_bhava = result["chalit"]
    label = result.get("ayanamsa_label", "Lahiri")
    lines = [f"Vedic chart (sidereal, {label})  UT={result['ut']}  ayan={result['ayanamsa']:.4f}"]
    for b in result["bodies"]:
        lines.append(_body_line(b, show_bhava))
    return "\n".join(lines)
