# The prediction experiment — protocol

A pre-registered, no-cherry-picking test of the five-factor model in
[`docs/METHODOLOGY.md`](METHODOLOGY.md). The rules were fixed before the
first run and are not adjusted retroactively.

## Protocol

1. **When.** Every A-share trading day, after the close (trading
   calendar via akshare `tool_trade_date_hist_sina`). Non-trading days:
   the runner prints `SKIP` and records nothing.
2. **Predict.** Score the full snapshot with the five-factor composite;
   the **Top 20** are recorded to `experiment/picks-YYYY-MM-DD.json`
   *before* the next session, with the benchmark close stored alongside.
   The prediction is fixed: *"each pick will outperform the CSI 500
   (000905) on the next trading day (excess return > 0)."*
3. **Settle.** On the next run, each unsettled pick is settled with
   actual closes: pick return minus CSI 500 return over the same window
   (from the stored `benchmark_close`). Excess > 0 = win, < 0 = loss.
4. **Scorecard.** `experiment/scorecard.json` is recomputed from all
   settled pick files (idempotent): total settled, wins/losses, win
   rate, average excess %, best/worst 3.
5. **Failures are logged, not hidden.** If a data source is down, the
   run is recorded as failed below; no picks are generated and nothing
   is back-filled later. A missed day stays missed.

## Records

Committed under [`experiment/`](../experiment/): one JSON per prediction
day, the matching human-readable report, and the cumulative scorecard.

## Run log

| Date | Result |
|---|---|
| 2026-10-20 | ✅ First run. Universe 3,259 rankable of 5,373. Top 20 recorded (benchmark close 6841.44, +0.60%). Scorecard empty — nothing to settle yet. |
| 2026-10-21 | ❌ **Run failed — data source outage.** Eastmoney `clist` endpoint returned empty replies / 502 from the runner's network all afternoon; no snapshot, so no settlement of the 10-20 picks and no new picks. Per protocol §5 the day is left blank, not back-filled. Settlement of the 2026-10-20 picks will use the next successful run's closes (excess measured from the stored benchmark close to that close, and flagged as a 2-session window when reported). |

## Reading the results honestly

- One day proves nothing; the scorecard only becomes interesting after
  dozens of settled days. The maintainer's prior is that the factor mix
  tilts heavily toward banks and other low-P/E, high-dividend names —
  the first Top 20 already shows it (9 of 20 are banks). That is the
  model working as specified, not a bug.
- Win rate and average excess are reported together: a >50% win rate
  with negative average excess would still be a losing signal.
