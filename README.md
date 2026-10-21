# A-Share Factor Stock Screener

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-brightgreen)](https://baronwankai.github.io/a-share-factor-screener/)
![Data snapshot](https://img.shields.io/badge/Data%20snapshot-2026--10--20-blue)
![Market](https://img.shields.io/badge/Market-China%20A--shares-red)

A free, open-source, **single-file web screener** for the full China A-share
market — **5,373 listed companies** (ST/*ST excluded) scored with a
transparent **five-factor model**. No build step, no server, no tracking:
all data is embedded in one HTML file and every filter runs locally in
your browser.

### ▶ Live demo: **https://baronwankai.github.io/a-share-factor-screener/**

---

## The five-factor model

| Factor | Metric | What it captures |
|---|---|---|
| Value | P/E (dynamic) | Cheapness vs. earnings |
| Value | P/B | Cheapness vs. book value |
| Quality | ROE (latest report) | Capital efficiency |
| Income | Dividend yield | Cash returned to shareholders |
| Momentum | 60-day price change | Medium-term trend strength |

Each factor is percentile-ranked across the whole market; the composite
score is the average of the five percentile ranks. Market capitalisation
is available as an additional filter. The model is deliberately simple
and fully transparent — no black box.

## What's in this repo

| File | Purpose |
|---|---|
| `index.html` | The screener itself — self-contained, open it and screen instantly |
| `fetch_data.py` | Data pipeline: rebuilds the snapshot from public market data (Eastmoney quote/fundamental endpoints via akshare) |
| `data.json` | The current snapshot produced by the pipeline (quotes, P/E, P/B, market cap, 60-day momentum, ROE, dividend yield) |
| `snapshot_stats.py` | Zero-dependency checker: factor coverage + recomputed Top 20 for any snapshot (its rankable count, 3,259, reproduces the experiment's recorded universe exactly) |
| `daily_picks.py` | Prediction-tracking experiment built on the same model (see below) |
| `experiment/` | The experiment's raw records — daily picks, reports and the cumulative scorecard, committed as generated |
| `docs/` | [`METHODOLOGY.md`](docs/METHODOLOGY.md) (factor spec) and [`EXPERIMENT.md`](docs/EXPERIMENT.md) (pre-registered protocol and run log, failures included) |

## The experiment: daily Top 20 vs. CSI 500

The same five-factor model runs as a **pre-registered prediction
experiment**: every trading day after close, `daily_picks.py`

1. checks the A-share trading calendar,
2. scores the full market and records the **Top 20** composite-score
   stocks as the prediction *"will outperform the CSI 500 (000905)
   tomorrow"*,
3. settles the previous day's picks against actual closes and keeps a
   cumulative scorecard (hit rate and average excess return).

No cherry-picking, no retroactive edits — every prediction is written to
disk before the outcome is known. This is the maintenance workload the
project exists to support: a small, honest, fully reproducible quant
research loop that anyone can re-run.

## Quick start

```bash
# Option A — just screen (zero install)
open index.html
# …or use the live demo link above.

# Option B — refresh the data snapshot, then screen
pip install akshare pandas requests
python fetch_data.py        # writes data.json
open index.html

# Option C — run the daily prediction experiment
python daily_picks.py       # settles yesterday's picks, emits today's Top 20
```

## Data sources & disclaimer

Quotes, fundamentals and the trading calendar come from public endpoints
(Eastmoney / Sina via akshare). Data is a point-in-time snapshot for
**research and education only — nothing here is investment advice.**
Verify against official exchange sources before making any decision.

## Roadmap

- Scheduled snapshot refresh (GitHub Actions) so the demo stays current
- English UI toggle for the screener page
- Additional factors (free-cash-flow yield, volatility) behind flags
- Scorecard visualisation for the prediction experiment

## Contributing

Issues and pull requests are welcome — data-source fixes are especially
valuable, as public endpoints change without notice.

## License

MIT — see [LICENSE](LICENSE).

## Maintainer

**Kai Wan** ([@baronwankai](https://github.com/baronwankai)) — designed the
factor model, built the screener, the data pipeline and the experiment
runner, and maintains all of it.

---

中文说明：全 A 股五因子选股筛选器（低 PE / 低 PB / 高 ROE / 高股息 /
60 日动量，剔除 ST），单文件网页、浏览器本地运行；`fetch_data.py`
刷新数据快照，`daily_picks.py` 是基于同一模型的每日 Top 20 对中证500
的预测验证实验。仅供研究学习，不构成投资建议。
