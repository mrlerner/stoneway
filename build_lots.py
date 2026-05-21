#!/usr/bin/env python3
"""Render lot_sizes.html: a to-scale, horizontal comparison of typical lot sizes
on Stone Way N vs N/NE 45th St. Both streets are drawn horizontally (frontage
left-to-right) at the SAME pixels-per-foot scale, so the size gap is visible."""
import json, csv, datetime

d = json.load(open('lots_series.json'))
SW, S45 = d['stoneway'], d['st45']
C_SW, C_45 = '#c0392b', '#2c6fbb'
SCALE = 1.45          # pixels per foot (shared by every drawing)
STRETCH_FT = 540      # length of street frontage shown in the representative block

def rep_block():
    """Two horizontal street bands, same scale, tiled with each street's typical lot."""
    pad_l, pad_t, gap, lbl = 16, 26, 46, 150
    roww = STRETCH_FT * SCALE
    W = pad_l + lbl + roww + 20
    streets = [('N/NE 45th St', S45, C_45), ('Stone Way N', SW, C_SW)]
    rowh = max(s['stats']['median_depth'] for _, s, _ in streets) * SCALE + gap
    H = pad_t + rowh * 2 + 30
    s = [f'<svg viewBox="0 0 {W:.0f} {H:.0f}" width="100%" font-family="system-ui,sans-serif">']
    for i, (name, data, col) in enumerate(streets):
        stt = data['stats']
        fr = stt['median_frontage'] * SCALE
        dp = stt['median_depth'] * SCALE
        y0 = pad_t + i * rowh
        base = y0 + dp                      # street line (lots sit on it)
        # label
        s.append(f'<text x="{pad_l}" y="{y0+dp/2-6:.0f}" font-size="14" font-weight="700" fill="{col}">{name}</text>')
        s.append(f'<text x="{pad_l}" y="{y0+dp/2+12:.0f}" font-size="11" fill="#666">typ. {stt["median_frontage"]:.0f}&times;{stt["median_depth"]:.0f} ft</text>')
        s.append(f'<text x="{pad_l}" y="{y0+dp/2+27:.0f}" font-size="11" fill="#666">median {stt["median"]:,} sqft</text>')
        x = pad_l + lbl
        xend = x + roww
        n = 0
        while x < xend - 2:
            w = min(fr, xend - x)
            s.append(f'<rect x="{x:.1f}" y="{base-dp:.1f}" width="{w-2:.1f}" height="{dp:.1f}" '
                     f'fill="{col}" fill-opacity="0.18" stroke="{col}" stroke-width="1.5"/>')
            x += fr; n += 1
        # street line
        s.append(f'<line x1="{pad_l+lbl}" y1="{base:.1f}" x2="{xend:.1f}" y2="{base:.1f}" stroke="#333" stroke-width="2"/>')
        s.append(f'<text x="{xend:.0f}" y="{base+16:.0f}" text-anchor="end" font-size="11" fill="#999">~{n} lots in {STRETCH_FT} ft of street</text>')
    # scale bar (100 ft)
    sb = 100 * SCALE
    sy = H - 12
    s.append(f'<line x1="{pad_l+lbl}" y1="{sy}" x2="{pad_l+lbl+sb:.0f}" y2="{sy}" stroke="#333" stroke-width="2"/>')
    s.append(f'<line x1="{pad_l+lbl}" y1="{sy-4}" x2="{pad_l+lbl}" y2="{sy+4}" stroke="#333" stroke-width="2"/>')
    s.append(f'<line x1="{pad_l+lbl+sb:.0f}" y1="{sy-4}" x2="{pad_l+lbl+sb:.0f}" y2="{sy+4}" stroke="#333" stroke-width="2"/>')
    s.append(f'<text x="{pad_l+lbl+sb+8:.0f}" y="{sy+4}" font-size="11" fill="#666">100 ft</text>')
    s.append('</svg>')
    return '\n'.join(s)

def hero():
    """The two typical lots, one on top of the other, same scale, frontage horizontal."""
    pad = 20
    fr_sw, dp_sw = SW['stats']['median_frontage']*SCALE, SW['stats']['median_depth']*SCALE
    fr_45, dp_45 = S45['stats']['median_frontage']*SCALE, S45['stats']['median_depth']*SCALE
    W = pad*2 + max(fr_sw, fr_45) + 170
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

<h2>Typical lot, side by side (same scale)</h2>
<div class="panel">{hero()}</div>

<h2>A representative stretch of each street</h2>
<p class="sub">Same {STRETCH_FT} ft of street frontage, drawn at the same scale. Stone Way fits fewer, larger lots; 45th packs in more, smaller ones.</p>
<div class="panel">{rep_block()}</div>

<div class="note">
<b>Method &amp; caveats</b>
<ul>
 <li><b>Source:</b> King County <code>parcel_address_area</code> feature service (lot square footage + parcel geometry), pulled {today}.</li>
 <li><b>Which lots:</b> parcels whose <i>primary</i> address is on the segment &mdash; Stone Way N #3400&ndash;4499 (N 34th&rarr;N 45th); 45th St between Stone Way and I-5 (same boundaries as the units analysis). One row per parcel; records with zero lot area excluded.</li>
 <li><b>Median vs mean:</b> both streets have a few very large parcels (e.g. 1815 N 45th at 75,112 sqft; 4400 Stone Way at 60,088), so the <b>median</b> is the better &ldquo;typical lot&rdquo; figure. Stone Way leads on both (median {mdr:.1f}&times;, mean {mr:.1f}&times;).</li>
 <li><b>Frontage &amp; depth</b> are each parcel's bounding-box dimensions along/perpendicular to the street (from geometry in State Plane feet); they slightly overstate irregular lots.</li>
 <li><b>Orientation:</b> both streets are drawn horizontally for comparison. Stone Way actually runs north&ndash;south; 45th runs east&ndash;west.</li>
</ul>
</div>

{lot_table()}
</body></html>"""
open('lot_sizes.html', 'w').write(html)
print('wrote lot_sizes.html')
