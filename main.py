# -*- coding: utf-8 -*-
"""CLI entry point for the US+HK cup-and-handle daily detector.

Examples
--------
Scan both markets and save an HTML report:
    python main.py run

Scan only HK and email the report (requires env SMTP creds):
    python main.py run --market hk --email

Quick self-test on a tiny subset (no email):
    python main.py selftest
"""
import os, sys, argparse, datetime, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _load_dotenv():
    """Load KEY=VALUE pairs from a local .env file if present (stdlib only)."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(p):
        return
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_dotenv()

import config
from detector import detect_symbol
from universe import load_us_universe, load_hk_universe
from report import build_report
from mailer import send_email
import marketcap
import glob

def run(market="both", top_n=None, do_email=False, verbose=True):
    cfg = config.CONFIG
    top_n = top_n or cfg["top_n"]
    markets = {"us": ["us"], "hk": ["hk"], "both": ["us", "hk"]}[market]

    targets = []
    if "us" in markets: targets += [("US", s, n) for s, n in load_us_universe()]
    if "hk" in markets: targets += [("HK", s, n) for s, n in load_hk_universe()]

    # --- market-cap filter (feature c) ---
    cap_dropped = 0
    floor_global = cfg.get("min_market_cap_b", 0)
    floor_per = cfg.get("min_market_cap_per_market", {}) or {}
    if floor_global and floor_global > 0:
        caps = marketcap.resolve([t[1] for t in targets], verbose=verbose)
        kept = []
        for mkt, sym, name in targets:
            cap = caps.get(sym)
            floor = floor_per.get(mkt.lower(), floor_global)
            if cap is None:
                # best-effort: keep if we couldn't fetch (don't block the scan)
                if verbose:
                    print(f"  cap {sym}: unknown (kept)")
                kept.append((mkt, sym, name))
            elif cap < floor:
                cap_dropped += 1
                if verbose:
                    print(f"  cap {sym}: {cap:.1f}B < {floor:.0f}B floor -> dropped")
            else:
                kept.append((mkt, sym, name))
        targets = kept
        if verbose and cap_dropped:
            print(f"  [cap filter] dropped {cap_dropped} below market-cap floor")

    results = []
    for mkt, sym, name in targets:
        try:
            rec = detect_symbol(sym, name, mkt, cfg["detect"])
            results.append(rec)
            if verbose:
                v = rec.get("verdict")
                print(f"  [{mkt}] {sym:<9} {v:<4} {rec.get('reason','')[:48]}")
        except Exception as e:
            results.append({"symbol": sym, "name": name, "market": mkt,
                            "verdict": "ERR", "reason": repr(e)[:80]})
        time.sleep(0.05)

    run_date = datetime.date.today().isoformat()
    chart_dir = cfg["charts"]["dir"] if cfg["charts"].get("enabled") else None
    html = build_report(results, run_date=run_date, top_n=top_n, chart_dir=chart_dir)

    os.makedirs(cfg["output_dir"], exist_ok=True)
    out_path = os.path.join(cfg["output_dir"], f"cah_report_{run_date}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    yes = sum(1 for r in results if r.get("verdict") == "YES")
    print(f"\nScanned {len(results)} symbols · {yes} qualifying · report -> {out_path}")

    # collect chart SVGs for the email
    svg_paths = []
    if chart_dir and os.path.isdir(chart_dir):
        svg_paths = sorted(glob.glob(os.path.join(chart_dir, f"*_{run_date}.svg")))

    if do_email:
        if not cfg["email"].get("enabled"):
            print("Email disabled in config (email.enabled=False). Set env vars and enabled=True.")
        else:
            try:
                send_email(html, cfg["email"]["subject"], cfg["email"], attachments=svg_paths)
                print("Emailed report to:", cfg["email"]["to_addrs"],
                      f"(+{len(svg_paths)} chart attachments)" if svg_paths else "")
            except Exception as e:
                print("Email failed:", e)
    return results, out_path

def selftest():
    print("Self-test on a small US+HK subset...")
    subset = [("US","COST","Costco"),("US","JPM","JPMorgan"),("HK","0939.HK","CCB"),
              ("HK","0005.HK","HSBC"),("HK","0700.HK","Tencent")]
    for mkt, sym, name in subset:
        try:
            rec = detect_symbol(sym, name, mkt, config.CONFIG["detect"])
            print(f"  [{mkt}] {sym:<9} {rec.get('verdict'):<4} {rec.get('reason','')}")
        except Exception as e:
            print(f"  [{mkt}] {sym:<9} ERR {repr(e)[:60]}")
    print("Self-test done.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="US+HK cup-and-handle daily detector")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="scan and build report")
    r.add_argument("--market", choices=["us","hk","both"], default="both")
    r.add_argument("--top", type=int, default=None)
    r.add_argument("--email", action="store_true")
    sub.add_parser("selftest", help="quick test on a tiny subset")
    args = ap.parse_args()

    if args.cmd == "selftest":
        selftest()
    else:
        run(market=getattr(args, "market", "both"),
            top_n=getattr(args, "top", None),
            do_email=getattr(args, "email", False))
