#!/usr/bin/env python3
"""Double-count check: are any two COUNTED permits actually the same building?
Strategy: (1) confirm permit numbers are unique; (2) cluster counted permits by
physical location (rounded lat/lng ~ within a building footprint) and by address;
print any cluster with >1 counted permit so it can be eyeballed against descriptions.
"""
import json, csv
from collections import defaultdict

rows = list(csv.DictReader(open('permits_by_corridor.csv')))
counted = [r for r in rows if r['counted'] == 'True']

# 1. unique permit numbers?
nums = [r['permitnum'] for r in counted]
print(f'counted permits: {len(nums)}; unique permit numbers: {len(set(nums))}')
assert len(nums) == len(set(nums)), 'DUPLICATE PERMIT NUMBER!'

# 2. cluster by ~location (4 decimal places ~ 11m) and by street address
by_loc = defaultdict(list)
by_addr = defaultdict(list)
# need lat/lng -> re-read from raw json keyed by permitnum
raw = {}
for f in ['stoneway2.json', 'st45_2.json']:
    for r in json.load(open(f)):
        raw[r['permitnum']] = r
for r in counted:
    rr = raw[r['permitnum']]
    key = (round(float(rr['latitude']), 4), round(float(rr['longitude']), 4))
    by_loc[key].append(r)
    by_addr[r['address']].append(r)

def show(title, groups):
    hits = {k: v for k, v in groups.items() if len(v) > 1}
    print(f'\n{title}: {len(hits)} cluster(s) with >1 counted permit')
    for k, v in hits.items():
        print(f'  @ {k}:')
        for r in v:
            print(f'     {r["issued_year"]} {r["address"]:18} {r["permitnum"]:12} '
                  f'net={float(r["net_units"]):.0f}  | {r["description"][:80]}')

show('Same exact address', by_addr)
show('Same location (~11m, possibly one project across addresses)', by_loc)

# 3. nearby clusters within ~40m (3 decimals) - looser, catches one project / adjacent lots
by_loc3 = defaultdict(list)
for r in counted:
    rr = raw[r['permitnum']]
    key = (round(float(rr['latitude']), 3), round(float(rr['longitude']), 3))
    by_loc3[key].append(r)
show('Within ~80m block (adjacent lots - verify these are distinct buildings)', by_loc3)
