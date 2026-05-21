#!/usr/bin/env python3
"""Average lot size on each corridor segment, from King County parcel data.
Geometry is in WA State Plane feet (EPSG 2926), so the bounding box gives each
lot's frontage (dimension parallel to the street) and depth (perpendicular):
  - Stone Way N runs north-south  -> frontage = north-south extent (y)
  - N/NE 45th St runs east-west    -> frontage = east-west extent (x)
"""
import json, csv, statistics as st

def load(path, street_axis):
    """street_axis: 'y' if street runs N-S (frontage=y), 'x' if E-W (frontage=x)."""
    d = json.load(open(path))
    by_pin = {}
    for f in d['features']:
        a = f['attributes']
        pin = a['PIN']
        lot = a.get('LOTSQFT') or 0
        if lot <= 0:
            continue
        rings = f.get('geometry', {}).get('rings') or []
        xs = [p[0] for r in rings for p in r]
        ys = [p[1] for r in rings for p in r]
        if not xs:
            continue
        w_x = max(xs) - min(xs)   # east-west extent (ft)
        w_y = max(ys) - min(ys)   # north-south extent (ft)
        frontage = w_y if street_axis == 'y' else w_x
        depth    = w_x if street_axis == 'y' else w_y
        by_pin[pin] = {'pin': pin, 'address': a['ADDR_FULL'], 'proptype': a['PROPTYPE'],
                       'lotsqft': lot, 'frontage_ft': round(frontage, 1),
                       'depth_ft': round(depth, 1)}
    return list(by_pin.values())

sw = load('parcels_stoneway.json', 'y')
s45 = load('parcels_45th.json', 'x')

def stats(rows, name):
    lots = [r['lotsqft'] for r in rows]
    fr = [r['frontage_ft'] for r in rows]
    dp = [r['depth_ft'] for r in rows]
    s = {'name': name, 'n': len(rows),
         'mean': round(st.mean(lots)), 'median': round(st.median(lots)),
         'total': sum(lots), 'min': min(lots), 'max': max(lots),
         'mean_frontage': round(st.mean(fr), 1), 'mean_depth': round(st.mean(dp), 1),
         'median_frontage': round(st.median(fr), 1), 'median_depth': round(st.median(dp), 1)}
    return s

S_SW, S_45 = stats(sw, 'Stone Way N'), stats(s45, 'N/NE 45th St')
for s in (S_SW, S_45):
    print(f"{s['name']:14}: n={s['n']:3}  mean={s['mean']:>7,} sqft  median={s['median']:>7,} sqft"
          f"  | frontage~{s['mean_frontage']:.0f}ft depth~{s['mean_depth']:.0f}ft  (range {s['min']:,}-{s['max']:,})")
print(f"Stone Way mean lot is {S_SW['mean']/S_45['mean']:.1f}x the 45th St mean; "
      f"median {S_SW['median']/S_45['median']:.1f}x")

# per-parcel CSV
with open('lots_by_corridor.csv', 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['corridor', 'address', 'pin', 'proptype', 'lotsqft', 'frontage_ft', 'depth_ft'])
    for r in sorted(sw, key=lambda r: r['address']):
        w.writerow(['Stone Way N', r['address'], r['pin'], r['proptype'], r['lotsqft'], r['frontage_ft'], r['depth_ft']])
    for r in sorted(s45, key=lambda r: r['address']):
        w.writerow(['N/NE 45th St', r['address'], r['pin'], r['proptype'], r['lotsqft'], r['frontage_ft'], r['depth_ft']])

json.dump({'stoneway': {'stats': S_SW, 'lots': sorted(sw, key=lambda r: -r['lotsqft'])},
           'st45': {'stats': S_45, 'lots': sorted(s45, key=lambda r: -r['lotsqft'])}},
          open('lots_series.json', 'w'))
print('wrote lots_by_corridor.csv, lots_series.json')
