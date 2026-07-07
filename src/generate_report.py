"""
Generate the branded monthly client report (self-contained HTML) from pipeline outputs.

Run after the three notebooks (01, 02, 03) have produced outputs/tables/*.csv and
outputs/charts/*.png:

    python3 src/generate_report.py

Output: docs/monthly_report.html — a single self-contained file (charts embedded as
base64) safe to email as an attachment or open directly in a browser.

--- Branding ---
BRAND below is a placeholder identity. Swap in Candice's real logo, colors, and contact
details once she sends them — every value is read from this one dict, so nothing else
in the file needs to change. To use a real logo image instead of the monogram mark, set
BRAND["logo_path"] to a PNG/SVG file path.
"""

import base64
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
OUT = ROOT / "outputs"
DOCS = ROOT / "docs"

BRAND = {
    "business_name": "The Candice Blair Group",
    "sub_name": "Niguel Point Properties",
    "monogram": "CB",
    "tagline": "Orange County Residential Market Intelligence",
    "contact_email": "info@candiceblairgroup.example",
    "contact_phone": "(949) 555-0100",
    "license_line": "DRE Lic. #00000000  —  placeholder, replace with Candice's license number",
    "marine": "#1f5159",
    "marine_deep": "#123338",
    "brass": "#9c7a3c",
    "logo_path": None,  # set to a file path to use a real logo image instead of the monogram
    "client_name": None,  # set per-send for a personalized "Prepared for" line
}


def b64_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def money(x):
    try:
        return f"${x:,.0f}"
    except (TypeError, ValueError):
        return "—"


def pct(x, digits=1, signed=False):
    try:
        fmt = f"{{:+.{digits}f}}%" if signed else f"{{:.{digits}f}}%"
        return fmt.format(x)
    except (TypeError, ValueError):
        return "—"


def load_data():
    mkt = pd.read_csv(OUT / "tables/market_selection_ranked.csv", dtype={"zip_code": str})
    distress = pd.read_csv(OUT / "tables/distress_scores_ranked.csv", dtype={"zip_code": str})
    forecast = pd.read_csv(OUT / "tables/price_forecasts_12mo.csv")
    permits = pd.read_csv(OUT / "tables/permit_activity_monthly.csv")
    permits["date"] = pd.to_datetime(permits["date"])
    return mkt, distress, forecast, permits


def compute_kpis(mkt, distress, forecast, permits):
    top = mkt.iloc[0]
    best_forecast = forecast.assign(
        chg_num=forecast["12mo Chg"].str.rstrip("%").astype(float)
    ).sort_values("chg_num", ascending=False).iloc[0]
    top_opportunity = distress.sort_values("distress_score", ascending=False).iloc[0]

    trailing12 = permits.set_index("date")["units_total"].rolling(12).sum()
    latest12 = trailing12.iloc[-1]
    prior12 = trailing12.iloc[-13] if len(trailing12) > 13 else None
    permit_yoy = (latest12 / prior12 - 1) * 100 if prior12 else None

    return {
        "top_zip": top["zip_code"],
        "top_city": top["City"],
        "top_score": top["investment_score"],
        "median_home_value": mkt["price_latest"].median(),
        "best_forecast_city": best_forecast["City"],
        "best_forecast_chg": best_forecast["12mo Chg"],
        "opportunity_zip": top_opportunity["zip_code"],
        "opportunity_city": top_opportunity["City"],
        "permits_trailing12": latest12,
        "permit_yoy": permit_yoy,
        "zip_count": len(mkt),
    }


def table_html(df, columns, headers, formatters=None):
    formatters = formatters or {}
    rows = []
    for _, row in df.iterrows():
        cells = []
        for c in columns:
            val = row[c]
            if c in formatters:
                val = formatters[c](val)
            cells.append(f"<td>{val}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    head = "".join(f"<th>{h}</th>" for h in headers)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def chart_card(letter, title, note, img_path):
    img_b64 = b64_image(img_path)
    return f"""
    <section class="exhibit">
      <div class="exhibit-head">
        <span class="exhibit-tag">Exhibit {letter}</span>
        <h3>{title}</h3>
      </div>
      <div class="exhibit-note">{note}</div>
      <div class="exhibit-figure">
        <img src="data:image/png;base64,{img_b64}" alt="{title}" />
      </div>
    </section>
    """


def build_html(mkt, distress, forecast, permits, kpis, report_month):
    b = BRAND

    if b["logo_path"]:
        logo_html = f'<img class="logo-img" src="data:image/png;base64,{b64_image(Path(b["logo_path"]))}" alt="{b["business_name"]}" />'
    else:
        logo_html = f'<div class="monogram">{b["monogram"]}</div>'

    prepared_for = f'<div class="prepared-for">Prepared for {b["client_name"]}</div>' if b["client_name"] else ""

    top_table = table_html(
        mkt.head(10),
        ["rank", "zip_code", "City", "investment_score", "renter_pct", "median_contract_rent", "price_chg_1yr_pct"],
        ["Rank", "ZIP", "City", "Score", "Renter %", "Median Rent", "1yr Price Chg"],
        {
            "investment_score": lambda v: f"{v:.1f}",
            "renter_pct": lambda v: pct(v * 100),
            "median_contract_rent": money,
            "price_chg_1yr_pct": lambda v: pct(v, signed=True),
        },
    )

    forecast_table = table_html(
        forecast,
        ["City", "Current Value", "12mo Forecast", "12mo Chg", "80% CI (Low)", "80% CI (High)"],
        ["City", "Current", "12mo Forecast", "12mo Chg", "80% CI Low", "80% CI High"],
    )

    opportunity_table = table_html(
        distress.sort_values("distress_score", ascending=False).head(8),
        ["zip_code", "City", "distress_score", "price_cut_rate", "investment_score"],
        ["ZIP", "City", "Opportunity Signal", "Price Cut Rate", "Market Score"],
        {
            "distress_score": lambda v: f"{v:.1f}",
            "price_cut_rate": lambda v: pct(v * 100),
            "investment_score": lambda v: f"{v:.1f}",
        },
    )

    exhibits = "".join([
        chart_card(
            "A", "Investment Score — Top 10 Zip Codes",
            "Factor breakdown behind this month's highest-ranked submarkets: renter demand, "
            "vacancy, affordability headroom, multifamily share, price momentum, price-cut rate, "
            "and inventory tightness, each scored 0–100 against every OC zip code.",
            OUT / "charts/factor_heatmap_top10.png",
        ),
        chart_card(
            "B", "Investment Score by City",
            "Zip-level scores rolled up to the city level, the more useful lens in a single-county "
            "market with 30+ distinct submarkets.",
            OUT / "charts/city_summary.png",
        ),
        chart_card(
            "C", "Home Value Trends — Key Cities",
            "Zillow Home Value Index history for Orange County's largest submarkets by listing volume.",
            OUT / "charts/city_price_history.png",
        ),
        chart_card(
            "D", "12-Month Price Forecast",
            "SARIMA time-series forecast with an 80% confidence interval, fit on 2018–present "
            "monthly home values.",
            OUT / "charts/price_forecasts.png",
        ),
        chart_card(
            "E", "Opportunity Matrix — Seller Motivation vs. Market Quality",
            "Zip codes in the upper-right combine elevated price-cut/inventory signal with strong "
            "underlying fundamentals — the target zone for off-market outreach and buy-and-hold "
            "acquisitions.",
            OUT / "charts/opportunity_matrix.png",
        ),
        chart_card(
            "F", "Residential Permit Activity, Orange County",
            "Census Building Permits Survey, county-level (no zip-level permit feed exists for OC's "
            "30+ incorporated cities). A leading indicator of new supply and builder confidence.",
            OUT / "charts/permits_over_time.png",
        ),
        chart_card(
            "G", "Market Health Indicators (Redfin)",
            "Days on market, months of supply, sale-to-list ratio, and price-drop frequency across "
            "all Orange County residential transactions.",
            OUT / "charts/redfin_market_health.png",
        ),
    ])

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{b['business_name']} — {report_month} Market Report</title>
<style>
{CSS}
</style>
</head>
<body>

<header class="masthead">
  <div class="masthead-brand">
    {logo_html}
    <div class="brand-text">
      <div class="business-name">{b['business_name']}</div>
      <div class="sub-name">{b['sub_name']}</div>
    </div>
  </div>
  <div class="masthead-meta">
    <div class="report-title">Orange County Residential<br />Market Intelligence Report</div>
    <div class="report-month">{report_month}</div>
    {prepared_for}
  </div>
</header>

<section class="kpi-strip">
  <div class="kpi">
    <div class="kpi-label">Top-Ranked Submarket</div>
    <div class="kpi-value">{kpis['top_zip']}</div>
    <div class="kpi-sub">{kpis['top_city']} · score {kpis['top_score']:.1f}/100</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">OC Median Home Value</div>
    <div class="kpi-value">{money(kpis['median_home_value'])}</div>
    <div class="kpi-sub">across {kpis['zip_count']} zip codes</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Strongest 12mo Forecast</div>
    <div class="kpi-value">{kpis['best_forecast_chg']}</div>
    <div class="kpi-sub">{kpis['best_forecast_city']}</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Top Opportunity Signal</div>
    <div class="kpi-value">{kpis['opportunity_zip']}</div>
    <div class="kpi-sub">{kpis['opportunity_city']}</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Permits, Trailing 12mo</div>
    <div class="kpi-value">{kpis['permits_trailing12']:,.0f}</div>
    <div class="kpi-sub">{('YoY ' + pct(kpis['permit_yoy'], signed=True)) if kpis['permit_yoy'] is not None else 'units authorized'}</div>
  </div>
</section>

<main>
  <section class="intro">
    <p>This month's report ranks all {kpis['zip_count']} Orange County zip codes on residential
    investment attractiveness, surfaces submarkets showing seller-motivation signal, and forecasts
    12-month home value trends for the county's largest cities — built entirely on public market
    data (Zillow, Redfin, U.S. Census).</p>
  </section>

  <section class="table-block">
    <div class="exhibit-head">
      <span class="exhibit-tag">Exhibit H</span>
      <h3>Top 10 Zip Codes — Full Ranking</h3>
    </div>
    <div class="table-scroll">{top_table}</div>
  </section>

  {exhibits}

  <section class="table-block">
    <div class="exhibit-head">
      <span class="exhibit-tag">Exhibit I</span>
      <h3>12-Month Price Forecast — By City</h3>
    </div>
    <div class="table-scroll">{forecast_table}</div>
  </section>

  <section class="table-block">
    <div class="exhibit-head">
      <span class="exhibit-tag">Exhibit J</span>
      <h3>Top Opportunity Zip Codes</h3>
    </div>
    <div class="table-scroll">{opportunity_table}</div>
  </section>

  <section class="notes">
    <h4>Methodology &amp; Limitations</h4>
    <ul>
      <li>Investment score blends renter %, vacancy, rent-to-income, rent burden, multifamily
      housing share, 1-year price momentum, price-cut rate, and inventory change — each
      percentile-ranked against all Orange County zip codes.</li>
      <li>Home values are Zillow's ZHVI (repeat-sales index, all homes) — the standard public
      proxy for residential and small multifamily pricing; unit-level rent/cap-rate data would
      require a paid feed (CoStar, RealPage, etc.).</li>
      <li>California eviction filings are sealed court records with no reliable open-data source,
      so the opportunity signal here is built from price cuts, inventory growth, and vacancy —
      not eviction/foreclosure activity as in markets with public eviction data.</li>
      <li>Permit activity is county-wide (Census Building Permits Survey); Orange County's 30+
      incorporated cities have no unified zip-level permit feed.</li>
      <li>Forecasts are statistical projections (SARIMA), not fundamental underwriting or
      appraisal — always pair with a property-level opinion of value.</li>
    </ul>
  </section>
</main>

<footer>
  <div class="footer-brand">{b['business_name']} · {b['sub_name']}</div>
  <div class="footer-contact">{b['contact_email']} · {b['contact_phone']}</div>
  <div class="footer-license">{b['license_line']}</div>
</footer>

</body>
</html>"""
    return html


CSS = """
:root {
  --paper: #f6f2e8;
  --paper-raised: #fffdf8;
  --ink: #1b2624;
  --ink-soft: #4a5651;
  --marine: #1f5159;
  --marine-deep: #123338;
  --brass: #9c7a3c;
  --line: #cbbfa0;
  --good: #3c7a5a;
  --warn: #a9542c;
}
@media (prefers-color-scheme: dark) {
  :root {
    --paper: #10201e;
    --paper-raised: #16302c;
    --ink: #eef2ee;
    --ink-soft: #a9b8b0;
    --marine: #6fb3ac;
    --marine-deep: #dcefe9;
    --brass: #cfa458;
    --line: #365049;
  }
}
:root[data-theme="dark"] {
  --paper: #10201e; --paper-raised: #16302c; --ink: #eef2ee; --ink-soft: #a9b8b0;
  --marine: #6fb3ac; --marine-deep: #dcefe9; --brass: #cfa458; --line: #365049;
}
:root[data-theme="light"] {
  --paper: #f6f2e8; --paper-raised: #fffdf8; --ink: #1b2624; --ink-soft: #4a5651;
  --marine: #1f5159; --marine-deep: #123338; --brass: #9c7a3c; --line: #cbbfa0;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: Georgia, 'Iowan Old Style', 'Palatino Linotype', Palatino, serif;
  font-size: 16px;
  line-height: 1.6;
}
.label {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.tabular { font-variant-numeric: tabular-nums; }

.masthead {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  padding: 48px clamp(20px, 5vw, 64px) 28px;
  border-bottom: 2px solid var(--marine);
}
.masthead-brand { display: flex; align-items: center; gap: 16px; }
.monogram {
  width: 56px; height: 56px; border-radius: 50%;
  background: var(--marine-deep);
  color: var(--paper-raised);
  display: flex; align-items: center; justify-content: center;
  font-family: Georgia, serif; font-size: 22px; letter-spacing: 0.02em;
  border: 1px solid var(--brass);
}
.logo-img { max-height: 56px; max-width: 160px; object-fit: contain; }
.business-name { font-size: 22px; font-weight: normal; color: var(--marine-deep); }
.sub-name {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-soft);
  margin-top: 2px;
}
.masthead-meta { text-align: right; }
.report-title {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 13px; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--ink-soft); line-height: 1.5;
}
.report-month { font-size: 20px; color: var(--brass); margin-top: 6px; }
.prepared-for {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 12px; color: var(--ink-soft); margin-top: 6px; font-style: italic;
}

.kpi-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  border-bottom: 1px solid var(--line);
  background: var(--paper-raised);
}
.kpi {
  padding: 22px clamp(12px, 2vw, 24px);
  border-right: 1px solid var(--line);
}
.kpi:last-child { border-right: none; }
.kpi-label {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 10.5px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--ink-soft); margin-bottom: 8px;
}
.kpi-value {
  font-size: 26px; color: var(--marine-deep);
  font-variant-numeric: tabular-nums;
}
.kpi-sub { font-size: 12.5px; color: var(--ink-soft); margin-top: 4px; }

main { max-width: 980px; margin: 0 auto; padding: 0 clamp(20px, 5vw, 64px); }

.intro { padding: 32px 0; border-bottom: 1px solid var(--line); }
.intro p { max-width: 68ch; color: var(--ink-soft); font-size: 16px; }

.exhibit, .table-block { padding: 36px 0; border-bottom: 1px solid var(--line); }
.exhibit-head { display: flex; align-items: baseline; gap: 14px; margin-bottom: 10px; }
.exhibit-tag {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--brass); border: 1px solid var(--brass); border-radius: 2px;
  padding: 2px 8px; white-space: nowrap;
}
.exhibit-head h3 { font-size: 19px; font-weight: normal; color: var(--marine-deep); margin: 0; }
.exhibit-note { color: var(--ink-soft); font-size: 14.5px; max-width: 68ch; margin-bottom: 18px; }
.exhibit-figure {
  background: var(--paper-raised);
  border: 1px solid var(--line);
  padding: 12px;
}
.exhibit-figure img { width: 100%; height: auto; display: block; }

.table-scroll { overflow-x: auto; }
table {
  width: 100%; border-collapse: collapse;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 13.5px;
}
th {
  text-align: left; font-weight: normal; text-transform: uppercase;
  letter-spacing: 0.05em; font-size: 11px; color: var(--ink-soft);
  padding: 8px 14px; border-bottom: 1px solid var(--marine);
  white-space: nowrap;
}
td {
  padding: 9px 14px; border-bottom: 1px solid var(--line);
  font-variant-numeric: tabular-nums; white-space: nowrap;
}
tr:hover td { background: var(--paper-raised); }

.notes { padding: 36px 0 48px; }
.notes h4 {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 13px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--ink-soft); font-weight: normal; margin: 0 0 14px;
}
.notes ul { margin: 0; padding-left: 20px; }
.notes li { color: var(--ink-soft); font-size: 14px; margin-bottom: 10px; max-width: 72ch; }

footer {
  text-align: center; padding: 32px 20px 48px;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: var(--ink-soft); font-size: 12px;
}
.footer-brand { color: var(--marine-deep); font-size: 13px; margin-bottom: 4px; }
.footer-license { margin-top: 4px; opacity: 0.8; }
"""


def main():
    DOCS.mkdir(exist_ok=True)
    mkt, distress, forecast, permits = load_data()
    kpis = compute_kpis(mkt, distress, forecast, permits)
    report_month = datetime.now().strftime("%B %Y")
    html = build_html(mkt, distress, forecast, permits, kpis, report_month)

    out_path = DOCS / "monthly_report.html"
    out_path.write_text(html)
    print(f"Report written to {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
