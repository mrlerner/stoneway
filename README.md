# Stone Way

Comparing residential-unit growth along two Wallingford (Seattle) corridors:

- **Stone Way N**, from N 34th St up to N 45th St
- **N/NE 45th St**, from Stone Way N east to I-5

The question: has Stone Way added housing faster than 45th St over the last ~20
years? (Short answer: yes — about **6×** more net units.)

**Live dashboard:** https://mrlerner.github.io/stoneway/

## Data source

City of Seattle **Building Permits** open dataset
([76t5-zqzr](https://data.seattle.gov/Built-Environment/Building-Permits/76t5-zqzr)),
queried through the Socrata API (no key required). It records every permit back to
the 1980s with address, lat/long, permit type, status, and the net change in
housing units (`housingunitsadded` / `housingunitsremoved`).

## Method

1. **Corridor membership** — a permit belongs to a corridor if its address is on
   that street *and* it falls inside the segment:
   - Stone Way N: house numbers 3400–4499.
   - 45th St: longitude between Stone Way (≈ -122.343) and I-5 (≈ -122.3235), on
     the 45th St line (lat ≈ 47.661).
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

## Reproduce

```bash
./fetch_data.sh      # optional: refresh the raw data
python3 analyze.py   # build the CSVs + series.json
python3 verify.py    # sanity-check for double counting
python3 build_chart.py   # regenerate index.html
```

## Caveats

- Permit counts are a close proxy for units *built*, not identical — a few issued
  permits expire unbuilt. For a built-stock cross-check, compare against King
  County Assessor apartment/condo records.
- Not-yet-issued projects in review are excluded from the totals (~250 units on
  45th St, which could narrow the gap going forward).
