# Orange County Residential Market Intelligence

A monthly market intelligence pipeline built for **Candice Blair** — broker/owner of
**Niguel Point Properties** and **The Candice Blair Group** — to send to her ~250 managed-property
and sales clients across Orange County.

Adapted from a sibling project ([`sf-multifamily-intel`](../sf-multifamily-intel)) that replicates the
top-of-funnel workflow of a multifamily acquisitions team: market selection, seller-motivation
signal detection, and price forecasting — entirely on free public data.

> **This repo is public and `docs/` is served live on GitHub Pages.** Candice has CRMLS access,
> but CRMLS's redistribution rules don't permit posting MLS-derived data or statistics to a
> public URL. If MLS data is ever added to this project, it stays out of `docs/`, `outputs/`, and
> this repo entirely — see `CLAUDE.md` for the full policy.

---

## What it does

### 1. Market Selection (`notebooks/01_market_selection.ipynb`)
Scores all 88 Orange County zip codes on 8 investment factors and produces a composite ranking:

| Factor | Signal |
|--------|--------|
| Renter % of households | Structural rental demand |
| Vacancy rate | Market tightness and pricing power |
| Rent-to-income ratio | Headroom for rent growth |
| Rent burden rate | Affordability ceiling |
| Multifamily housing share | Established MF market, permissive zoning |
| 1-year price momentum | Appreciation trend |
| Price cut rate | Seller vs. buyer power |
| Inventory change | Supply tightness |

Output: ranked zip code table, factor heatmap, city-level rollup (OC has 30+ cities in one
county), interactive choropleth map, and an AB 1482 (statewide rent cap) exposure note.

**Section 8, "Candice's actual service area,"** flags the ~39 zip codes that fall within Niguel
Point Properties' 14-city property-management footprint and/or The Candice Blair Group's 9
featured sales cities (scraped from her own sites — see `data/reference/SOURCES.md`), and layers
on three factors that matter for her specifically but don't belong in a percentile score:
short-term rental legality (she owns an Airbnb), Mello-Roos/CFD exposure (heavy in South OC's
master-planned communities), and wildfire risk (canyon/WUI communities in her footprint). This is
directional research, not a live feed — re-verify before advising a client. Exports to
`outputs/tables/service_area_ranked.csv`.

### 2. Seller-Motivation Signal Detection (`notebooks/02_distressed_signals.ipynb`)
Surfaces zip codes with elevated seller-motivation signal using price cuts, inventory growth,
and vacancy — plus a county-wide building-permit trend as a capital-deployment indicator.

Key output: **Opportunity Matrix** — distress score vs. market attractiveness, highlighting zip
codes with likely-motivated sellers in fundamentally strong submarkets.

**This section is deliberately narrower than the SF version** — see Limitations below.

### 3. Price Forecasting (`notebooks/03_price_forecasting.ipynb`)
SARIMA time series models fit on Zillow Home Value Index data (monthly, 2018–present) to produce
12-month price forecasts with 80% confidence intervals for Orange County's largest cities (Irvine,
Anaheim, Newport Beach, Santa Ana, and one more by zip-code coverage).

Also includes Redfin transaction-level market health indicators: days on market, months of
supply, sale-to-list ratio, and price drop frequency — Redfin tracks Orange County as its own
metro ("Anaheim, CA"), separate from the LA-Long Beach-Anaheim CBSA.

### 4. Monthly Client Report (`src/generate_report.py`)
Assembles a single self-contained, branded HTML report from the notebook outputs — safe to email
as an attachment. Branding (business name, colors, contact info, logo) lives in one `BRAND` dict
at the top of the script.

```bash
python3 src/generate_report.py
# -> docs/monthly_report.html
```

**Still needed from Candice before this goes out to real clients:** logo file, brand colors,
license number, and preferred contact details — `BRAND` in `src/generate_report.py` currently
holds placeholders.

---

## Data Sources

All free and publicly available:

| Source | Data | Update frequency |
|--------|------|-----------------|
| [Zillow Research](https://www.zillow.com/research/data/) | ZHVI price index, inventory, price cuts (zip-level) | Monthly |
| [Redfin Data Center](https://www.redfin.com/news/data-center/) | Transaction metrics, county + zip level | Monthly |
| [US Census ACS 5-year](https://www.census.gov/programs-surveys/acs) | Renter rates, vacancy, rent burden, MF housing share | Annual |
| [Census Building Permits Survey](https://www.census.gov/construction/bps/) | Residential permits, county-level | Monthly |
| Census 2020 ZCTA-to-county relationship file | Authoritative OC zip code list (88 zips, majority-land method) | Static |

---

## Setup

```bash
pip install -r requirements.txt

python3 src/fetch_zillow.py
python3 src/fetch_redfin.py
python3 src/fetch_census.py
python3 src/fetch_permits.py

jupyter lab
```

Run notebooks in order: `01_market_selection` → `02_distressed_signals` → `03_price_forecasting`,
then `python3 src/generate_report.py` for the client-facing report.

For a monthly refresh, just re-run the fetch scripts (they overwrite `data/raw/`) and re-execute
the three notebooks, then regenerate the report.

---

## Key Outputs

```
outputs/
├── charts/       # factor heatmap, city summary, price history, forecasts, opportunity matrix, permits, Redfin health
├── maps/         # interactive choropleth (market_selection_map.html)
└── tables/       # market_selection_ranked.csv, distress_scores_ranked.csv, price_forecasts_12mo.csv, permit_activity_monthly.csv
docs/
└── monthly_report.html   # branded client-facing report
```

---

## Limitations

- **No eviction-based distress signal.** The SF version of this project used SF's open eviction
  notice data as its strongest seller-motivation signal. California eviction filings are largely
  sealed court records — there is no honest public substitute, so this signal is dropped rather
  than approximated for Orange County.
- **No zip-level permit data.** Orange County spans 30+ incorporated cities, each with its own
  permit system, and no unified zip-level open-data feed exists (the county's own open-data portal
  only covers unincorporated land). The Census Building Permits Survey fills the gap but only at
  the county level.
- Price data is ZHVI (all-home repeat-sales index) — multifamily-specific cap rate or NOI data
  requires a paid feed (CoStar, RealPage, Reonomy, etc.).
- Rent index (ZORI) is paywalled by Zillow; median contract rent from ACS is used as a proxy
  (same limitation as the SF project).
- **This is a market-selection and trend tool, not a listing search tool.** It tells you which
  zip codes look attractive and which show seller-motivation signal — it does not return
  individual on-market or off-market properties. Actual deal sourcing needs either MLS/CRMLS
  access (Candice's broker license) or a paid data service (PropStream, Reonomy, BatchLeads,
  Attom) layered on top of this market-selection output.
- Forecasts are statistical projections, not fundamental underwriting.

---

## Stack

Python 3.13 · pandas · numpy · statsmodels (SARIMA) · matplotlib · folium · pyshp · requests
