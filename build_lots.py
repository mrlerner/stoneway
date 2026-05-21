#!/usr/bin/env python3
"""Render lot_sizes.html: a to-scale, horizontal comparison of lot sizes on
Stone Way N vs N/NE 45th St. The headline visual draws an ACTUAL, contiguous
stretch of each street (both sides, real parcel positions and sizes) at the same
pixels-per-foot scale, so the reader sees the real grain of each street."""
import json, csv, datetime, re, statistics as st

d = json.load(open('lots_series.json'))
SW, S45 = d['stoneway'], d['st45']
C_SW, C_45 = '#c0392b', '#2c6fbb'
SCALE = 1.15          # pixels per foot (shared by every drawing)
WINDOW_FT = 720       # length of street frontage shown in the real stretch

def load_parcels(path, along):
    """along='y' for a N-S street (Stone Way), 'x' for an E-W street (45th).
    Returns parcels with along-street position (s) and perpendicular center (pc),
    all in State Plane feet."""
    raw = json.load(open(path))
    out = {}
    for f in raw['features']:
        a = f['attributes']; lot = a.get('LOTSQFT') or 0
        if lot <= 0:
            continue
        rings = f.get('geometry', {}).get('rings') or []
        xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
        if not xs:
            continue
        if along == 'y':
            s0, s1, p0, p1 = min(ys), max(ys), min(xs), max(xs)
        else:
            s0, s1, p0, p1 = min(xs), max(xs), min(ys), max(ys)
        m = re.match(r'(\d+)', a['ADDR_FULL'].strip())
        out[a['PIN']] = dict(addr=a['ADDR_FULL'].strip(), hn=int(m.group(1)) if m else 0,
                             area=lot, s0=s0, s1=s1, front=s1 - s0, depth=p1 - p0,
                             pc=(p0 + p1) / 2, sc=(s0 + s1) / 2)
    return list(out.values())

def choose_window(parcels):
    """Pick the WINDOW_FT-long run whose median lot area is closest to the
    street's overall median (the most 'typical' stretch), preferring more lots.
    Blocks dominated by an unusually large parcel (> 4x the overall median) are
    skipped so the stretch reflects the typical grain, not an anomaly."""
    overall = st.median([p['area'] for p in parcels])
    cap = overall * 4
    starts = sorted(p['sc'] for p in parcels)
    best = None
    for require_cap in (True, False):           # relax the cap only if nothing qualifies
        for start in starts:
            win = [p for p in parcels if start <= p['sc'] <= start + WINDOW_FT]
            if len(win) < 6:
                continue
            if require_cap and max(p['area'] for p in win) > cap:
                continue
            score = (abs(st.median([p['area'] for p in win]) - overall), -len(win))
            if best is None or score < best[0]:
                best = (score, win)
        if best:
            break
    return best[1] if best else parcels

def _blockface(parcels, along):
    """Pick a representative window, then return the real lots along the SINGLE
    side of the street that has more parcels, in geographic order (a clean
    blockface with no cross-street gaps), plus a human side label."""
    win = choose_window(parcels)
    cl = st.median([p['pc'] for p in parcels])
    lo = [p for p in win if p['pc'] < cl]
    hi = [p for p in win if p['pc'] >= cl]
    side = hi if len(hi) >= len(lo) else lo
    side = sorted(side, key=lambda p: p['sc'])
    is_hi = side is hi
    if along == 'y':   # Stone Way runs N-S; perpendicular is easting -> E/W sides
        label = 'east side' if is_hi else 'west side'
    else:              # 45th runs E-W; perpendicular is northing -> N/S sides
        label = 'north side' if is_hi else 'south side'
    return dict(lots=side, label=label,
                run_ft=sum(p['front'] for p in side),
                dmax=max((p['depth'] for p in side), default=60),
                hns=sorted(p['hn'] for p in side))

def draw_both():
    """Both blockfaces in ONE SVG so the pixels-per-foot scale is genuinely shared."""
    gsw = _blockface(sw_parcels, 'y'); g45 = _blockface(s45_parcels, 'x')
    padx = 16
    plotw = max(gsw['run_ft'], g45['run_ft']) * SCALE
    W = padx * 2 + plotw
    s = [f'<svg viewBox="0 0 {W:.0f} {{H}}" width="100%" font-family="system-ui,sans-serif">']
    y = 0
    for name, col, g in [('Stone Way N', C_SW, gsw), ('N/NE 45th St', C_45, g45)]:
        y += 24
        street_y = y                      # street line at top; lots hang below
        s.append(f'<text x="{padx}" y="{y-9:.0f}" font-size="14" font-weight="700" fill="{col}">{name} '
                 f'<tspan font-weight="400" font-size="11" fill="#888">&middot; {g["label"]}, {g["hns"][0]}&ndash;{g["hns"][-1]} block</tspan></text>')
        s.append(f'<line x1="{padx}" y1="{street_y:.1f}" x2="{padx+g["run_ft"]*SCALE:.0f}" y2="{street_y:.1f}" stroke="#333" stroke-width="2.5"/>')
        x = padx
        for p in g['lots']:
            w = max(p['front'] * SCALE, 1); h = p['depth'] * SCALE
            s.append(f'<rect x="{x:.1f}" y="{street_y:.1f}" width="{w-1.2:.1f}" height="{h:.1f}" '
                     f'fill="{col}" fill-opacity="0.18" stroke="{col}" stroke-width="1.3"/>')
            if w > 30:
                s.append(f'<text x="{x+w/2:.1f}" y="{street_y+15:.1f}" text-anchor="middle" font-size="9.5" fill="#555">{p["area"]:,}</text>')
                s.append(f'<text x="{x+w/2:.1f}" y="{street_y+h/2+4:.1f}" text-anchor="middle" font-size="8.5" fill="#aaa">{p["front"]:.0f}&times;{p["depth"]:.0f}ft</text>')
            x += w
        y = street_y + g['dmax'] * SCALE + 30
    sb = 100 * SCALE; by = y + 2
    s.append(f'<line x1="{padx}" y1="{by:.0f}" x2="{padx+sb:.0f}" y2="{by:.0f}" stroke="#333" stroke-width="2"/>')
    s.append(f'<line x1="{padx}" y1="{by-4:.0f}" x2="{padx}" y2="{by+4:.0f}" stroke="#333" stroke-width="2"/>')
    s.append(f'<line x1="{padx+sb:.0f}" y1="{by-4:.0f}" x2="{padx+sb:.0f}" y2="{by+4:.0f}" stroke="#333" stroke-width="2"/>')
    s.append(f'<text x="{padx+sb+8:.0f}" y="{by+4:.0f}" font-size="10" fill="#666">100 ft &middot; each box is one real lot (area in sqft, frontage&times;depth); street runs along the top line</text>')
    s.append('</svg>')
    return '\n'.join(s).replace('{H}', f'{y+14:.0f}')

def hero():
    """The two typical lots, same scale, frontage horizontal."""
    pad = 20
    fr_sw, dp_sw = SW['stats']['median_frontage']*SCALE, SW['stats']['median_depth']*SCALE
    fr_45, dp_45 = S45['stats']['median_frontage']*SCALE, S45['stats']['median_depth']*SCALE
    W = pad*2 + max(fr_sw, fr_45) + 180
    H = pad*2 + dp_sw + dp_45 + 30
    s = [f'<svg viewBox="0 0 {W:.0f} {H:.0f}" width="100%" font-family="system-ui,sans-serif">']
    y = pad
    for name, fr, dp, area, col in [('Stone Way N', fr_sw, dp_sw, SW['stats']['median'], C_SW),
                                    ('N/NE 45th St', fr_45, dp_45, S45['stats']['median'], C_45)]:
        s.append(f'<rect x="{pad}" y="{y:.1f}" width="{fr:.1f}" height="{dp:.1f}" '
                 f'fill="{col}" fill-opacity="0.2" stroke="{col}" stroke-width="2"/>')
        s.append(f'<text x="{pad+fr+14:.0f}" y="{y+18:.0f}" font-size="14" font-weight="700" fill="{col}">{name}</text>')
        s.append(f'<text x="{pad+fr+14:.0f}" y="{y+38:.0f}" font-size="12" fill="#555">median lot {area:,} sqft</text>')
        y += dp + 30
    s.append('</svg>')
    return '\n'.join(s)

def lot_table():
    rows = list(csv.DictReader(open('lots_by_corridor.csv')))
    out = ['<h2>Every lot in the count</h2>',
           '<p class="sub">All parcels whose primary address is on the segment, with King County lot square footage.</p>']
    for corr, col in [('Stone Way N', C_SW), ('N/NE 45th St', C_45)]:
        cr = [r for r in rows if r['corridor'] == corr]
        cr.sort(key=lambda r: -int(r['lotsqft']))
        out.append(f'<h3 style="color:{col};margin:14px 0 6px">{corr} <span style="color:#999;font-weight:400;font-size:13px">({len(cr)} lots)</span></h3>')
        out.append('<table class="pt"><thead><tr><th>Address</th><th>Lot sqft</th><th>Frontage ft</th><th>Depth ft</th><th>Type</th><th>PIN</th></tr></thead><tbody>')
        for r in cr:
            out.append(f'<tr><td>{r["address"]}</td><td>{int(r["lotsqft"]):,}</td><td>{r["frontage_ft"]}</td>'
                       f'<td>{r["depth_ft"]}</td><td>{r["proptype"]}</td><td>{r["pin"]}</td></tr>')
        out.append('</tbody></table>')
    return '\n'.join(out)

sw_parcels = load_parcels('parcels_stoneway.json', 'y')
s45_parcels = load_parcels('parcels_45th.json', 'x')
today = datetime.date.today().isoformat()
mr = SW['stats']['mean']/S45['stats']['mean']
mdr = SW['stats']['median']/S45['stats']['median']
html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Lot sizes: Stone Way N vs 45th St</title>
<style>
 body{{font-family:system-ui,sans-serif;max-width:920px;margin:30px auto;padding:0 16px;color:#222;line-height:1.5}}
 h1{{font-size:22px;margin-bottom:2px}} h2{{font-size:15px;margin-top:34px;color:#444}}
 .sub{{color:#777;font-size:13px;margin-top:0}}
 .cards{{display:flex;gap:14px;margin:18px 0}}
 .card{{flex:1;border:1px solid #e5e5e5;border-radius:10px;padding:14px 16px}}
 .card .n{{font-size:28px;font-weight:800}} .card .l{{font-size:13px;color:#666}}
 .sw{{color:{C_SW}}} .st{{color:{C_45}}}
 .panel{{border:1px solid #eee;border-radius:10px;padding:14px 16px;margin:10px 0;background:#fcfcfc}}
 .note{{background:#fafafa;border:1px solid #eee;border-radius:8px;padding:12px 16px;font-size:12.5px;color:#555}}
 .note li{{margin:3px 0}}
 table.pt{{border-collapse:collapse;width:100%;font-size:12px;margin-bottom:10px}}
 table.pt th,table.pt td{{border-bottom:1px solid #eee;padding:4px 6px;text-align:left}}
 table.pt th{{background:#f7f7f7;font-size:11px;color:#555}}
 table.pt td:nth-child(2),table.pt td:nth-child(3),table.pt td:nth-child(4){{text-align:right}}
 a{{color:#2c6fbb}}
</style></head><body>
<p class="sub"><a href="index.html">&larr; back to the units dashboard</a></p>
<h1>Lot sizes: Stone Way N vs N/NE 45th St</h1>
<p class="sub">Wallingford, Seattle &middot; King County parcels on each studied segment &middot; built {today}</p>

<div class="cards">
 <div class="card"><div class="n sw">{SW['stats']['median']:,}</div><div class="l">median lot, <b>Stone Way N</b> (sqft)<br>mean {SW['stats']['mean']:,} &middot; {SW['stats']['n']} lots</div></div>
 <div class="card"><div class="n st">{S45['stats']['median']:,}</div><div class="l">median lot, <b>N/NE 45th St</b> (sqft)<br>mean {S45['stats']['mean']:,} &middot; {S45['stats']['n']} lots</div></div>
 <div class="card"><div class="n">{mdr:.1f}&times;</div><div class="l">larger typical lot on<br>Stone Way (by median)</div></div>
</div>

<h2>An actual stretch of each street (real lots, to scale)</h2>
<p class="sub">A representative block on each street &mdash; the real, consecutive lots along one side, in order, drawn to the same scale. Each box is an actual parcel sized by its real frontage and depth. Stone Way's lots are visibly bigger and fewer; 45th's are narrow and many.</p>
<div class="panel">{draw_both()}</div>

<h2>Typical lot, side by side (same scale)</h2>
<div class="panel">{hero()}</div>

<div class="note">
<b>Method &amp; caveats</b>
<ul>
 <li><b>Source:</b> King County <code>parcel_address_area</code> feature service (lot square footage + parcel geometry), pulled {today}.</li>
 <li><b>Which lots:</b> parcels whose <i>primary</i> address is on the segment &mdash; Stone Way N #3400&ndash;4499 (N 34th&rarr;N 45th); 45th St between Stone Way and I-5 (same boundaries as the units analysis). One row per parcel; records with zero lot area excluded.</li>
 <li><b>The &ldquo;actual stretch&rdquo;</b> is auto-selected: of every ~{WINDOW_FT} ft run, it shows the one whose median lot area is closest to the street's overall median (skipping blocks dominated by an unusually large parcel) &mdash; a typical, not cherry-picked, block.</li>
 <li><b>One side shown:</b> the blockface uses the consecutive lots along whichever side of the street has more parcels in that block, in geographic order, butted together &mdash; so it reads as a clean row without cross-street gaps. The other side's grain is similar.</li>
 <li><b>Median vs mean:</b> both streets have a few very large parcels (e.g. 1815 N 45th at 75,112 sqft; 4400 Stone Way at 60,088), so the <b>median</b> is the better &ldquo;typical lot&rdquo; figure. Stone Way leads on both (median {mdr:.1f}&times;, mean {mr:.1f}&times;).</li>
 <li><b>Lot rectangles</b> are each parcel's bounding box (frontage along the street &times; depth), from geometry in State Plane feet; irregular lots are slightly overstated.</li>
 <li><b>Orientation:</b> both streets are drawn horizontally for comparison. Stone Way actually runs north&ndash;south; 45th runs east&ndash;west.</li>
</ul>
</div>

{lot_table()}
</body></html>"""
open('lot_sizes.html', 'w').write(html)
print('wrote lot_sizes.html')
# report the chosen stretches for transparency
for parcels, along, nm in [(sw_parcels, 'y', 'Stone Way'), (s45_parcels, 'x', '45th')]:
    win = choose_window(parcels)
    hns = sorted(p['hn'] for p in win)
    print(f"  {nm}: chose {hns[0]}-{hns[-1]} block, {len(win)} lots, "
          f"median {st.median([p['area'] for p in win]):,.0f} sqft")
