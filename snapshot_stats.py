#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Snapshot statistics for the A-Share Factor Stock Screener.

Loads data.json, reports factor coverage, and recomputes the five-factor
composite ranking exactly as specified in docs/METHODOLOGY.md
(percentile ranks; P/E and P/B inverted; unweighted mean).
Pure standard library — no third-party dependencies.

Usage: python snapshot_stats.py [path-to-data.json]
"""
import json
import sys

FACTORS = [  # (field, higher_is_better)
    ("pe", False),
    ("pb", False),
    ("roe", True),
    ("div", True),
    ("mom60", True),
]


def percentile_ranks(values, higher_is_better):
    """Return {index: percentile 0..100}; ties share the mid-rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        mid = (i + j) / 2.0  # 0-based mid-rank
        pct = mid / (len(order) - 1) * 100 if len(order) > 1 else 100.0
        if not higher_is_better:
            pct = 100.0 - pct
        for k in range(i, j + 1):
            ranks[order[k]] = pct
        i = j + 1
    return ranks


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data.json"
    with open(path, encoding="utf-8") as f:
        snap = json.load(f)
    stocks = snap["stocks"]
    print(f"Snapshot: {snap.get('fetched_at')}  source: {snap.get('source')}")
    print(f"Total stocks in snapshot: {len(stocks)}")

    print("\nFactor coverage (non-null):")
    for field, _ in FACTORS:
        n = sum(1 for s in stocks if s.get(field) is not None)
        print(f"  {field:>6}: {n:>5} ({n / len(stocks) * 100:.1f}%)")

    rankable = [
        s for s in stocks
        if all(s.get(f) is not None for f, _ in FACTORS) and (s.get("pe") or 0) > 0
    ]
    print(f"\nRankable (all 5 factors present, P/E > 0): {len(rankable)}")

    pct_by_factor = {}
    for field, hib in FACTORS:
        pct_by_factor[field] = percentile_ranks([s[field] for s in rankable], hib)
    scored = []
    for idx, s in enumerate(rankable):
        score = sum(pct_by_factor[f][idx] for f, _ in FACTORS) / len(FACTORS)
        scored.append((score, s))
    scored.sort(key=lambda t: -t[0])

    print("\nTop 20 composite scores in this snapshot:")
    print(f"{'#':>3} {'code':<8}{'name':<10}{'score':>7}{'PE':>8}{'PB':>6}{'ROE%':>7}{'DIV%':>7}{'MOM60%':>8}")
    for i, (score, s) in enumerate(scored[:20], 1):
        print(f"{i:>3} {s['code']:<8}{s['name']:<10}{score:>7.2f}"
              f"{s['pe']:>8.2f}{s['pb']:>6.2f}{s['roe']:>7.2f}{s['div']:>7.2f}{s['mom60']:>8.2f}")


if __name__ == "__main__":
    main()
