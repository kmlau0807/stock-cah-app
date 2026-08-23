# -*- coding: utf-8 -*-
"""HTML daily report builder for the cup-and-handle scan (US + HK).

Builds a ranked qualifying table plus a full table, and (feature b) embeds an
annotated SVG chart for every qualifying name. Charts are also written to
`chart_dir` so they can be attached to the email.
"""
import html, datetime, os

import chart as chart_mod


def build_report(results, run_date=None, top_n=25, chart_dir=None):
    run_date = run_date or datetime.date.today().isoformat()
    yes = [r for r in results if r.get("verdict") == "YES"]
    yes.sort(key=lambda r: (-r.get("score", 0),))
    yes = yes[:top_n]
    no = [r for r in results if r.get("verdict") == "NO"]
    na = [r for r in results if r.get("verdict") == "N/A"]
    err = [r for r in results if r.get("verdict") == "ERR"]

    def f(v, s=""):
        try:
            return f"{v:.1f}{s}"
        except Exception:
            return "-"

    def row(r):
        v = r.get("verdict")
        if v == "YES":
            cls = "yes"
            det = (f"cup {f(r.get('cup_depth'),'%')} · handle {f(r.get('handle_depth'),'%')} · "
                   f"rim-gap {f(r.get('rim_gap'),'%')} · {f(r.get('near_rim'),'%')} to rim · "
                   f"U-days {r.get('round_days')} · breakoutVol {f(r.get('vol_breakout'))}"
                   + ("" if r.get("breakout_confirmed") else " · ⚠ breakout vol NOT surged"))
        elif v == "NO":
            cls = "no"; det = r.get("reason", "")
        else:
            cls = "na"; det = r.get("reason", "")
        mkt = r.get("market", "").upper()
        return (f"<tr class='{cls}'><td>{mkt}</td><td><b>{r['symbol']}</b></td>"
                f"<td>{html.escape(str(r.get('name','')))}</td><td class='v'>{v}</td>"
                f"<td class='d'>{html.escape(det)}</td></tr>")

    yes_rows = "".join(row(r) for r in yes)
    other_rows = "".join(row(r) for r in no + na + err)

    summary = (f"{len(yes)} qualifying · {len(no)} rejected · {len(na)} not-forming · {len(err)} errors "
               f"· {len(results)} scanned")

    # --- annotated charts for qualifying names (feature b) ---
    chart_blocks = ""
    if chart_dir:
        os.makedirs(chart_dir, exist_ok=True)
    for r in yes:
        series = r.get("series")
        if not series:
            continue
        pairs = [(ts, c, (r.get("vols") or [None] * len(series))[i]) for i, (ts, c) in enumerate(series)]
        svg = chart_mod.build_svg(r["symbol"], r.get("name", ""), pairs, r)
        if not svg:
            continue
        if chart_dir:
            cpath = os.path.join(chart_dir, f"{r['symbol'].replace('.', '_')}_{run_date}.svg")
            with open(cpath, "w", encoding="utf-8") as fh:
                fh.write(svg)
        chart_blocks += (f'<div class="chart"><div class="ctitle">{r["market"]} · {r["symbol"]} · '
                         f'{html.escape(str(r.get("name","")))} — <b>{r.get("grade")}</b></div>'
                         f'{svg}</div>')

    doc = f"""<!DOCTYPE html><html><head><meta charset=utf-8><title>CAH Daily {run_date}</title>
<style>
body{{background:#0d1117;color:#e6edf3;font-family:Segoe UI,Arial,sans-serif;margin:0;padding:24px}}
h2{{margin:0 0 4px}} .sub{{color:#9aa4b2;font-size:13px;margin-bottom:6px}}
.summary{{color:#9aa4b2;font-size:14px;margin:8px 0 16px;padding:8px 12px;background:#161b22;border-radius:6px}}
h3{{margin:18px 0 8px;font-size:15px;color:#c9d1d9}}
table{{border-collapse:collapse;width:100%;font-size:13.5px}} th,td{{border:1px solid #2a2f3a;padding:7px 10px;text-align:left}}
th{{background:#161b22;color:#9aa4b2}} tbody tr.yes{{background:#0f2417}} tbody tr.no{{background:#11161f}} tbody tr.na{{background:#0d1117}}
.v{{font-weight:700;text-align:center}} .yes .v{{color:#3fb950}} .no .v{{color:#f85149}} .na .v{{color:#9aa4b2}}
.d{{color:#b6c0cc;font-size:12.5px}}
.legend{{margin:6px 0 10px;font-size:13px}}
.tag{{display:inline-block;padding:2px 8px;border-radius:4px;margin-right:8px;font-weight:700}}
.tag.y{{background:#0f2417;color:#3fb950}} .tag.n{{background:#241010;color:#f85149}} .tag.a{{background:#1c2027;color:#9aa4b2}}
.note{{color:#9aa4b2;font-size:12px;margin-top:18px}}
.chart{{margin:14px 0;padding:8px;background:#11161f;border:1px solid #2a2f3a;border-radius:8px}}
.chart .ctitle{{font-size:13px;color:#c9d1d9;margin-bottom:4px}}
.chart svg{{width:100%;height:auto;display:block}}
</style></head><body>
<h2>Daily Cup-and-Handle Scan &mdash; US + HK</h2>
<div class=sub>Generated {run_date} · 1-year daily window · v3 accuracy criteria (prior uptrend, U-shape, handle&lt;cup, volume contraction + breakout surge).</div>
<div class=summary>{summary}</div>

<h3>Qualifying patterns (ranked) — annotated charts</h3>
<div class=legend><span class=tag>y>YES</span><span class=tag>n>NO</span><span class=tag>a>N/A</span></div>
{chart_blocks or '<p class=d>No qualifying cup-and-handle patterns found today.</p>'}

<h3>Qualifying — detail</h3>
<table><thead><tr><th>Mkt</th><th>Ticker</th><th>Name</th><th>Verdict</th><th>Detail</th></tr></thead>
<tbody>{yes_rows or '<tr><td colspan=5 class=d>No qualifying patterns found today.</td></tr>'}</tbody></table>

<h3>All scanned</h3>
<table><thead><tr><th>Mkt</th><th>Ticker</th><th>Name</th><th>Verdict</th><th>Detail / Fail reason</th></tr></thead>
<tbody>{other_rows}</tbody></table>

<p class=note>For study / screening only &mdash; not investment advice. Breakout volume = last-10-day volume ÷ handle volume; &lt;1.2 means the breakout is not yet confirmed by volume.</p>
</body></html>"""
    return doc
