# -*- coding: utf-8 -*-
"""Cup-and-handle detector v3 (the accuracy-tuned criteria from the session).
Returns a structured result per symbol with verdict, reasons, pivot levels and a quality score.
"""
import datetime

def _slope(closes):
    n = len(closes)
    if n < 2:
        return 0.0
    x = list(range(n)); mx = sum(x)/n; my = sum(closes)/n
    num = sum((x[i]-mx)*(closes[i]-my) for i in range(n))
    den = sum((x[i]-mx)**2 for i in range(n))
    return num/den if den else 0.0

def analyze(pairs, cfg=None):
    """pairs = [(ts, close, volume), ...]; cfg = CONFIG['detect'] dict."""
    if cfg is None:
        cfg = {}
    n = len(pairs)
    if n < 150:
        return {"ok": False, "verdict": "N/A", "reason": "insufficient data (<150 bars)"}

    closes = [p[1] for p in pairs]
    R_idx = max(range(n), key=lambda i: closes[i]); R = closes[R_idx]
    R_pos = R_idx / (n - 1)

    left_seg_end = max(0, R_idx - 15)
    if left_seg_end < 20:
        return {"ok": False, "verdict": "N/A", "reason": "no left rim (peak too old / at window start)"}

    L_idx = max(range(left_seg_end), key=lambda i: closes[i]); L = closes[L_idx]
    cup_seg = closes[L_idx:R_idx+1]
    B_off = min(range(len(cup_seg)), key=lambda i: cup_seg[i]); B_idx = L_idx + B_off; B = cup_seg[B_off]
    cup_depth = (R - B) / R; rim_gap = (R - L) / R
    cup_span = R_idx - L_idx; bottom_pos = B_off / max(1, cup_span)

    after = closes[R_idx:]; H_off = min(range(len(after)), key=lambda i: after[i]); H_idx = R_idx + H_off; H = after[H_off]
    handle_depth = (R - H) / R; handle_span = n - R_idx; cur = closes[-1]; near_rim = (R - cur) / R

    def avg_vol(a, b):
        seg = [pairs[i][2] for i in range(a, b) if i < n]
        return sum(seg)/len(seg) if seg else 0
    vol_handle = avg_vol(R_idx, n); vol_cupup = avg_vol(L_idx, R_idx)
    vol_ratio = vol_handle / vol_cupup if vol_cupup else 1
    vol_breakout = (avg_vol(max(R_idx, n-10), n) / vol_handle) if vol_handle else 1

    rec = {"ok": True, "R": R, "L": L, "B": B, "H": H, "cur": cur, "R_pos": R_pos,
           "cup_depth": cup_depth*100, "handle_depth": handle_depth*100, "rim_gap": rim_gap*100,
           "near_rim": near_rim*100, "bottom_pos": bottom_pos, "handle_span": handle_span,
           "cup_span": cup_span, "vol_ratio": vol_ratio, "vol_breakout": vol_breakout,
           "R_idx": R_idx, "L_idx": L_idx, "B_idx": B_idx, "H_idx": H_idx}

    c = cfg
    fails = []
    # --- base gates ---
    if R_pos < c.get("rim_recent_min", 0.45): fails.append("rim too old")
    if rim_gap*100 > c.get("rim_gap_max_pct", 18): fails.append(f"rim gap {rim_gap*100:.0f}%")
    if not (c.get("cup_depth_min_pct",12) <= cup_depth*100 <= c.get("cup_depth_max_pct",45)):
        fails.append(f"cup {cup_depth*100:.0f}%")
    if not (c.get("bottom_pos_min",0.30) <= bottom_pos <= c.get("bottom_pos_max",0.70)):
        fails.append("bottom off-center")
    if handle_depth*100 < c.get("handle_depth_min_pct",3): fails.append("no handle dip")
    if handle_depth*100 > c.get("handle_depth_max_pct",22): fails.append(f"handle {handle_depth*100:.0f}% deep")
    if handle_span < c.get("handle_span_min",12): fails.append("handle too short")
    if handle_span > c.get("handle_span_max",45): fails.append("handle too long")
    if cup_span < c.get("cup_span_min",40): fails.append("cup too short")
    if not (c.get("near_rim_min_pct",-3) <= near_rim*100 <= c.get("near_rim_max_pct",18)):
        fails.append(f"{near_rim*100:.0f}% from rim")
    # --- v3 accuracy gates ---
    pre = closes[max(0, L_idx-80):L_idx+1]
    if len(pre) >= 20:
        adv = (L - pre[0]) / pre[0] * 100
        rec["pre_adv"] = adv
        if _slope(pre) <= 0 or adv < c.get("pre_uptrend_adv_min_pct",8):
            fails.append("no prior uptrend")
    band = c.get("u_shape_band_pct",4)
    near_bottom = sum(1 for x in cup_seg if x <= B*(1+band/100))
    rec["round_days"] = near_bottom
    if near_bottom < c.get("u_shape_min_days",3): fails.append("V-shape not U")
    if handle_depth*100 >= cup_depth*100: fails.append("handle>=cup")
    if vol_ratio > c.get("vol_handle_max_ratio",0.80): fails.append("handle vol not contracted")
    if vol_breakout < c.get("vol_breakout_min_ratio",1.20): rec["breakout_confirmed"] = False
    else: rec["breakout_confirmed"] = True

    rec["fails"] = fails
    rec["verdict"] = "YES" if not fails else "NO"
    # quality score (higher = better), used to rank YES rows
    score = 100
    score -= abs(rim_gap*100 - 5) * 0.5
    score -= abs(handle_depth*100 - 9) * 1.0
    score -= abs(cup_depth*100 - 22) * 0.5
    score += (vol_breakout - 1) * 60
    score -= max(0, near_rim*100) * 1.0
    rec["score"] = round(max(0, score), 1)
    if rec["verdict"] == "YES":
        rec["grade"] = "textbook" if (rim_gap*100 <= 10 and handle_depth*100 <= 12) else "clean"
        rec["reason"] = rec["grade"]
    else:
        rec["grade"] = ""
        rec["reason"] = "; ".join(fails)
    return rec

def detect_symbol(sym, name, market, cfg):
    from fetcher import fetch
    pairs, meta = fetch(sym)
    rec = analyze(pairs, cfg)
    if not rec.get("ok"):
        rec["verdict"] = rec.get("verdict") or "N/A"
    rec["symbol"] = sym; rec["name"] = (meta.get("shortName") or name); rec["market"] = market
    # stash raw series (needed by the chart generator) — closes + timestamps + volumes
    rec["series"] = [(p[0], p[1]) for p in pairs]
    rec["vols"] = [p[2] for p in pairs]
    return rec
