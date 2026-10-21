# Experiment records

Raw, unedited outputs of the daily prediction experiment — see
[`docs/EXPERIMENT.md`](../docs/EXPERIMENT.md) for the protocol.

- `picks-YYYY-MM-DD.json` — that day's Top 20 prediction, written
  before the next trading session, with the benchmark close stored for
  settlement.
- `report-YYYY-MM-DD.md` — the human-readable daily report (Chinese):
  settlement of prior picks, cumulative scorecard, today's Top 20.
- `scorecard.json` — cumulative record, recomputed from all settled
  pick files.

These files are the experiment's evidence trail: they are committed
as generated and never edited afterwards.
