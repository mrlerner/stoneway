#!/usr/bin/env python3
"""Restaurants on Stone Way N vs N/NE 45th St -- a survivorship-aware view.

Source: King County Public Health Food Establishment Inspection Data
(data.kingcounty.gov f29f-zza5).

IMPORTANT data limitation that shapes what we can honestly say:
This dataset is effectively a registry of CURRENTLY-ACTIVE food establishments.
Closed restaurants are purged -- county-wide only ~54 of 12,874 establishments have
a last inspection before 2024. So it CANNOT give a true "restaurants open each year"
stock (early years would be survivorship-biased and closures never appear).

What it CAN honestly support, and what this script computes:
  (a) How many restaurants are open RIGHT NOW on each corridor (a clean snapshot).
  (b) The opening-year VINTAGE of those current restaurants: for each year Y,
      how many of today's restaurants had already first appeared by Y. This shows
      WHEN today's restaurant scene was established and which corridor's current
      restaurants are newer -- but it is NOT the historical count of all restaurants
      that were open in year Y (it omits any that have since closed).

Unit = business_id (one food-service permit). Restaurant test = inspection
description mentions "Seating" (sit-down/quick-service); no-seating grocery and
school-lunch permits drop out automatically. A short explicit exclusion list
removes seated permit-holders that aren't restaurants (convenience/retail).

Corridor membership reuses the housing analysis boundaries exactly
(Stone Way N house # 3400-4499; 45th St on the 45th line between Stone Way and I-5).
"""
import json, re, csv

START_YEAR, END_YEAR = 2006, 2025  # inspection data begins 2006-01-02

# Explicit non-restaurant exclusions (carry a "Seating" permit but aren't restaurants).
NON_RESTAURANT = {
    'PR0001037': 'convenience store (7-Eleven)',
    'PR0091763': 'retail store (Brooks Running flagship event space)',
}

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

rows = load('rest_stoneway.json', 'rest_45th.json')

# ---- collapse inspection records into establishments (business_id) ----
est = {}
for r in rows:
    b = r.get('business_id')
    if not b:
        continue
    e = est.get(b)
    if e is None:
        e = est[b] = {
            'business_id': b,
            'name': r.get('name') or r.get('program_identifier') or '',
            'address': r.get('address') or '',
            'lat': fnum(r, 'latitude'), 'lng': fnum(r, 'longitude'),
            'descs': set(), 'dates': [],
        }
    if r.get('description'):
        e['descs'].add(r['description'])
    d = (r.get('inspection_date') or '')[:10]
    if d:
        e['dates'].append(d)
    if not e['address'] and r.get('address'):
        e['address'] = r['address']
    if not e['lat'] and fnum(r, 'latitude'):
        e['lat'] = fnum(r, 'latitude'); e['lng'] = fnum(r, 'longitude')

def classify(e):
    """Return (corridor, in_segment_bool, reason)."""
    addr = (e['address'] or '').upper()
    lat, lng, hn = e['lat'], e['lng'], housenum(addr)
    if 'STONE WAY N' in addr and 'STONE WAY NE' not in addr:
        if hn is None: return ('Stone Way N', False, 'no house number')
        if not (3400 <= hn <= 4499):
            return ('Stone Way N', False, f'#{hn} outside 34th-45th segment')
        return ('Stone Way N', True, '')
    if '45TH ST' in addr:
        if not (47.659 <= lat <= 47.663):
            return ('N/NE 45th St', False, f'lat {lat} not on 45th line')
        if not (-122.343 <= lng <= -122.3235):
            side = 'W of Stone Way' if lng < -122.343 else 'E of I-5'
            return ('N/NE 45th St', False, f'lng {lng} {side}')
        return ('N/NE 45th St', True, '')
    return (None, False, 'not on a target street')

def is_restaurant(e):
    return any('Seating' in (d or '') for d in e['descs'])

def seat_band(descs):
    # smallest-to-largest seating band seen
    for band in ['Seating 151-250', 'Seating 51-150', 'Seating 13-50', 'Seating 0-12']:
        for d in descs:
            if d and band in d:
                return band.replace('Seating ', '') + ' seats'
    return ''

records = []
for b, e in est.items():
    corr, in_seg, seg_reason = classify(e)
    if corr is None:
        continue
    dates = sorted(e['dates'])
    first_y = int(dates[0][:4]) if dates else None
    last_y = int(dates[-1][:4]) if dates else None
    rest = is_restaurant(e)
    excluded_nonrest = b in NON_RESTAURANT

    counted = bool(in_seg and rest and not excluded_nonrest and first_y)
    if not counted:
        if not in_seg:            reason = seg_reason
        elif not rest:            reason = 'no seating (grocery / school / other)'
        elif excluded_nonrest:    reason = NON_RESTAURANT[b]
        else:                     reason = 'no inspection dates'
    else:
        reason = ''

    records.append({
        'corridor': corr, 'counted': counted, 'reason_if_excluded': reason,
        'name': e['name'], 'address': e['address'], 'business_id': b,
        'seating': seat_band(e['descs']),
        'category': ' / '.join(sorted(e['descs'])),
        'first_year': first_y or '', 'last_year': last_y or '',
        'n_inspections': len(e['dates']),
        'last_inspection': dates[-1] if dates else '',
    })

records.sort(key=lambda x: (x['corridor'], str(x['first_year']) or '9999', x['address']))

# ---- VINTAGE of currently-active restaurants ----
# cumulative[c][y] = # of today's restaurants that had first appeared by year y.
# new[c][y]        = # of today's restaurants that first appeared in year y.
corridors = ['Stone Way N', 'N/NE 45th St']
years = list(range(START_YEAR, END_YEAR + 1))
new_by = {c: {y: 0 for y in years} for c in corridors}
for r in records:
    if r['counted']:
        new_by[r['corridor']][int(r['first_year'])] += 1
cum_by = {c: [] for c in corridors}
for c in corridors:
    run = 0
    for y in years:
        run += new_by[c][y]
        cum_by[c].append(run)

open_now = {c: cum_by[c][-1] for c in corridors}

# ---- write per-establishment audit CSV ----
with open('restaurants_by_corridor.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
    w.writeheader(); w.writerows(records)

# ---- write yearly vintage CSV ----
with open('restaurants_vintage_by_year.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['year', 'StoneWay_open_to_date', 'StoneWay_new',
                '45th_open_to_date', '45th_new'])
    for i, y in enumerate(years):
        w.writerow([y, cum_by['Stone Way N'][i], new_by['Stone Way N'][y],
                    cum_by['N/NE 45th St'][i], new_by['N/NE 45th St'][y]])

print(f'CURRENTLY-OPEN RESTAURANTS (King County active food-permit registry):')
for c in corridors:
    print(f'  {c:14}: {open_now[c]} open now')
print(f'  Ratio Stone Way / 45th = {open_now["Stone Way N"]/open_now["N/NE 45th St"]:.2f}x')
print('  (Vintage curve = how many of these had first appeared by each year;')
print('   NOT a true historical stock -- closed restaurants are purged from source.)')

json.dump({'years': years, 'cum_by': cum_by, 'new_by': new_by,
           'open_now': open_now, 'start': START_YEAR, 'end': END_YEAR},
          open('restaurants_series.json', 'w'))
