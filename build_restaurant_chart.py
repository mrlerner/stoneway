#!/usr/bin/env python3
"""Render a self-contained HTML chart of restaurants on Stone Way N vs 45th St
from restaurants_series.json (no external deps).

Honest framing: the source (King County active food-permit registry) only retains
currently-open establishments, so this is a SNAPSHOT of restaurants open now plus
the opening-year VINTAGE of those restaurants -- not a true historical stock that
would include since-closed restaurants. The caveat box says so plainly.
"""
import json, datetime, csv as _csv

d = json.load(open('restaurants_series.json'))
years = d['years']
cum = d['cum_by']
new = {k: {int(y): v for y, v in vals.items()} for k, vals in d['new_by'].items()}
open_now = d['open_now']
C_SW, C_45 = '#c0392b', '#2c6fbb'   # Stone Way red, 45th blue

# ---------- vintage line chart ----------
def line_chart():
    W, H = 860, 380
    ml, mr, mt, mb = 50, 20, 20, 40
    pw, ph = W-ml-mr, H-mt-mb
    ymax = max(max(cum['Stone Way N']), max(cum['N/NE 45th St']))
    ymax = (int(ymax/10)+1)*10
    def X(i): return ml + pw*i/(len(years)-1)
    def Y(v): return mt + ph*(1 - v/ymax)
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="system-ui,sans-serif">']
    for gv in range(0, ymax+1, 10):
        y = Y(gv)
        s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{W-mr}" y2="{y:.1f}" stroke="#eee"/>')
        s.append(f'<text x="{ml-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="#888">{gv}</text>')
    for i, yr in enumerate(years):
        if yr % 2 == 0:
            s.append(f'<text x="{X(i):.1f}" y="{H-mb+20}" text-anchor="middle" font-size="10" fill="#888">{yr}</text>')
    for key, col in [('Stone Way N', C_SW), ('N/NE 45th St', C_45)]:
        pts = ' '.join(f'{X(i):.1f},{Y(cum[key][i]):.1f}' for i in range(len(years)))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"/>')
        ex, ey = X(len(years)-1), Y(cum[key][-1])
        s.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{col}"/>')
        s.append(f'<text x="{ex-6:.1f}" y="{ey-8:.1f}" text-anchor="end" font-size="13" font-weight="700" fill="{col}">{cum[key][-1]:.0f}</text>')
    s.append('</svg>')
    return '\n'.join(s)

# ---------- grouped bar chart (new arrivals per year) ----------
def bar_chart():
    W, H = 860, 300
    ml, mr, mt, mb = 40, 20, 20, 40
    pw, ph = W-ml-mr, H-mt-mb
    ymax = max(max(new['Stone Way N'].values()), max(new['N/NE 45th St'].values()))
    ymax = max(ymax, 1)
    ymax = (int(ymax/2)+1)*2
    gw = pw/len(years)
    bw = gw*0.36
    def Y(v): return mt + ph*(1 - v/ymax)
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" font-family="system-ui,sans-serif">']
    for gv in range(0, ymax+1, 2):
        y = Y(gv)
        s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{W-mr}" y2="{y:.1f}" stroke="#eee"/>')
        s.append(f'<text x="{ml-8}" y="{y+4:.1f}" text-anchor="end" font-size="11" fill="#888">{gv}</text>')
    base = Y(0)
    for i, yr in enumerate(years):
        gx = ml + gw*i + gw*0.5
        for off, key, col in [(-bw, 'Stone Way N', C_SW), (0, 'N/NE 45th St', C_45)]:
            v = new[key][yr]
            if v <= 0: continue
            h = base - Y(v)
            s.append(f'<rect x="{gx+off:.1f}" y="{Y(v):.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{col}"/>')
        if yr % 2 == 0:
            s.append(f'<text x="{gx:.1f}" y="{H-mb+20}" text-anchor="middle" font-size="10" fill="#888">{yr}</text>')
    s.append('</svg>')
    return '\n'.join(s)

def rest_tables():
    rows = [r for r in _csv.DictReader(open('restaurants_by_corridor.csv')) if r['counted'] == 'True']
    out = ['<h2>The restaurants behind the totals (spot-check)</h2>',
           '<p class="sub">Every currently-open restaurant on each segment, with the year it '
           'first appears in King County inspection records (a proxy for when it opened). '
           'Sorted newest-first.</p>']
    for corr, col in [('Stone Way N', C_SW), ('N/NE 45th St', C_45)]:
        cr = [r for r in rows if r['corridor'] == corr]
        cr.sort(key=lambda r: (r['first_year'] or '0'), reverse=True)
        out.append(f'<h3 style="color:{col};margin:18px 0 6px">{corr} '
                   f'<span style="color:#999;font-weight:400;font-size:13px">'
                   f'({len(cr)} open now)</span></h3>')
        out.append('<table class="pt"><thead><tr>'
                   '<th>Opened by</th><th>Restaurant</th><th>Address</th>'
                   '<th>Seating</th><th>Last inspection</th></tr></thead><tbody>')
        for r in cr:
            out.append(
                f'<tr><td>{r["first_year"]}</td><td>{r["name"].title()}</td>'
                f'<td>{r["address"]}</td><td>{r["seating"]}</td>'
                f'<td>{r["last_inspection"]}</td></tr>')
        out.append('</tbody></table>')
    return '\n'.join(out)

ratio = open_now['N/NE 45th St']/open_now['Stone Way N']
# share of current restaurants that arrived in the last 2 years
def recent_share(c):
    n = new[c][2024] + new[c][2025]
    return n, 100*n/open_now[c]
sw_recent = recent_share('Stone Way N')
st_recent = recent_share('N/NE 45th St')
today = datetime.date.today().isoformat()

html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Wallingford restaurants: Stone Way N vs 45th St</title>
<style>
 body{{font-family:system-ui,sans-serif;max-width:920px;margin:30px auto;padding:0 16px;color:#222;line-height:1.5}}
 h1{{font-size:22px;margin-bottom:2px}} h2{{font-size:15px;margin-top:34px;color:#444}}
 .sub{{color:#777;font-size:13px;margin-top:0}}
 .cards{{display:flex;gap:14px;margin:18px 0;flex-wrap:wrap}}
 .card{{flex:1;min-width:150px;border:1px solid #e5e5e5;border-radius:10px;padding:14px 16px}}
 .card .n{{font-size:30px;font-weight:800}} .card .l{{font-size:13px;color:#666}}
 .sw{{color:{C_SW}}} .st{{color:{C_45}}}
 .legend span{{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:5px;vertical-align:middle}}
 .warn{{background:#fff8e6;border:1px solid #f0d99b;border-radius:8px;padding:12px 16px;font-size:13px;color:#6a5300;margin:18px 0}}
 .note{{background:#fafafa;border:1px solid #eee;border-radius:8px;padding:12px 16px;font-size:12.5px;color:#555}}
 .note li{{margin:3px 0}}
 table.pt{{border-collapse:collapse;width:100%;font-size:12px;margin-bottom:10px}}
 table.pt th,table.pt td{{border-bottom:1px solid #eee;padding:4px 6px;text-align:left;vertical-align:top}}
 table.pt th{{background:#f7f7f7;font-size:11px;color:#555}}
</style></head><body>
<h1>Restaurants open: Stone Way N vs N/NE 45th St</h1>
<p class="sub">Wallingford, Seattle &middot; currently-open restaurants and when they opened &middot; built {today}</p>

<div class="cards">
 <div class="card"><div class="n sw">{open_now['Stone Way N']}</div><div class="l">restaurants open now on <b>Stone Way N</b><br>(N 34th &rarr; N 45th)</div></div>
 <div class="card"><div class="n st">{open_now['N/NE 45th St']}</div><div class="l">restaurants open now on <b>N/NE 45th St</b><br>(Stone Way &rarr; I-5)</div></div>
 <div class="card"><div class="n">{ratio:.1f}&times;</div><div class="l">more open restaurants on<br>45th St than Stone Way</div></div>
</div>

<div class="warn">
<b>Read this first &mdash; what this can and can't show.</b> The only free, reproducible
source for restaurants at the block level is King County's food-permit inspection data,
which is effectively a registry of restaurants open <i>today</i>. Closed restaurants are
purged from it. So this page shows (1) how many restaurants are open <b>right now</b> on
each block, and (2) the <b>opening-year vintage</b> of those current restaurants &mdash;
i.e. how many of today's restaurants had already opened by each past year. It is
<b>not</b> a true count of all restaurants open in each past year, because restaurants
that have since closed leave no trace here. Treat the early years as
&ldquo;survivors only,&rdquo; not the full historical scene.
</div>

<p class="legend"><span style="background:{C_SW}"></span>Stone Way N &nbsp;&nbsp;<span style="background:{C_45}"></span>N/NE 45th St</p>

<h2>How many of today's restaurants had opened by each year</h2>
<p class="sub">Cumulative count of <i>currently-open</i> restaurants, indexed by the year each first appears in inspection records. Rising lines = today's scene was built up; it does not dip for closures (closed places aren't in the data).</p>
{line_chart()}

<h2>New restaurant arrivals per year (among those still open)</h2>
<p class="sub">Count of today's restaurants whose records begin in each year.</p>
{bar_chart()}

<div class="note">
<b>What the data says</b>
<ul>
 <li><b>45th St has more open restaurants today: {open_now['N/NE 45th St']} vs {open_now['Stone Way N']} on Stone Way</b> ({ratio:.1f}&times;). So on raw count, Stone Way has <i>not</i> overtaken 45th.</li>
 <li><b>But Stone Way's restaurants are much newer.</b> {sw_recent[0]} of its {open_now['Stone Way N']} current restaurants ({sw_recent[1]:.0f}%) first appear in 2024&ndash;2025, vs {st_recent[0]} of {open_now['N/NE 45th St']} ({st_recent[1]:.0f}%) on 45th. Stone Way's current-restaurant count nearly doubled since 2022 ({cum['Stone Way N'][years.index(2022)]}&rarr;{open_now['Stone Way N']}), tracking its housing boom.</li>
 <li>So a fairer read of your theory: Stone Way is the faster-<i>growing</i> restaurant corridor, but 45th still has the larger established restaurant row.</li>
</ul>
<b>Method &amp; caveats</b>
<ul>
 <li><b>Source:</b> King County Public Health Food Establishment Inspection Data (Socrata f29f-zza5), pulled {today}.</li>
 <li><b>Restaurant test:</b> an establishment counts if its inspection record carries a seating category (sit-down / quick-service). No-seating grocery and school-lunch permits are excluded automatically; convenience-store and retail permit-holders with seating (7-Eleven, Brooks Running) are excluded explicitly &mdash; see <code>restaurants_by_corridor.csv</code> for the full audit trail with reasons.</li>
 <li><b>Opening proxy:</b> a restaurant's first inspection date. New establishments are inspected at opening, so this is close; restaurants already open in 2006 (data start) show 2006 and are left-censored.</li>
 <li><b>Survivorship:</b> closed restaurants are absent from the source, so this is not a historical stock. A true 20-year open-per-year curve needs a source with restaurant close dates (e.g. WA Dept. of Revenue business records) &mdash; under investigation.</li>
 <li><b>Corridor definition:</b> same segments as the housing analysis (Stone Way N #3400&ndash;4499; 45th St between Stone Way and I-5).</li>
</ul>
</div>

{rest_tables()}
</body></html>"""
open('restaurants.html', 'w').write(html)
print('wrote restaurants.html')
