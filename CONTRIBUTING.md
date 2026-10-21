# Contributing

Thanks for looking. This is a small, single-maintainer project; the
most valuable contributions are the unglamorous ones.

## Especially welcome

- **Data-source fixes.** The pipeline depends on public Eastmoney /
  akshare endpoints that change and fail without notice. A failing
  `fetch_data.py` run with a captured error is a perfect issue.
- **Reproduction reports.** If your composite scores from the shipped
  `data.json` differ from `snapshot_stats.py` output, that is a bug —
  the methodology in `docs/METHODOLOGY.md` is the spec.
- **Translations** of the screener UI (currently Chinese).

## Dev setup

```bash
pip install -r requirements.txt
python fetch_data.py       # refresh data.json (needs network access to Eastmoney)
python snapshot_stats.py   # summarise the snapshot + print Top 20 composite
python daily_picks.py      # one experiment run (SKIP on non-trading days)
```

## Ground rules

- The factor model changes only through `docs/METHODOLOGY.md` first:
  document the change, then code it. The experiment protocol
  (`docs/EXPERIMENT.md`) is pre-registered — protocol changes apply to
  future runs only and are noted in the run log.
- Never edit committed files under `experiment/` — they are the
  prediction record.
- Keep `index.html` dependency-free and self-contained; that is the
  whole point of the format.
