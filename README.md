# stock-cah-app

A zero-dependency (Python standard library only) daily scanner that detects the
**cup-and-handle** chart pattern across US and HK equity markets and produces an
inline-SVG HTML report (optionally emailed).

## Features

- **Cup-and-handle detector** implementing the v3 rule set: prior uptrend, U-shaped
  bottom, handle shallower than the cup, volume contraction during the handle with a
  breakout surge, plus cup/handle duration limits and a right-rim re-test.
- **Two markets** — US and HK — with pluggable universe files
  (`data/universe_hk.json`, `data/universe_us.json`). Example templates are shipped
  as `data/universe_*.example.json`.
- **Market-cap filter** — optionally drops symbols below a per-market floor
  (e.g. ≥ HK$50B for HK). Caps are fetched from stockanalysis.com and cached for 7 days.
- **Annotated charts** — each qualifying symbol gets a dark-themed SVG with the
  cup/handle bands, right-rim breakout line, and key markers (L-rim / Cup / R-rim /
  Handle / Now).
- **Email** — SMTP delivery of the report plus chart attachments, driven by `.env`.
- **Scheduler friendly** — runs headless via `python main.py run`; pair it with the
  Windows Task Scheduler script (`scheduler/setup_windows.ps1`) or `crontab.txt`.

## Usage

```bash
# Scan both markets, write reports/cah_report_<date>.html
python main.py run

# HK only, with email (needs .env SMTP creds and email.enabled=True)
python main.py run --market hk --email

# Quick sanity check on a tiny subset
python main.py selftest
```

## Configuration

- `config.py` — detection thresholds, market-cap floors, output dirs, email settings.
- `.env.example` — copy to `.env` and fill in `CAH_SMTP_*` / `CAH_EMAIL_*` to enable mail.
- `data/universe_hk.json` / `data/universe_us.json` — your watchlist
  (`[["SYMBOL", "Name"], ...]`). Missing files fall back to the built-in defaults.

## Data sources

- Price/volume: Yahoo Finance chart endpoint (no auth).
- Market cap: stockanalysis.com (cached; respects 429 rate limiting).

## Disclaimer

For educational/research use only. Not investment advice.
