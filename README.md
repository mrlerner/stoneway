# Stone Way

Comparing residential-unit growth along two Wallingford (Seattle) corridors:

- **Stone Way N**, from N 34th St up to N 45th St
- **N/NE 45th St**, from Stone Way N east to I-5

Two related questions:

1. Has Stone Way added housing faster than 45th St over the last ~20 years?
   (Yes — about **6×** more net units.)
2. Are Stone Way's lots bigger? (Yes — typical lot ~**1.7×** larger by median,
   which helps explain why larger buildings landed there.)

**Live dashboard:** https://mrlerner.github.io/stoneway/
&middot; **Lot-size comparison:** https://mrlerner.github.io/stoneway/lot_sizes.html

## Corridors studied (exact segments)

These are the **specific street segments** the analysis covers. Anything outside
them is deliberately excluded — keep these boundaries fixed so results stay
comparable over time.

### N/NE 45th St — from I-5 (east) to Stone Way N (west)
- **East boundary:** I-5 freeway (longitude ≈ -122.3235). Addresses across I-5 in
  the University District (e.g. 1013+ NE 45th St) are **out**.
- **West boundary:** the Stone Way N intersection (longitude ≈ -122.343).
  Addresses further west toward Fremont (all NW 45th St, and N 45th St below
  ~#1200) are **out**.
- In practice this is roughly **#100–324 NE 45th St** and **#1220–2414 N 45th St**.
- Verified cut points: last counted on the east is `324 NE 45th`; first counted on
  the west is `1220 N 45th` (at the Stone Way corner).

### Stone Way N — from N 45th St (north) down to N 34th St / the water (south)
- **North boundary:** N 45th St (house number **#4500**). The stretch between 45th
  and N 50th (#4612, 4709, 4807, 4809 …) is **out**.
- **South boundary:** N 34th St near Lake Union (house number **#3400**), where
  Stone Way ends at the water.
- So the segment is **Stone Way N house numbers #3400–4499** (Seattle's grid maps
  the first two digits to the cross street, so #3400 = N 34th and #4500 = N 45th).

To re-check these boundaries at any time, run `python3 verify_addresses.py` — it
lists every address with its segment status and shows the nearest excluded
neighbor past each cut point.

## Data source

City of Seattle **Building Permits** open dataset
([76t5-zqzr](https://data.seattle.gov/Built-Environment/Building-Permits/76t5-zqzr)),
queried through the Socrata API (no key required). It records every permit back to
the 1980s with address, lat/long, permit type, status, and the net change in
housing units (`housingunitsadded` / `housingunitsremoved`).

## Method

1. **Corridor membership** — a permit belongs to a corridor if its address is on
   that street *and* it falls inside the segment defined under
   [Corridors studied](#corridors-studied-exact-segments) above (Stone Way N by
   house number #3400–4499; 45th St by longitude between Stone Way and I-5 on the
   45th St line, lat ≈ 47.661).
2. **What's counted** — only *issued construction* permits (`permittypemapped =
   Building`) that change unit counts. Net units per permit = added − removed.
3. **Demolition permits excluded** — Seattle copies a project's unit count onto
   its demolition permit, so counting them would multiply-count one building
   (e.g. 4009/4011/4015 Stone Way are one 125-unit project, not 437). Excluding
   demolition permits removes that error.
4. **Timing** = permit *issued* year.

## Files

| File | Purpose |
|------|---------|
| `fetch_data.sh` | Pulls raw permit JSON from Seattle's API → `stoneway2.json`, `st45_2.json`. |
| `analyze.py` | Classifies permits into corridors, applies the counting rules, writes `permits_by_corridor.csv`, `units_by_year.csv`, and `series.json`. |
| `verify.py` | Double-count check: confirms unique permit numbers and no two counted permits share an address or location. |
| `build_chart.py` | Renders `index.html` (the dashboard) from `series.json` + `permits_by_corridor.csv`. |
| `stoneway2.json`, `st45_2.json` | Raw API snapshots (so the analysis is reproducible without re-fetching). |
| `permits_by_corridor.csv` | Every permit, with a `counted` flag and exclusion reason — the audit trail. |
| `units_by_year.csv` | Year-by-year net + cumulative units per corridor. |
| `index.html` | Self-contained dashboard (inline SVG charts + permit tables). |
| `fetch_parcels.sh` | Pulls parcels (lot size + geometry) for both segments from the King County `parcel_address_area` service → `parcels_*.json`. |
| `analyze_lots.py` | Computes average/median lot size + frontage/depth per corridor; writes `lots_by_corridor.csv`, `lots_series.json`. |
| `build_lots.py` | Renders `lot_sizes.html` — a to-scale, horizontal lot-size comparison. |
| `lots_by_corridor.csv` | Every parcel with lot sqft, frontage, depth. |
| `lot_sizes.html` | Self-contained lot-size visualization. |

## Reproduce

```bash
# Units analysis
./fetch_data.sh      # optional: refresh the raw permit data
python3 analyze.py   # build the CSVs + series.json
python3 verify.py    # sanity-check for double counting
python3 build_chart.py   # regenerate index.html

# Lot-size analysis
./fetch_parcels.sh   # optional: refresh parcel data
python3 analyze_lots.py  # compute lot stats -> lots_by_corridor.csv, lots_series.json
python3 build_lots.py    # regenerate lot_sizes.html

# Restaurant analysis
./fetch_restaurants.sh        # optional: refresh raw inspection data
python3 analyze_restaurants.py
python3 build_restaurant_chart.py   # regenerate restaurants.html
```

## Restaurants (Stone Way N vs 45th St)

A companion analysis of how many **restaurants** are open on the same two segments.
Question: has Stone Way's restaurant scene overtaken 45th St's?

**Short answer:** not on raw count — **45th St has 48 open restaurants today vs 29
on Stone Way (1.7×)**. But Stone Way's restaurants are far *newer*: ~38% of them
first appear in 2024–2025 and its count nearly doubled since 2022 (15→29), tracking
the housing boom. So Stone Way is the faster-*growing* restaurant corridor, while
45th still has the larger established row.

**Important data limitation.** The only free, reproducible block-level source is
King County Public Health's Food Establishment Inspection Data
([f29f-zza5](https://data.kingcounty.gov/Health-Wellness/Food-Establishment-Inspection-Data/f29f-zza5)),
which is effectively a registry of restaurants open *today* — closed restaurants are
purged (county-wide only ~54 of 12,874 establishments have a last inspection before
2024). So this analysis honestly shows **(1)** how many restaurants are open *now*
and **(2)** the *opening-year vintage* of those current restaurants — **not** a true
historical stock that would include since-closed places. A true 20-year open-per-year
curve needs a source with restaurant *close* dates; none exists cleanly for free
(WA DOR's Business Lookup keeps close dates but only 5 years and has no API; the best
partial option is a Feb-2020 Kaggle snapshot of f29f-zza5 to diff against today and
recover 2020-era closures).

Method: a food permit is a "restaurant" if its inspection record carries a *seating*
category (sit-down / quick-service); no-seating grocery and school-lunch permits drop
out automatically, and convenience/retail permit-holders with seating (7-Eleven,
Brooks Running) are excluded explicitly with a stated reason. Opening proxy = first
inspection date. Corridor boundaries are identical to the housing analysis.

| File | Purpose |
|------|---------|
| `fetch_restaurants.sh` | Pulls food-establishment inspection JSON for both corridors → `rest_stoneway.json`, `rest_45th.json`. |
| `analyze_restaurants.py` | Classifies establishments into corridors, applies the restaurant test, writes `restaurants_by_corridor.csv`, `restaurants_vintage_by_year.csv`, `restaurants_series.json`. |
| `build_restaurant_chart.py` | Renders `restaurants.html` (the restaurant dashboard). |
| `restaurants_by_corridor.csv` | Every establishment with a `counted` flag + exclusion reason — the audit trail. |
| `restaurants.html` | Self-contained restaurant dashboard. |

## Caveats

- Permit counts are a close proxy for units *built*, not identical — a few issued
  permits expire unbuilt. For a built-stock cross-check, compare against King
  County Assessor apartment/condo records.
- Not-yet-issued projects in review are excluded from the totals (~250 units on
  45th St, which could narrow the gap going forward).
