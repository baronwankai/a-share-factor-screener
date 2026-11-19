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

| 2026-10-21 (evening retry) | ✅ Retry succeeded after the data source recovered. Universe 3,256 rankable of 5,373. Benchmark close 6840.56 (-0.01%). Settled the 2026-10-20 picks over the single session 10-20 → 10-21: 3 wins / 17 losses, average excess -0.9%. Top 20 for 2026-10-21 recorded. Scorecard: 20 settled, win rate 15.0%, average excess -0.9%. |
| 2026-10-22 | ✅ Ran normally. Universe 3,257 rankable of 5,373. Benchmark close 6655.25 (-2.71%). Settled the 2026-10-21 picks: 17 wins / 3 losses, average excess +0.92% — the low-P/E bank-heavy basket held up far better than the index on a down day. Top 20 for 2026-10-22 recorded. Scorecard: 40 settled, win rate 50.0%, average excess +0.01%. |
| 2026-10-23 | ✅ Ran normally. Universe 3,256 rankable of 5,373. Benchmark close 6814.44 (+2.39%). Settled the 2026-10-22 picks: 1 win / 19 losses, average excess -2.89% — the bank-heavy basket lagged badly on a day the index rallied 2.39%. Top 20 for 2026-10-23 recorded. Scorecard: 60 settled, win rate 35.0%, average excess -0.96%. |
| 2026-10-26 | ✅ Ran normally. Universe 3,253 rankable. Benchmark close 6712.73 (-1.49%). Settled the 2026-10-23 picks: 20 wins / 0 losses, average excess +2.7%. Top 20 for 2026-10-26 recorded. Scorecard: 80 settled, win rate 51.2%, average excess -0.05%. |
| 2026-10-27 | ✅ Ran normally. Universe 3,249 rankable. Benchmark close 6511.42 (-3.0%). Settled the 2026-10-26 picks: 17 wins / 3 losses, average excess +2.96%. Top 20 for 2026-10-27 recorded. Scorecard: 100 settled, win rate 58.0%, average excess +0.56%. |
| 2026-10-28 | ✅ Ran normally. Universe 3,251 rankable. Benchmark close 6640.89 (+1.99%). Settled the 2026-10-27 picks: 1 win / 19 losses, average excess -2.35% — the bank-heavy basket lagged badly on a day the index rallied 1.99%. Top 20 for 2026-10-28 recorded. Scorecard: 120 settled, win rate 49.2%, average excess +0.07%. |
| 2026-10-29 | ✅ Ran normally. Universe 3,242 rankable. Benchmark close 6453.72 (-2.82%). Settled the 2026-10-28 picks: 19 wins / 1 loss, average excess +4.39% — the bank-heavy basket held up far better than the index on a down day. Top 20 for 2026-10-29 recorded. Scorecard: 140 settled, win rate 55.7%, average excess +0.69%. |
| 2026-10-30 | ✅ Ran normally. Universe 3,235 rankable. Benchmark close 6266.19 (-2.91%). Settled the 2026-10-29 picks: 20 wins / 0 losses, average excess +3.69% — the bank-heavy basket held up far better than the index on a down day. Top 20 for 2026-10-30 recorded. Scorecard: 160 settled, win rate 61.3%, average excess +1.06%. |
| 2026-11-02 | ✅ Ran normally. Universe 3,235 rankable. Benchmark close 6420.23 (+2.46%). Settled the 2026-10-30 picks: 3 wins / 17 losses, average excess -2.56% — the bank-heavy basket lagged on a day the index rose 2.46%. Top 20 for 2026-11-02 recorded. Scorecard: 180 settled, win rate 56.1%, average excess +0.66%. |
| 2026-11-03 | ✅ Ran normally. Universe 3,235 rankable. Benchmark close 6327.05 (-1.45%). Settled the 2026-11-02 picks: 18 wins / 2 losses, average excess +0.8%. Top 20 for 2026-11-03 recorded. Scorecard: 200 settled, win rate 59.5%, average excess +0.67%. |
| 2026-11-04 | ✅ Ran normally. Universe 3,236 rankable. Benchmark close 6622.03 (+4.66%). Settled the 2026-11-03 picks: 0 wins / 20 losses, average excess -4.76% — the bank-heavy basket lagged badly on a day the index rallied 4.66%. Top 20 for 2026-11-04 recorded. Scorecard: 220 settled, win rate 54.1%, average excess +0.18%. |
| 2026-11-05 | ✅ Ran normally. Universe 3,236 rankable. Benchmark close 6740.93 (+1.8%). Settled the 2026-11-04 picks: 1 win / 19 losses, average excess -1.86% — the bank-heavy basket lagged on a day the index rose 1.8%. Top 20 for 2026-11-05 recorded. Scorecard: 240 settled, win rate 50.0%, average excess +0.01%. |
| 2026-11-06 | ✅ Ran normally. Universe 3,236 rankable. Benchmark close 6597.35 (-2.13%). Settled the 2026-11-05 picks: 18 wins / 2 losses, average excess +2.38% — the bank-heavy basket cushioned a down day. Top 20 for 2026-11-06 recorded. Scorecard: 260 settled, win rate 53.1%, average excess +0.19%. |
| 2026-11-09 | ✅ Ran normally. Universe 3,236 rankable. Benchmark close 6586.18 (-0.17%). Settled the 2026-11-06 picks: 17 wins / 3 losses, average excess +0.66% — the bank-heavy basket again held up on a flat-to-down day. Top 20 for 2026-11-09 recorded. Scorecard: 280 settled, win rate 55.4%, average excess +0.23%. |
| 2026-11-10 | ✅ Ran normally. Universe 3,236 rankable. Benchmark close 6645.89 (+0.91%). Settled the 2026-11-09 picks: 1 win / 19 losses, average excess -1.0% — the bank-heavy basket lagged on a day the index rose 0.91%. Top 20 for 2026-11-10 recorded. Scorecard: 300 settled, win rate 52.0%, average excess +0.14%. |
| 2026-11-11 | ✅ Ran normally. Universe 3,236 rankable. Benchmark close 6713.18 (+1.01%). Settled the 2026-11-10 picks: 0 wins / 20 losses, average excess -1.38% — the bank-heavy basket lagged on a day the index rose 1.01%. Top 20 for 2026-11-11 recorded. Scorecard: 320 settled, win rate 48.8%, average excess +0.05%. |
| 2026-11-12 | ✅ Ran normally. Universe 3,236 rankable. Benchmark close 6604.15 (-1.62%). Settled the 2026-11-11 picks: 19 wins / 1 loss, average excess +1.31% — the bank-heavy basket cushioned a down day. Top 20 for 2026-11-12 recorded. Scorecard: 340 settled, win rate 51.5%, average excess +0.12%. |
| 2026-11-13 | ✅ Ran normally. Universe 3,236 rankable. Benchmark close 6465.49 (-2.10%). Settled the 2026-11-12 picks: 20 wins / 0 losses, average excess +3.51% — the bank-heavy basket held up far better than the index on a down day. Top 20 for 2026-11-13 recorded. Scorecard: 360 settled, win rate 54.2%, average excess +0.31%. |
| 2026-11-16 | ✅ Ran normally. Universe 3,237 rankable. Benchmark close 6297.18 (-2.6%). Settled the 2026-11-13 picks: 20 wins / 0 losses, average excess +4.45% — the bank-heavy basket held up far better than the index on a down day. Top 20 for 2026-11-16 recorded. Scorecard: 380 settled, win rate 56.6%, average excess +0.53%. |
| 2026-11-17 | ✅ Ran normally. Universe 3,237 rankable. Benchmark close 6283.01 (-0.23%). Settled the 2026-11-16 picks: 14 wins / 6 losses, average excess +0.29% — the bank-heavy basket held up on a flat day. Top 20 for 2026-11-17 recorded. Scorecard: 400 settled, win rate 57.2%, average excess +0.52%. |
| 2026-11-18 | ✅ Ran normally. Universe 3,237 rankable. Benchmark close 6282.22 (-0.01%). Settled the 2026-11-17 picks: 6 wins / 14 losses, average excess -0.28% — the bank-heavy basket lagged on a flat day. Top 20 for 2026-11-18 recorded. Scorecard: 420 settled, win rate 56.0%, average excess +0.48%. |
| 2026-11-19 | ✅ Ran normally. Universe 3,237 rankable. Benchmark close 6251.96 (-0.48%). Settled the 2026-11-18 picks: 8 wins / 12 losses, average excess -0.28% — the bank-heavy basket lagged on a down day. Top 20 for 2026-11-19 recorded. Scorecard: 440 settled, win rate 55.2%, average excess +0.44%. |

- One day proves nothing; the scorecard only becomes interesting after
  dozens of settled days. The maintainer's prior is that the factor mix
  tilts heavily toward banks and other low-P/E, high-dividend names —
  the first Top 20 already shows it (9 of 20 are banks). That is the
  model working as specified, not a bug.
- Win rate and average excess are reported together: a >50% win rate
  with negative average excess would still be a losing signal.

## Milestone: first 10 picks settled (2026-10-21)

After the evening retry, `experiment/scorecard.json` crossed its first
milestone band (10 settled): 20 picks settled from 1 settled trading day
(2026-10-20), win rate 15.0%, average excess -0.9%. One batch proves
nothing — this is recorded as the baseline, not a verdict.

## Milestone: first 30 picks settled (2026-10-22)

`experiment/scorecard.json` crossed the 30-settled band on the 2026-10-22
run: 40 picks settled from 2 settled trading days (2026-10-20,
2026-10-21), win rate 50.0%, average excess +0.01%. The two batches are
mirror images — the first lost -0.9% on average, the second gained +0.92%
on a day the index fell 2.71% — so the scorecard sits almost exactly at
coin-flip. The experiment is still far too young for any conclusion.

## Milestone: first 60 picks settled (2026-10-23)

`experiment/scorecard.json` crossed the 60-settled band on the 2026-10-23
run: 60 picks settled from 3 settled trading days (2026-10-20, 2026-10-21,
2026-10-22), win rate 35.0%, average excess -0.96%. The third batch was the
worst so far — 1 win / 19 losses, average excess -2.89% on a day the index
rose 2.39% — and it dragged the scorecard well below coin-flip. Three
batches is still a tiny sample, but the bank-heavy value tilt now shows a
clear pattern: it cushions down days and lags rallies, exactly the
low-beta behavior the factor mix predicts.
