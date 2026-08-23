# -*- coding: utf-8 -*-
"""Data fetcher: Yahoo Finance chart endpoint (works for US + HK .HK tickers in this env)."""
import urllib.request, json, time

def fetch(sym, rng="1y", iv="1d", retries=3, timeout=25):
    """Return (pairs, meta) where pairs = [(timestamp, close, volume), ...]."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval={iv}"
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            d = json.load(urllib.request.urlopen(req, timeout=timeout))["chart"]["result"][0]
            ts = d["timestamp"]; q = d["indicators"]["quote"][0]; meta = d["meta"]
            pairs = [(t, q["close"][i], (q["volume"][i] or 0))
                     for i, t in enumerate(ts) if q["close"][i] is not None]
            return pairs, meta
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    raise last_err
