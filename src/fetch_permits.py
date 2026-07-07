"""
Fetch Census Building Permits Survey (BPS) data for Orange County.

Unlike San Francisco (a consolidated city-county with its own Socrata permit portal),
Orange County spans dozens of incorporated cities with no unified permit open-data feed,
and California eviction filings are largely sealed / not publicly available as open data
(see README limitations). The Census BPS is the closest public, consistent substitute:
a federal survey of new residential building permits issued, at the county level, monthly,
back to 2000 — https://www.census.gov/construction/bps/

Each monthly file is a full nationwide snapshot for that survey month. We pull the last
N months and filter to Orange County (state FIPS 06, county FIPS 059).
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

BASE_URL = "https://www2.census.gov/econ/bps/County"

OC_STATE_FIPS = "06"
OC_COUNTY_FIPS = "059"

LOOKBACK_MONTHS = 72  # 6 years of history

COLS = [
    "survey_date", "state_fips", "county_fips", "region_code", "division_code", "county_name",
    "bldgs_1unit", "units_1unit", "value_1unit",
    "bldgs_2unit", "units_2unit", "value_2unit",
    "bldgs_3to4unit", "units_3to4unit", "value_3to4unit",
    "bldgs_5plusunit", "units_5plusunit", "value_5plusunit",
    "bldgs_1unit_rep", "units_1unit_rep", "value_1unit_rep",
    "bldgs_2unit_rep", "units_2unit_rep", "value_2unit_rep",
    "bldgs_3to4unit_rep", "units_3to4unit_rep", "value_3to4unit_rep",
    "bldgs_5plusunit_rep", "units_5plusunit_rep", "value_5plusunit_rep",
]


def month_codes(n_months: int) -> list:
    """Generate YYMM survey-date filename codes for the last n_months, most recent first."""
    today = datetime.now()
    codes = []
    y, m = today.year, today.month
    for _ in range(n_months):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
        codes.append(f"{y % 100:02d}{m:02d}")
    return codes


def fetch_month(code: str) -> pd.DataFrame:
    url = f"{BASE_URL}/co{code}c.txt"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception:
        return pd.DataFrame()

    lines = resp.text.splitlines()
    data_lines = [l for l in lines[3:] if l.strip()]
    if not data_lines:
        return pd.DataFrame()

    from io import StringIO
    df = pd.read_csv(StringIO("\n".join(data_lines)), header=None, names=COLS, dtype={"state_fips": str, "county_fips": str})
    oc = df[(df["state_fips"] == OC_STATE_FIPS) & (df["county_fips"] == OC_COUNTY_FIPS)]
    return oc


def fetch_all() -> pd.DataFrame:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    codes = month_codes(LOOKBACK_MONTHS)
    rows = []
    print(f"Fetching {len(codes)} months of Census Building Permits Survey (Orange County)...")
    for i, code in enumerate(codes):
        row = fetch_month(code)
        if not row.empty:
            rows.append(row)
        if i % 12 == 0:
            print(f"  ...{code}")

    if not rows:
        print("  No data found.")
        return pd.DataFrame()

    result = pd.concat(rows, ignore_index=True)
    result["units_total"] = (
        result["units_1unit"] + result["units_2unit"] + result["units_3to4unit"] + result["units_5plusunit"]
    )
    result["units_multifamily"] = result["units_3to4unit"] + result["units_5plusunit"]
    result = result.sort_values("survey_date")

    out_path = RAW_DIR / "oc_building_permits_monthly.csv"
    result.to_csv(out_path, index=False)
    print(f"  {len(result)} months saved to {out_path}")
    return result


if __name__ == "__main__":
    fetch_all()
