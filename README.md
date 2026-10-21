# A-Share Factor Stock Screener

A single-file, browser-based stock screener for the full China A-share market
(5,300+ listed companies, ST stocks excluded). No build step, no server —
open `index.html` and screen instantly.

**Live demo:** open `index.html` in any modern browser (or serve this repo
with GitHub Pages).

## Features

- **Five-factor model** — value (P/E, P/B), quality (ROE), income
  (dividend yield) and momentum (60-day price change), plus market-cap
  filtering.
- **Full-market coverage** — snapshot covers every A-share listing
  (5,373 stocks in the current snapshot), ST/*ST names excluded.
- **Zero dependencies at runtime** — all data is embedded in the single
  HTML file; filtering and ranking happen locally in the browser.
- **Refreshable data** — `fetch_data.py` rebuilds the snapshot from
  public market data (Eastmoney quote/fundamental endpoints via akshare):
  quotes, dynamic P/E, P/B, market cap, 60-day momentum, ROE
  (latest interim/annual report) and dividend yield.

## Usage

```bash
# 1. (Optional) refresh the data snapshot
pip install akshare pandas
python fetch_data.py        # writes data.json

# 2. open the screener
open index.html             # or: python -m http.server, then visit the page
```

## How it works

`fetch_data.py` pulls a full-market quote snapshot and joins it with ROE
and dividend-yield tables, producing `data.json`. The screener page scores
and ranks stocks with the five factors above; composite-score ranking is
the same model used in the maintainer's daily Top-20 vs. CSI 500
prediction-tracking experiment.

## Data & disclaimer

Market data is a point-in-time snapshot for research and education only.
**Nothing in this project is investment advice.** Data may be delayed or
inaccurate; verify against official exchange sources before making any
decision.

## License

MIT — see [LICENSE](LICENSE).

## Maintainer

Kai Wan — issues and pull requests welcome.

---

中文说明：全 A 股五因子选股筛选器（低 PE / 低 PB / 高 ROE / 高股息 /
60 日动量，剔除 ST），单文件网页、浏览器本地运行；`fetch_data.py`
可从东方财富公开接口刷新数据快照。仅供研究学习，不构成投资建议。
