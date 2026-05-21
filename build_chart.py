#!/usr/bin/env python3
"""Render a self-contained HTML chart from series.json (no external deps)."""
import json, datetime

d = json.load(open('series.json'))
years = d['years']
cum = d['cum']
net = {k: {int(y): v for y, v in vals.items()} for k, vals in d['net_by'].items()}
totals = d['totals']; pipe = d['pipeline']; base = d.get('baseline', {})
C_SW, C_45 = '#c0392b', '#2c6fbb'   # Stone Way red, 45th blue

# ---------- cumulative line chart ----------
def line_chart():
    W, H = 860, 380
    ml, mr, mt, mb = 60, 20, 20, 40
    pw, ph = W-ml-mr, H-mt-mb
    ymax = max(max(cum['Stone Way N']), max(cum['N/NE 45th St']))
    ymax = (int(ymax/250)+1)*250
    def X(i): return ml + pw*i/(len(years)-1)
    def Y(v): return mt + ph*(1 - v/ymax)
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="system-ui,sans-serif">']
    # gridlines + y labels
    step = 250
    for gv in range(0, ymax+1, step):
        y = Y(gv)
        s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{W-mr}" y2="{y:.1f}" stroke="#eee"/>')
        s.append(f'<text x="{ml-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="#888">{gv}</text>')
    # x labels (every other year)
    for i, yr in enumerate(years):
        if yr % 2 == 0:
            s.append(f'<text x="{X(i):.1f}" y="{H-mb+20}" text-anchor="middle" font-size="10" fill="#888">{yr}</text>')
    for key, col in [('Stone Way N', C_SW), ('N/NE 45th St', C_45)]:
        pts = ' '.join(f'{X(i):.1f},{Y(cum[key][i]):.1f}' for i in range(len(years)))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"/>')
        # end dot + label
        ex, ey = X(len(years)-1), Y(cum[key][-1])
        s.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{col}"/>')
        s.append(f'<text x="{ex-6:.1f}" y="{ey-8:.1f}" text-anchor="end" font-size="13" font-weight="700" fill="{col}">{cum[key][-1]:.0f}</text>')
    s.append('</svg>')
    return '\n'.join(s)

# ---------- grouped bar chart (per-year net added) ----------
def bar_chart():
    W, H = 860, 320
    ml, mr, mt, mb = 50, 20, 20, 40
    pw, ph = W-ml-mr, H-mt-mb
    ymax = max(max(net['Stone Way N'].values()), max(net['N/NE 45th St'].values()))
    ymax = (int(ymax/100)+1)*100
    gw = pw/len(years)
    bw = gw*0.36
    def Y(v): return mt + ph*(1 - v/ymax)
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="system-ui,sans-serif">']
    for gv in range(0, ymax+1, 100):
        y = Y(gv)
        s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{W-mr}" y2="{y:.1f}" stroke="#eee"/>')
        s.append(f'<text x="{ml-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="#888">{gv}</text>')
    base = Y(0)
    for i, yr in enumerate(years):
        gx = ml + gw*i + gw*0.5
        for off, key, col in [(-bw, 'Stone Way N', C_SW), (0, 'N/NE 45th St', C_45)]:
            v = net[key][yr]
            if v <= 0: continue
            h = base - Y(v)
            s.append(f'<rect x="{gx+off:.1f}" y="{Y(v):.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{col}"/>')
        if yr % 2 == 0:
            s.append(f'<text x="{gx:.1f}" y="{H-mb+20}" text-anchor="middle" font-size="10" fill="#888">{yr}</text>')
    s.append('</svg>')
    return '\n'.join(s)

import csv as _csv
def permit_tables():
    rows = [r for r in _csv.DictReader(open('permits_by_corridor.csv')) if r['counted'] == 'True']
    out = ['<h2>The permits behind the totals (spot-check)</h2>',
           '<p class="sub">Only construction (building) permits that add net housing units &mdash; '
           'demolition and not-yet-issued permits are not shown (they are in the CSV). '
           'Click a permit number to open its record on the Seattle permit portal.</p>']
    for corr, col in [('Stone Way N', C_SW), ('N/NE 45th St', C_45)]:
        cr = [r for r in rows if r['corridor'] == corr]
        cr.sort(key=lambda r: (r['issued_date'] or '9999', r['address']))
        tot = sum(float(r['net_units']) for r in cr)
        out.append(f'<h3 style="color:{col};margin:18px 0 6px">{corr} '
                   f'<span style="color:#999;font-weight:400;font-size:13px">'
                   f'({len(cr)} buildings &middot; {tot:.0f} net units)</span></h3>')
        out.append('<table class="pt"><thead><tr>'
                   '<th>Yr</th><th>Address</th><th>Permit #</th><th>Type</th>'
                   '<th>+units</th><th>&minus;units</th><th>Net</th><th>Status</th>'
                   '<th>Description</th></tr></thead><tbody>')
        for r in cr:
            url = f"https://services.seattle.gov/portal/customize/LinkToRecord.aspx?altId={r['permitnum']}"
            out.append(
                f'<tr><td>{r["issued_year"]}</td><td>{r["address"]}</td>'
                f'<td><a href="{url}" target="_blank">{r["permitnum"]}</a></td>'
                f'<td>{r["permittype"]}</td>'
                f'<td>{float(r["units_added"]):.0f}</td><td>{float(r["units_removed"]):.0f}</td>'
                f'<td><b>{float(r["net_units"]):.0f}</b></td><td>{r["status"]}</td>'
                f'<td>{r["description"]}</td></tr>')
        out.append('</tbody></table>')
    return '\n'.join(out)

ncounted = sum(1 for r in _csv.DictReader(open('permits_by_corridor.csv')) if r['counted'] == 'True')
ratio = totals['Stone Way N']/totals['N/NE 45th St']
today = datetime.date.today().isoformat()
html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Wallingford residential growth: Stone Way N vs 45th St</title>
<style>
 body{{font-family:system-ui,sans-serif;max-width:920px;margin:30px auto;padding:0 16px;color:#222;line-height:1.5}}
 h1{{font-size:22px;margin-bottom:2px}} h2{{font-size:15px;margin-top:34px;color:#444}}
 .sub{{color:#777;font-size:13px;margin-top:0}}
 .cards{{display:flex;gap:14px;margin:18px 0}}
 .card{{flex:1;border:1px solid #e5e5e5;border-radius:10px;padding:14px 16px}}
 .card .n{{font-size:30px;font-weight:800}} .card .l{{font-size:13px;color:#666}}
 .sw{{color:{C_SW}}} .st{{color:{C_45}}}
 .legend span{{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:5px;vertical-align:middle}}
 .note{{background:#fafafa;border:1px solid #eee;border-radius:8px;padding:12px 16px;font-size:12.5px;color:#555}}
 .note li{{margin:3px 0}}
 table.pt{{border-collapse:collapse;width:100%;font-size:12px;margin-bottom:10px}}
 table.pt th,table.pt td{{border-bottom:1px solid #eee;padding:4px 6px;text-align:left;vertical-align:top}}
 table.pt th{{background:#f7f7f7;font-size:11px;color:#555;position:sticky;top:0}}
 table.pt td:nth-child(5),table.pt td:nth-child(6),table.pt td:nth-child(7){{text-align:right}}
 table.pt tr.ex{{color:#aaa}} table.pt tr.ex a{{color:#9bb}}
 table.pt td:last-child{{color:#888;max-width:280px}}
</style></head><body>
<h1>Residential units added: Stone Way N vs N/NE 45th St</h1>
<p class="sub">Wallingford, Seattle &middot; net new units from issued construction permits, 2011&ndash;2025 &middot; built {today}</p>
<p class="sub">See also: <a href="lot_sizes.html">lot-size comparison &rarr;</a></p>

<div class="cards">
 <div class="card"><div class="n sw">{totals['Stone Way N']:.0f}</div><div class="l">net units added on <b>Stone Way N</b><br>(N 34th &rarr; N 45th)</div></div>
 <div class="card"><div class="n st">{totals['N/NE 45th St']:.0f}</div><div class="l">net units added on <b>N/NE 45th St</b><br>(Stone Way &rarr; I-5)</div></div>
 <div class="card"><div class="n">{ratio:.1f}&times;</div><div class="l">more units added on<br>Stone Way than 45th</div></div>
</div>

<p class="legend"><span style="background:{C_SW}"></span>Stone Way N &nbsp;&nbsp;<span style="background:{C_45}"></span>N/NE 45th St</p>

<h2>Cumulative net units added over time</h2>
{line_chart()}

<h2>Net units added per year</h2>
{bar_chart()}

<div class="note">
<b>Method &amp; caveats</b>
<ul>
 <li><b>Source:</b> City of Seattle Building Permits open data (dataset 76t5-zqzr), pulled {today}.</li>
 <li><b>What's counted:</b> issued <i>construction</i> permits (new buildings + additions) with a net change in housing units. Net = units added &minus; units removed on each permit.</li>
 <li><b>Demolition permits excluded</b> &mdash; Seattle's data spuriously copies a project's unit count onto its demolition permits, so including them would multiply-count the same building (e.g. 4009/4011/4015 Stone Way are one 125-unit project, not 437).</li>
 <li><b>Double-count check:</b> all {ncounted} counted permits have unique permit numbers, no two share an address, and no two share a location within ~11m &mdash; so no building is counted twice. The only cases where counted permits sit on the same block were checked individually against their descriptions and confirmed to be separate buildings.</li>
 <li><b>Corridor definition:</b> properties addressed on each street within the segment (Stone Way N #3400&ndash;4499; 45th St between Stone Way and I-5). A half-block-deep definition would add a few side-street-addressed projects but does not change the picture.</li>
 <li><b>Timing</b> = permit <i>issued</i> year (when construction was approved). Not-yet-issued projects in review are excluded: ~{pipe['N/NE 45th St']:.0f} units on 45th St and ~{pipe['Stone Way N']:.0f} on Stone Way are in the pipeline.</li>
 <li><b>Window</b> = last 15 years (2011&ndash;2025); permitting before 2011 was sparse. The few earlier units are carried as a starting baseline (Stone Way {base.get('Stone Way N', 0):.0f}, 45th {base.get('N/NE 45th St', 0):.0f}), so the cumulative totals still reflect all activity back to 2004.</li>
 <li>Permit counts are a close proxy for units built but not identical (a few issued permits expire unbuilt). Cross-check totals against King County Assessor apartment/condo files for a built-stock validation.</li>
</ul>
</div>

{permit_tables()}
</body></html>"""
open('index.html', 'w').write(html)
print('wrote index.html')
