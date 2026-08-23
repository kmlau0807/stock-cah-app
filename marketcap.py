# -*- coding: utf-8 -*-
"""Market-cap lookup for the cap filter (feature c).

Source: stockanalysis.com (no auth required, works for US + HK tickers).
NOTE: the free endpoint is rate-limited (~429 if hit too fast), so requests are
throttled with exponential backoff, and results are cached locally
(data/marketcap_cache.json, max-age configurable). A manual override file
(data/marketcap_override.json) always wins. The cache is also seeded once from
any existing report JSON that already contains market caps.

Cap is returned in *billions of the stock's local currency* (HKD for .HK names,
USD for US names), matching the MIN_MARKET_CAP logic of the original HK screener.
Parse handles T/B/M/K suffixes.
"""
import os, re, json, time, urllib.request, urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_FILE = os.path.join(DATA_DIR, "marketcap_cache.json")
OVERRIDE_FILE = os.path.join(DATA_DIR, "marketcap_override.json")
CACHE_MAX_AGE_DAYS = 7
_REQ_DELAY = 1.0          # polite delay between requests (seconds)
_RATE_LIMITED = {"flag": False}  # circuit breaker: once 429 seen, stop hammering


def _parse_cap(raw):
    if raw is None:
        return None
    raw = raw.strip().replace(",", "")
    m = re.match(r"^([\d.]+)\s*([TBMK]?)$", raw, re.I)
    if not m:
        return None
    val = float(m.group(1))
    suf = m.group(2).upper()
    mult = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3, "": 1}[suf]
    return val * mult / 1e9  # billions


def _fetch_once(symbol):
    url = f"https://stockanalysis.com/stocks/{symbol}/"
    h = urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=25
    ).read().decode("utf-8", "ignore")
    m = re.search(r'marketCap:"([^"]+)"', h)
    if m:
        return _parse_cap(m.group(1))
    return None


def _fetch(symbol):
    """Fetch with a 429 circuit-breaker + throttle. Returns cap in billions or None.

    If the source rate-limits us (HTTP 429), we set the breaker and stop issuing
    further requests for this run, so a daily scan never hangs. Cached/seed caps
    still resolve; the rest are left unknown (kept). The cache fills in on later
    days when not rate-limited.
    """
    if _RATE_LIMITED["flag"]:
        return None
    try:
        cap = _fetch_once(symbol)
        time.sleep(_REQ_DELAY)
        return cap
    except urllib.error.HTTPError as e:
        if e.code == 429:
            _RATE_LIMITED["flag"] = True
            time.sleep(5)
        return None
    except Exception:
        time.sleep(_REQ_DELAY)
        return None


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            return json.load(open(CACHE_FILE))
        except Exception:
            return {}
    return {}


def save_cache(c):
    os.makedirs(DATA_DIR, exist_ok=True)
    json.dump(c, open(CACHE_FILE, "w"), indent=2)


def load_overrides():
    if os.path.exists(OVERRIDE_FILE):
        try:
            return json.load(open(OVERRIDE_FILE))
        except Exception:
            return {}
    return {}


def seed_from_report(path):
    """One-time seed: pull mcap_raw (e.g. '4.10T') from an existing report JSON."""
    if not os.path.exists(path):
        return {}
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}
    seeded = {}
    for r in data:
        sym = r.get("symbol") or r.get("ticker")
        raw = r.get("mcap_raw") or r.get("marketCap") or r.get("mcap")
        if sym and raw:
            c = _parse_cap(str(raw))
            if c:
                seeded[sym] = {"cap": c, "t": time.time()}
    return seeded


def resolve(symbols, max_age_days=CACHE_MAX_AGE_DAYS, force=False, verbose=False):
    """Return {symbol: cap_billions}. Best-effort; missing -> None."""
    cache = load_cache()
    # seed once if cache empty
    if not cache:
        seed = seed_from_report(os.path.join(BASE_DIR, "..", "outputs", "hk_top20_liquid.json"))
        if seed:
            cache.update(seed)
            if verbose:
                print(f"  cap cache seeded with {len(seed)} names from earlier report")
    now = time.time()
    out = {}
    for sym in symbols:
        cap = None
        ent = cache.get(sym)
        if ent and not force and (now - ent.get("t", 0)) < max_age_days * 86400:
            cap = ent.get("cap")
        if cap is None:
            cap = _fetch(sym)
            if cap is not None:
                cache[sym] = {"cap": cap, "t": now}
                if verbose:
                    print(f"  cap {sym}: {cap:.1f}B (fetched)")
            else:
                if verbose:
                    print(f"  cap {sym}: FAILED")
        out[sym] = cap
    # manual overrides always win
    for sym, v in load_overrides().items():
        try:
            out[sym] = float(v)
        except Exception:
            pass
    save_cache(cache)
    return out
