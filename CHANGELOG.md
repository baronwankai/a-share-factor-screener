# Changelog

## v1.1.0 — 2026-10-21

Substance release: documentation and evidence trail.

- `docs/METHODOLOGY.md` — full factor specification: universe
  construction, percentile scoring, `data.json` schema, limitations.
- `docs/EXPERIMENT.md` — pre-registered experiment protocol and run log,
  including the 2026-10-21 data-source outage (failed runs are logged,
  never back-filled).
- `experiment/` — raw records committed as generated: first prediction
  file (2026-10-20 Top 20), first daily report, cumulative scorecard.
- `snapshot_stats.py` — zero-dependency snapshot checker; reproduces the
  experiment's rankable universe (3,259) from the shipped snapshot.
- `CONTRIBUTING.md`, `requirements.txt`.

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
