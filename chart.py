# -*- coding: utf-8 -*-
"""Annotated cup-and-handle SVG chart generator (feature b).

Draws the price line, a shaded cup band, a shaded handle band, the right-rim /
breakout line, and markers for the left rim, cup bottom, right rim, handle low
and current price. Returns a standalone SVG string (viewBox 0 0 720 340).
"""
import datetime


def _fmt_date(ts):
    try:
        return datetime.datetime.fromtimestamp(ts, datetime.UTC).strftime("%Y-%m-%d")
    except Exception:
        return ""


def build_svg(symbol, name, pairs, rec, width=720, height=340):
    closes = [p[1] for p in pairs]
    vols = [p[2] for p in pairs if p[2] is not None] or [0]
    n = len(closes)
    if n < 5:
        return ""

    lo, hi = min(closes), max(closes)
    pad = (hi - lo) * 0.14 or 1.0
    ymin, ymax = lo - pad, hi + pad

    M = {"l": 58, "r": 16, "t": 30, "b": 46}
    pw = width - M["l"] - M["r"]
    ph = height - M["t"] - M["b"]

    def X(i):
        return M["l"] + (i / (n - 1)) * pw

    def Y(v):
        return M["t"] + (1 - (v - ymin) / (ymax - ymin)) * ph

    # price polyline
    pts = " ".join(f"{X(i):.1f},{Y(closes[i]):.1f}" for i in range(n))

    # volume strip (bottom 22px)
    vmax = max(vols) or 1
    vb = M["t"] + ph + 6
    vbars = ""
    for i, p in enumerate(pairs):
        v = p[2]
        if not v:
            continue
        h = (v / vmax) * 20
        vbars += f'<rect x="{X(i)-0.8:.1f}" y="{vb+22-h:.1f}" width="1.6" height="{h:.1f}" fill="#2f3b4d"/>'

    # bands
    L = rec.get("L_idx"); R = rec.get("R_idx"); B = rec.get("B_idx"); H = rec.get("H_idx")
    bands = ""
    if L is not None and R is not None:
        bands += (f'<rect x="{X(L):.1f}" y="{M["t"]}" width="{X(R)-X(L):.1f}" '
                  f'height="{ph}" fill="#58a6ff" opacity="0.10"/>')
    if R is not None:
        bands += (f'<rect x="{X(R):.1f}" y="{M["t"]}" width="{X(n-1)-X(R):.1f}" '
                  f'height="{ph}" fill="#ff7b9e" opacity="0.12"/>')

    # rim / breakout line
    rim = ""
    if R is not None:
        rx = X(R)
        rim = (f'<line x1="{rx:.1f}" y1="{M["t"]}" x2="{rx:.1f}" y2="{M["t"]+ph}" '
               f'stroke="#e0b341" stroke-width="1.4" stroke-dasharray="5 4"/>'
               f'<text x="{rx:.1f}" y="{M["t"]-8}" fill="#e0b341" font-size="11" '
               f'text-anchor="middle">R-rim / breakout</text>')

    # y gridlines
    grid = ""
    for frac in (0, 0.25, 0.5, 0.75, 1):
        v = ymin + (ymax - ymin) * frac
        y = M["t"] + ph * (1 - frac)
        grid += (f'<line x1="{M["l"]}" y1="{y:.1f}" x2="{width-M["r"]}" y2="{y:.1f}" '
                 f'stroke="#20262f" stroke-width="1"/>'
                 f'<text x="{M["l"]-6}" y="{y+3:.1f}" fill="#9aa4b2" font-size="10" text-anchor="end">{v:.2f}</text>')

    # x date labels (5 evenly spaced)
    xticks = ""
    for k in range(5):
        i = int(k / 4 * (n - 1))
        xticks += (f'<text x="{X(i):.1f}" y="{height-10}" fill="#9aa4b2" font-size="10" text-anchor="middle">'
                   f'{_fmt_date(pairs[i][0])}</text>')

    # markers
    def marker(i, v, label, color, dx):
        if i is None or v is None:
            return ""
        x, y = X(i), Y(v)
        return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" stroke="#0d1117" stroke-width="1.2"/>'
                f'<text x="{x+dx:.1f}" y="{y-6:.1f}" fill="{color}" font-size="10.5" text-anchor="middle">{label}</text>')

    mk = ""
    mk += marker(L, rec.get("L"), "L-rim", "#3fb950", 0)
    mk += marker(B, rec.get("B"), "Cup", "#58a6ff", 0)
    mk += marker(R, rec.get("R"), "R-rim", "#3fb950", 0)
    mk += marker(H, rec.get("H"), "Handle", "#ff7b9e", 0)
    mk += marker(n - 1, rec.get("cur"), "Now", "#e6edf3", 0)

    subtitle = (f"cup {rec.get('cup_depth',0):.0f}% · handle {rec.get('handle_depth',0):.0f}% · "
                f"rim-gap {rec.get('rim_gap',0):.0f}% · {rec.get('near_rim',0):.0f}% to rim")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" font-family="Segoe UI, Arial, sans-serif">
<rect x="0" y="0" width="{width}" height="{height}" fill="#0d1117"/>
<text x="{M["l"]}" y="18" fill="#e6edf3" font-size="13" font-weight="700">{symbol} · {name}</text>
<text x="{width-M["r"]}" y="18" fill="#9aa4b2" font-size="11" text-anchor="end">{subtitle}</text>
{grid}
{bands}
<path d="{pts}" fill="none" stroke="#58a6ff" stroke-width="1.8"/>
{vbars}
{rim}
{mk}
{xticks}
</svg>'''
    return svg
