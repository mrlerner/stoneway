#!/usr/bin/env python3
"""Boundary verification: confirm counted addresses fall in the intended segments.
  45th St: I-5 (east) -> Stone Way (west)
  Stone Way N: N 45th St (north) -> N 34th St / water (south)
Shows counted addresses plus the nearest EXCLUDED neighbors past each boundary,
so the cut points are visible.
"""
import json, re

STONE_W = -122.343    # Stone Way N longitude (west boundary of 45th segment)
I5_E    = -122.3235   # I-5 longitude (east boundary of 45th segment)

def load(*fs):
    out = []
    for f in fs:
        out += json.load(open(f))
    d = {r['permitnum']: r for r in out}
    return list(d.values())

def hn(a):
    m = re.match(r'\s*(\d+)', a or '')
    return int(m.group(1)) if m else None

def fnum(r, k):
    try: return float(r.get(k) or 0)
    except: return 0.0

def is_building(r):
    return r.get('permittypemapped') == 'Building' and (r.get('issueddate') or '')

rows = load('stoneway2.json', 'st45_2.json')

print('='*78)
print('45th ST  — want: I-5 (lng %.4f, east)  →  Stone Way (lng %.4f, west)' % (I5_E, STONE_W))
print('='*78)
s45 = [r for r in rows if '45TH ST' in (r['originaladdress1'] or '').upper()
       and 47.659 <= fnum(r, 'latitude') <= 47.663]   # exclude 145th St mismatches
s45.sort(key=lambda r: fnum(r, 'longitude'))           # west -> east
print('  %-20s %-10s %-9s %s' % ('address', 'longitude', 'building?', 'in segment?'))
for r in s45:
    lng = fnum(r, 'longitude')
    inseg = STONE_W <= lng <= I5_E
    side = '' if inseg else ('  <-- WEST of Stone Way (excl)' if lng < STONE_W
                             else '  <-- EAST of I-5 (excl)')
    star = 'COUNTED' if (inseg and is_building(r) and fnum(r,'housingunitsadded')-fnum(r,'housingunitsremoved')!=0) else ''
    print('  %-20s %.5f  %-9s %-5s %-7s%s' % (
        r['originaladdress1'], lng,
        'yes' if r.get('permittypemapped')=='Building' else 'demo',
        'IN' if inseg else 'out', star, side))

print()
print('='*78)
print('STONE WAY N — want: N 45th St (#4500, north)  →  N 34th St / water (#3400, south)')
print('='*78)
sw = [r for r in rows if 'STONE WAY N' in (r['originaladdress1'] or '').upper()
      and 'STONE WAY NE' not in (r['originaladdress1'] or '').upper()]
sw.sort(key=lambda r: hn(r['originaladdress1']) or 0)   # south -> north by house #
print('  %-20s %-7s %-9s %s' % ('address', 'house#', 'building?', 'in segment (3400-4499)?'))
for r in sw:
    h = hn(r['originaladdress1'])
    inseg = h is not None and 3400 <= h <= 4499
    side = '' if inseg else ('  <-- NORTH of N 45th (excl)' if (h or 0) >= 4500
                             else '  <-- below #3400 (excl)')
    star = 'COUNTED' if (inseg and is_building(r) and fnum(r,'housingunitsadded')-fnum(r,'housingunitsremoved')!=0) else ''
    print('  %-20s %-7s %-9s %-5s %-7s%s' % (
        r['originaladdress1'], h,
        'yes' if r.get('permittypemapped')=='Building' else 'demo',
        'IN' if inseg else 'out', star, side))
