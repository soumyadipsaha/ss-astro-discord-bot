from app.astro import chart
from app.astro.ephemeris import init_ephe


def setup_module(_module):
    init_ephe()


def test_j2000_lahiri_ayanamsa():
    jd = chart.swe.julday(2000, 1, 1, 12.0, chart.swe.GREG_CAL)
    ayan = chart.ayanamsa(jd)
    assert abs(ayan - 23.853) < 0.01, ayan


def test_sidereal_sun_j2000_is_sagittarius():
    jd = chart.swe.julday(2000, 1, 1, 12.0, chart.swe.GREG_CAL)
    grahas = {g["sanskrit"]: g for g in chart.graha_positions(jd)}
    sun = grahas["Surya"]["longitude"]
    assert abs(sun - 256.52) < 0.01, sun
    assert chart.sign_of(sun) == 8
    assert chart.SIGNS[8][0] == "Sagittarius"


def test_rahu_ketu_are_180_apart():
    jd = chart.swe.julday(2000, 1, 1, 12.0, chart.swe.GREG_CAL)
    g = {x["sanskrit"]: x for x in chart.graha_positions(jd)}
    diff = (g["Ketu"]["longitude"] - g["Rahu"]["longitude"]) % 360
    assert abs(diff - 180.0) < 1e-9


def test_build_chart_has_ten_bodies():
    result = chart.build_chart("2000-01-01", "17:30", 28.6139, 77.2090, 5.5)
    assert len(result["bodies"]) == 10
    assert result["bodies"][0]["name"].startswith("Lagna")
    names = [b["name"] for b in result["bodies"]]
    assert "Ketu (South Node)" in names
    assert "Rahu (North Node)" in names


def test_chalit_assigns_bhavas_in_range():
    result = chart.build_chart("2000-01-01", "17:30", 28.6139, 77.2090, 5.5, chalit=True)
    assert result["chalit"] is True
    assert result["bhava_starts"] is not None
    assert len(result["bhava_starts"]) == 12
    bhavas = [b["bhava"] for b in result["bodies"]]
    assert all(1 <= n <= 12 for n in bhavas)


def test_porphyry_not_placidus():
    result = chart.build_chart("2000-01-01", "17:30", 28.6139, 77.2090, 5.5, chalit=True)
    cusps, _ascmc = chart.swe.houses(
        chart.swe.julday(2000, 1, 1, 12.0, chart.swe.GREG_CAL),
        28.6139, 77.2090, b"P",
    )
    placidus_first = cusps[1]
    assert abs(result["cusps"][0] - placidus_first) > 0.5


def test_custom_ayanamsa_offset():
    args = ("2000-01-01", "12:00", 28.6139, 77.2090, 5.5)
    base = chart.build_chart(*args)
    custom = chart.build_chart(*args, ayanamsa_offset_arcmin=6.0)

    assert base["ayanamsa_label"] == "Lahiri"
    assert custom["ayanamsa_label"] == "Lahiri +6\u2032"
    assert abs((custom["ayanamsa"] - base["ayanamsa"]) - 0.1) < 1e-9

    by_name = lambda r: {b["name"]: b for b in r["bodies"]}
    for key in ["Surya (Sun)", "Chandra (Moon)", "Lagna (Ascendant)"]:
        diff = (by_name(base)[key]["longitude"] - by_name(custom)[key]["longitude"]) % 360
        assert abs(diff - 0.1) < 1e-9, key
