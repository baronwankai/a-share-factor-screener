# Changelog

## v1.0.0 — 2026-10-21

Initial public release.

- `index.html` — self-contained five-factor screener for the full A-share
  market (5,373 stocks, ST excluded); data snapshot dated 2026-10-20.
- `fetch_data.py` — data pipeline producing `data.json` from public
  Eastmoney/akshare endpoints (quotes, dynamic P/E, P/B, market cap,
  60-day momentum, ROE, dividend yield).
- `daily_picks.py` — daily Top-20 vs. CSI 500 prediction-tracking
  experiment runner with cumulative scorecard.
- Live demo via GitHub Pages.
