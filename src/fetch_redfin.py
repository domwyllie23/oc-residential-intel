"""
Fetch Redfin market tracker data for Orange County residential/multifamily analysis.
County file: ~240MB compressed, downloaded fully then filtered.
Zip file: ~1.5GB compressed, streamed and filtered on the fly.

Note: Redfin tracks Orange County as its own metro ("Anaheim, CA"), separate from the
Los Angeles-Long Beach-Anaheim CBSA used by some other sources (e.g. Zillow's metro file).
"""

import requests
import pandas as pd
import gzip
import io
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

COUNTY_URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/county_market_tracker.tsv000.gz"
ZIP_URL = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/zip_code_market_tracker.tsv000.gz"

OC_REGION = "Orange County, CA"
OC_STATE = "CA"
OC_METRO_KEYWORD = "Anaheim"  # Redfin's PARENT_METRO_REGION for Orange County

MULTIFAMILY_TYPES = ["Multi-Family (2-4 Unit)", "Condo/Co-op", "Townhouse"]


def fetch_county_data() -> pd.DataFrame:
    print("Downloading Redfin county data (~240MB)...")
    resp = requests.get(COUNTY_URL, stream=True, timeout=300)
    resp.raise_for_status()

    content = b""
    total = 0
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
        content += chunk
        total += len(chunk)
        if total % (20 * 1024 * 1024) == 0:
            print(f"  {total // 1024 // 1024}MB downloaded...")

    print("  Decompressing...")
    with gzip.open(io.BytesIO(content)) as f:
        df = pd.read_csv(f, sep="\t", low_memory=False)

    df_oc = df[df["REGION"] == OC_REGION].copy()

    out_path = RAW_DIR / "redfin_county_oc.csv"
    df_oc.to_csv(out_path, index=False)
    print(f"  {len(df_oc)} rows saved to {out_path}")

    mf_mask = df_oc["PROPERTY_TYPE"].isin(MULTIFAMILY_TYPES)
    df_mf = df_oc[mf_mask]
    mf_path = RAW_DIR / "redfin_county_oc_multifamily.csv"
    df_mf.to_csv(mf_path, index=False)
    print(f"  {len(df_mf)} multifamily rows saved to {mf_path}")

    return df_oc


def fetch_zip_data_streaming() -> pd.DataFrame:
    """Stream the 1.5GB zip file and filter to Orange County without loading it all into memory."""
    print("Streaming Redfin zip data (1.5GB compressed — filtering on the fly)...")
    resp = requests.get(ZIP_URL, stream=True, timeout=600)
    resp.raise_for_status()

    print("  Buffering... (this takes a few minutes)")
    content = b""
    total = 0
    for chunk in resp.iter_content(chunk_size=4 * 1024 * 1024):
        content += chunk
        total += len(chunk)
        if total % (100 * 1024 * 1024) == 0:
            print(f"  {total // 1024 // 1024}MB buffered...")

    print("  Decompressing and filtering...")
    with gzip.open(io.BytesIO(content)) as f:
        chunks = []
        reader = pd.read_csv(f, sep="\t", chunksize=50000, low_memory=False)
        for i, chunk in enumerate(reader):
            oc = chunk[
                chunk["STATE_CODE"].eq(OC_STATE) &
                chunk["PARENT_METRO_REGION"].str.contains(OC_METRO_KEYWORD, case=False, na=False)
            ]
            if not oc.empty:
                chunks.append(oc)
            if i % 50 == 0:
                print(f"  Processed chunk {i}...")

    if not chunks:
        print("  No Orange County data found.")
        return pd.DataFrame()

    df = pd.concat(chunks, ignore_index=True)
    out_path = RAW_DIR / "redfin_zip_oc.csv"
    df.to_csv(out_path, index=False)
    print(f"  {len(df)} rows saved to {out_path}")
    return df


if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    fetch_county_data()
    fetch_zip_data_streaming()
