#!/usr/bin/env python3
"""Wallingford residential-unit growth: Stone Way N vs N/NE 45th St.
Source: City of Seattle Building Permits (data.seattle.gov 76t5-zqzr).
Method: count CONSTRUCTION permits only (permittypemapped='Building'); demolition
permits are excluded because their housingunitsadded field is spuriously populated
with the related project's unit count. Net units per permit = added - removed.
Corridor membership = address-on-street + physical bounding box. Timing = issued year.
"""
import json, re, csv

def load(*fs):
    rows = []
    for f in fs:
        rows += json.load(open(f))
    return rows

def housenum(addr):
    m = re.match(r'\s*(\d+)', addr or '')
    return int(m.group(1)) if m else None

def fnum(r, k):
    try: return float(r.get(k) or 0)
    except: return 0.0

rows = load('stoneway2.json', 'st45_2.json')
# de-dup identical permitnum (a permit can appear once per source pull)
seen = {}
for r in rows:
    seen[r.get('permitnum')] = r
rows = list(seen.values())

def classify(r):
    """Return (corridor, included_bool, reason)."""
    addr = (r.get('originaladdress1') or '').upper()
    lat = fnum(r, 'latitude'); lng = fnum(r, 'longitude')
    hn = housenum(addr)
    # ---- Stone Way N, segment N 34th -> N 45th = house # 3400-4499 ----
    if 'STONE WAY N' in addr and 'STONE WAY NE' not in addr:
        if hn is None: return ('Stone Way N', False, 'no house number')
        if not (3400 <= hn <= 4499):
            return ('Stone Way N', False, f'#{hn} outside 34th-45th segment')
        return ('Stone Way N', True, '')
    # ---- 45th St, segment Stone Way (-122.343) -> I-5 (-122.3235) ----
    if '45TH ST' in addr:
        if not (47.659 <= lat <= 47.663):
            return ('N/NE 45th St', False, f'lat {lat} not on 45th line')
        if not (-122.343 <= lng <= -122.3235):
            side = 'W of Stone Way' if lng < -122.343 else 'E of I-5'
            return ('N/NE 45th St', False, f'lng {lng} {side}')
        return ('N/NE 45th St', True, '')
    return (None, False, 'not on a target street')

per_permit = []
for r in rows:
    corr, inc, reason = classify(r)
    if corr is None:
        continue
    issued = (r.get('issueddate') or '')[:10]
    is_demo = (r.get('permittypemapped') == 'Demolition')
    counted = inc and bool(issued) and not is_demo
    if inc and not issued: reason = 'not issued (pipeline)'
    elif inc and is_demo:  reason = 'demolition permit (units counted on construction permit)'
    net = fnum(r, 'housingunitsadded') - fnum(r, 'housingunitsremoved')
    per_permit.append({
        'corridor': corr, 'counted': counted, 'reason_if_excluded': '' if counted else reason,
        'address': r.get('originaladdress1'), 'permitnum': r.get('permitnum'),
        'permittype': r.get('permittypedesc'), 'permitclass': r.get('permitclass'),
        'issued_year': issued[:4], 'issued_date': issued,
        'status': r.get('statuscurrent'),
        'units_added': fnum(r, 'housingunitsadded'),
        'units_removed': fnum(r, 'housingunitsremoved'),
        'net_units': net if counted else 0,
        'description': (r.get('description') or '')[:120],
    })

per_permit.sort(key=lambda x: (x['corridor'], x['issued_date'] or '9999', x['address']))

# ---- yearly aggregation of counted permits ----
corridors = ['Stone Way N', 'N/NE 45th St']
ALL_YEARS = list(range(2004, 2026))
DISPLAY_START = 2011          # chart shows the last ~15 years; pre-2011 is sparse
years = [y for y in ALL_YEARS if y >= DISPLAY_START]
net_all = {c: {y: 0.0 for y in ALL_YEARS} for c in corridors}
for p in per_permit:
    if p['counted']:
        net_all[p['corridor']][int(p['issued_year'])] += p['net_units']

# pre-2011 net is carried as a baseline so cumulative totals stay accurate
baseline = {c: sum(net_all[c][y] for y in ALL_YEARS if y < DISPLAY_START) for c in corridors}
# full cumulative (all years, for the CSV record)
cum_all = {c: [] for c in corridors}
for c in corridors:
    run = 0.0
    for y in ALL_YEARS:
        run += net_all[c][y]; cum_all[c].append(run)
# displayed series: per-year + cumulative seeded with the pre-2011 baseline
net_by = {c: {y: net_all[c][y] for y in years} for c in corridors}
cum = {c: [] for c in corridors}
for c in corridors:
    run = baseline[c]
    for y in years:
        run += net_all[c][y]; cum[c].append(run)

totals = {c: cum[c][-1] for c in corridors}
# pipeline (in-segment, construction, not yet issued)
pipeline = {c: 0.0 for c in corridors}
for p in per_permit:
    if (not p['counted']) and p['reason_if_excluded'] == 'not issued (pipeline)' \
       and p['permitnum'].endswith('-CN') and p['status'] != 'Canceled':
        pipeline[p['corridor']] += p['units_added']

# ---- write per-permit CSV ----
with open('permits_by_corridor.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(per_permit[0].keys()))
    w.writeheader(); w.writerows(per_permit)

# ---- write yearly summary CSV ----
with open('units_by_year.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['year', 'StoneWay_net_added', 'StoneWay_cumulative',
                '45th_net_added', '45th_cumulative'])
    for i, y in enumerate(ALL_YEARS):
        w.writerow([y, net_all['Stone Way N'][y], cum_all['Stone Way N'][i],
                    net_all['N/NE 45th St'][y], cum_all['N/NE 45th St'][i]])

print('TOTALS (issued construction permits, net units):')
for c in corridors:
    print(f'  {c:14}: {totals[c]:.0f} net units added  (+{pipeline[c]:.0f} in pipeline)')
print(f'  Ratio Stone Way / 45th = {totals["Stone Way N"]/totals["N/NE 45th St"]:.1f}x')
print(f'  counted permits: {sum(1 for p in per_permit if p["counted"])}')

# stash for chart builder
json.dump({'years': years, 'net_by': net_by, 'cum': cum,
           'totals': totals, 'pipeline': pipeline, 'baseline': baseline}, open('series.json', 'w'))
