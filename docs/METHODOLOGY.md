# Factor methodology

This document describes exactly how the screener and the prediction
experiment score stocks. The model is intentionally simple and fully
transparent: anyone with the same snapshot can reproduce every number.

## Universe

- All China A-share listings from the quote snapshot (**5,373** stocks in
  the 2026-10-20 snapshot), **excluding ST / \*ST** names (delisting-risk
  warnings make their prices and fundamentals non-comparable).
- A stock is **rankable** when all five factors are present and P/E > 0
  (a non-positive P/E makes the value rank meaningless). In the
  2026-10-20 experiment run, **3,259** of the snapshot universe were
  rankable.

## The five factors

| Factor | Field | Direction | Source |
|---|---|---|---|
| Value — earnings | `pe` (dynamic P/E) | lower is better | quote snapshot |
| Value — book | `pb` (P/B) | lower is better | quote snapshot |
| Quality | `roe` (%, latest interim/annual report) | higher is better | financial statements (akshare `stock_yjbb_em`) |
| Income | `div` (dividend yield %, latest annual distribution) | higher is better | distribution data (akshare `stock_fhps_em`) |
| Momentum | `mom60` (60-trading-day price change, %) | higher is better | quote snapshot |

Market capitalisation (`mcap`) is shipped in the snapshot and available
in the UI as a filter, but it is **not** part of the composite score.

## Scoring

For each factor, every rankable stock receives a **percentile rank**
(0–100) within the rankable universe, oriented so that 100 is always
"best" (for P/E and P/B the ordering is inverted). The **composite score**
is the unweighted mean of the five percentile ranks:

```
score = ( pct(pe)↓ + pct(pb)↓ + pct(roe)↑ + pct(div)↑ + pct(mom60)↑ ) / 5
```

Equal weights are a deliberate choice: the project tests whether a
naive, fully transparent multi-factor rank has any predictive content at
all, before any optimisation is allowed near it.

## Snapshot schema (`data.json`)

```jsonc
{
  "fetched_at": "2026-10-20 01:43:40",
  "source": "...",
  "count": 5373,
  "coverage": { /* per-factor non-null counts */ },
  "stocks": [
    { "code": "920992", "name": "中科美菱", "price": 12.29, "chg": 2.16,
      "pe": 60.49, "pb": 1.9, "mcap": 11.9, "mom60": 9.24, "ytd": -28.96,
      "roe": 1.56, "div": 0.63 }
  ]
}
```

`mcap` is in CNY 100M (亿）. `chg` is the snapshot day's % change, `ytd`
the year-to-date % change. Missing fundamentals are `null`, never
silently zero-filled — a stock with a missing factor is unrankable, not
scored as zero.

## Known limitations

- **Point-in-time, not survivorship-free history.** Snapshots describe
  the market as of fetch time; delisted names simply stop appearing.
- **Public endpoints are unstable.** The Eastmoney `clist` API
  intermittently returns empty replies / 502s from some networks
  (observed 2026-10-21, see `docs/EXPERIMENT.md` run log). The pipeline
  retries per page and the experiment runner treats a failed fetch as a
  failed run — it never fabricates a partial ranking.
- **Fundamentals lag.** ROE and dividend yield come from the latest
  published report/distribution, which can be months old.
- **No transaction costs, no tradability filter** beyond ST exclusion
  (limit-up/limit-down names are still ranked). The experiment measures
  signal, not an investable portfolio.
