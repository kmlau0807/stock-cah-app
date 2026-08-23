# -*- coding: utf-8 -*-
"""Configuration for the US+HK cup-and-handle daily detector.
Secrets (SMTP password) are read from environment variables so they are never hardcoded.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    # Which markets to scan: "us", "hk", or both
    "markets": ["us", "hk"],

    # Data window for the pattern
    "lookback": "1y",
    "interval": "1d",

    # How many qualifying names to headline in the report
    "top_n": 25,

    # --- v3 detection thresholds (tuned during the session) ---
    "detect": {
        "rim_recent_min": 0.45,     # right rim must be in latter 55% of window
        "rim_gap_max_pct": 18.0,    # left/right rims within 18%
        "cup_depth_min_pct": 12.0,
        "cup_depth_max_pct": 45.0,
        "bottom_pos_min": 0.30,     # cup bottom centeredness
        "bottom_pos_max": 0.70,
        "handle_depth_min_pct": 3.0,
        "handle_depth_max_pct": 22.0,
        "handle_span_min": 12,
        "handle_span_max": 45,
        "cup_span_min": 40,
        "near_rim_min_pct": -3.0,   # current price vs right rim
        "near_rim_max_pct": 18.0,
        "pre_uptrend_adv_min_pct": 8.0,   # rise into the left rim
        "u_shape_min_days": 3,            # >=3 days within 4% of bottom
        "u_shape_band_pct": 4.0,
        "vol_handle_max_ratio": 0.80,     # handle vol <= 0.8x cup-run-up
        "vol_breakout_min_ratio": 1.20,   # recent vol >= 1.2x handle vol (confirmation)
    },

    # --- Market-cap filter (feature c) ---
    # Floor in billions of the stock's LOCAL currency (HKD for .HK, USD for US).
    # 0 disables the filter. The original HK screener used >= HK$50B; set
    # min_market_cap_per_market["hk"] = 50 to match that. Lives in marketcap.py.
    "min_market_cap_b": 5,
    "min_market_cap_per_market": {"hk": 50},  # HK floor raised to match original screener

    # Pluggable universe (feature a): path to an old screener.py that defines
    # HK_UNIVERSE. Used by tools/import_screener_universe.py to build the
    # data/universe_hk.json override (the scanner prefers that file automatically).
    "custom_hk_universe_path": r"C:\Users\lauki\WorkBuddy\2026-08-19-09-19-48\hk_screener\screener.py",

    "charts": {
        "enabled": True,
        "dir": os.path.join(BASE_DIR, "reports", "charts"),
    },

    "data_dir": os.path.join(BASE_DIR, "data"),

    "schedule": {
        "time": "08:30",            # HH:MM local time
        "timezone": "Asia/Hong_Kong",
    },

    "email": {
        # Enabled when CAH_EMAIL_ENABLED=true (default) AND creds are present in env.
        "enabled": os.getenv("CAH_EMAIL_ENABLED", "true").lower() in ("1", "true", "yes"),
        "smtp_host": os.getenv("CAH_SMTP_HOST", ""),
        "smtp_port": int(os.getenv("CAH_SMTP_PORT", "587")),
        "smtp_user": os.getenv("CAH_SMTP_USER", ""),
        "smtp_pass": os.getenv("CAH_SMTP_PASS", ""),
        "use_tls": True,
        "from_addr": os.getenv("CAH_EMAIL_FROM", ""),
        "to_addrs": [x.strip() for x in os.getenv("CAH_EMAIL_TO", "").split(",") if x.strip()],
        "subject": "Daily Cup-and-Handle Scan - US + HK",
    },

    "output_dir": os.path.join(BASE_DIR, "reports"),
}
