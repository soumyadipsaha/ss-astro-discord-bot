from datetime import datetime, timedelta

DASHA_LORDS = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
DASHA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17]  # total = 120
YEAR_DAYS   = 365.2564


def compute_vimshottari(moon_lon: float, birth_ut: datetime) -> list[dict]:
    """Return list of 9 MD dicts {lord, start, end} covering the full 120-year cycle."""
    NAK_WIDTH = 360.0 / 27
    nak_idx   = int(moon_lon / NAK_WIDTH)
    progress  = (moon_lon % NAK_WIDTH) / NAK_WIDTH  # fraction of nakshatra elapsed

    li      = nak_idx % 9
    elapsed = progress * DASHA_YEARS[li] * YEAR_DAYS
    cursor  = birth_ut - timedelta(days=elapsed)

    mds = []
    for i in range(9):
        idx    = (li + i) % 9
        end    = cursor + timedelta(days=DASHA_YEARS[idx] * YEAR_DAYS)
        mds.append({"lord": DASHA_LORDS[idx], "start": cursor, "end": end})
        cursor = end
    return mds


def compute_antardashas(md: dict) -> list[dict]:
    """Return 9 AD dicts within an MD, starting from the MD lord."""
    li      = DASHA_LORDS.index(md["lord"])
    md_days = (md["end"] - md["start"]).total_seconds() / 86400
    cursor  = md["start"]
    ads     = []
    for i in range(9):
        idx  = (li + i) % 9
        days = DASHA_YEARS[idx] / 120 * md_days
        end  = cursor + timedelta(days=days)
        ads.append({"lord": DASHA_LORDS[idx], "start": cursor, "end": end})
        cursor = end
    return ads
