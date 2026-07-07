# Reference Data Sources

## oc_service_area_factors.csv

Compiled July 2026 via web research, not an automated feed — **re-verify before advising a
client**, especially STR status (ordinances change frequently; several OC cities were actively
revisiting rules in 2025-2026 ahead of the 2026 World Cup and 2028 Olympics).

**Service area (`in_pm_service_area`, `in_sales_featured_cities`):**
Scraped from Candice's own sites, July 2026:
- Niguel Point Properties PM service-area list: https://www.niguelpointpropertiespm.com/
- The Candice Blair Group featured cities: https://www.candiceblairgroup.com/
- "Canyon Areas" (as marketed on the sales site) resolved to Coto de Caza, Rancho Santa
  Margarita, and Silverado — the unincorporated/canyon communities conventionally grouped
  under that label in South OC real estate marketing.
- Laguna Hills is not in either published list but appeared in an active Candice Blair Group
  listing (24955 Wells Fargo, Laguna Hills, CA 92653) — included as adjacent, not core.

**STR status (`str_status`, `str_notes`):**
Web research, cross-referencing:
- https://www.orangecountylawyers.com/blog/airbnb-vrbo-in-orange-county-ca-cities-that-allow-or-deny/
- https://www.guestable.com/blog/orange-county-short-term-rentals/
- https://www.strprofitmap.com/regulations/CA/laguna-niguel (Laguna Niguel ban + list of other
  banned cities: Aliso Viejo, Costa Mesa, Garden Grove, Lake Forest, Tustin, Villa Park,
  Westminster, Yorba Linda)
- https://www.malakaisparks.com/mission-viejo-short-term-rental-rules-2025-update/
- https://www.sanjuancapistrano.org/Faq.aspx?QID=157
- Cities marked "Verify" had no reliable secondary-source confirmation as of this research —
  don't repeat the status to a client without checking the city's municipal code directly.

**Mello-Roos / CFD signal (`mello_roos_signal`):**
Qualitative only — no per-parcel data exists publicly. Based on:
- https://www.lametrohomefinder.com/blog/mello-roos-orange-county-cfd-districts-2026
- Ladera Ranch, Rancho Mission Viejo, and Irvine's newer villages are consistently flagged as
  the heaviest CFD burdens in the county; Coto de Caza is unusual in that some parcels carry
  none. **Always pull the actual CFD/Mello-Roos disclosure for a specific parcel** — this
  column is a directional heads-up, not a substitute for title/escrow disclosures.

**Wildfire notes (`wildfire_notes`):**
Directional only, based on general knowledge of CAL FIRE's Fire Hazard Severity Zone (FHSZ)
program and news coverage of the March 2025 unincorporated-OC map update — **not** a
parcel-level lookup against the actual FHSZ GIS layer. Canyon/wildland-urban-interface
communities (Coto de Caza, Silverado, Laguna Beach's hillside areas) are flagged "Elevated";
everything else is a rough coastal/urban-flatland default of "Low." For an actual insurance or
underwriting decision, check the parcel against CAL FIRE's official viewer:
https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones
