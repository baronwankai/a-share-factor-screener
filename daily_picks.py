#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日选股预测 vs 实际 验证系统
==============================
每次运行做四件事:
  1. 判断今天是否为 A 股交易日(akshare tool_trade_date_hist_sina);
     不是交易日 -> 打印 SKIP 退出(exit 0)。
  2. 拉今日全A股收盘快照(东方财富 clist 直连, 剔除ST), 合并 ROE(半年报)
     与股息率(2025年报); 五因子(PE/PB/ROE/股息率/60日动量)齐全且 PE>0 的
     股票参与排名, 各因子做百分位排名后取平均为综合分;
     快照存 data/snapshot-YYYY-MM-DD.json。
  3. 结算此前未结算的预测(正常节奏下即上一交易日): 用今日收盘价算每只
     入选股涨跌幅, 减去中证500同期涨跌幅(以预测文件里存的 benchmark_close
     为起点), 超额>0 跑赢 / <0 跑输; 结果写回预测文件, 并重算
     scorecard.json 累计战绩(由全部已结算文件汇总, 幂等)。
  4. 产出今日预测: 综合分 Top 20 存 picks/picks-YYYY-MM-DD.json
     (预测定义: 次一交易日跑赢中证500), 并生成 report-YYYY-MM-DD.md。

基准指数: 中证500(000905)。今日收盘取东方财富 82.push2 单指数行情
(80.push2/push2his 在本机代理下不通, 故不用 akshare index_zh_a_hist;
 历史收盘用新浪 stock_zh_index_daily 作兜底)。

运行: ./daily_picks.py（依赖: akshare, pandas, requests）
"""
import json
import math
import os
import sys
import time
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
PICKS_DIR = os.path.join(BASE, "picks")
SCORECARD = os.path.join(BASE, "scorecard.json")
SCREENER_JSON = os.path.expanduser("~/workspace/your_files/stock-screener/data.json")
BENCH_CODE = "000905"
BENCH_NAME = "中证500"

import requests
import pandas as pd
import akshare as ak


def _num(x):
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, allow_nan=False)


# ---------------- 1. 交易日判断 ----------------
def is_trading_day(d):
    cal = ak.tool_trade_date_hist_sina()
    days = set(cal["trade_date"].astype(str))
    return d.isoformat() in days


# ---------------- 2a. 行情快照(东方财富 clist, 同选股筛选器) ----------------
CLIST_URL = "https://82.push2.eastmoney.com/api/qt/clist/get"
CLIST_PARAMS = {
    "po": 1, "np": 1,
    "ut": "bd1d9ddb04089700cf9c27f6f7426281",
    "fltt": 2, "invt": 2, "fid": "f12",
    "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
    "fields": "f12,f14,f2,f3,f9,f20,f21,f23,f24,f25",
}


def _get_page(pn, pz=100, tries=8):
    for i in range(tries):
        try:
            r = requests.get(CLIST_URL, params={**CLIST_PARAMS, "pn": pn, "pz": pz}, timeout=25)
            j = r.json()
            if j.get("data") and isinstance(j["data"].get("diff"), list):
                return j["data"]
        except Exception:
            pass
        time.sleep(0.6 + i * 0.8)
    return None


def fetch_spot():
    print("抓取行情快照...")
    first = _get_page(1)
    if not first:
        raise RuntimeError("行情快照首页抓取失败")
    total = first["total"]
    pages = (total + 99) // 100
    print("  共 %d 只, %d 页" % (total, pages))
    rows = list(first["diff"])
    for pn in range(2, pages + 1):
        d = _get_page(pn)
        if d:
            rows.extend(d["diff"])
        if pn % 20 == 0:
            print("  已抓 %d/%d 页" % (pn, pages))
        time.sleep(0.15)
    out = []
    for s in rows:
        code = str(s.get("f12", "")).strip()
        name = str(s.get("f14", "")).strip()
        price = _num(s.get("f2"))
        if not code or not name or price is None:
            continue
        if "ST" in name.upper():
            continue
        mcap = _num(s.get("f20"))
        out.append({
            "code": code, "name": name, "price": round(price, 2),
            "chg": _num(s.get("f3")),
            "pe": _num(s.get("f9")),
            "pb": _num(s.get("f23")),
            "mcap": round(mcap / 1e8, 1) if mcap else None,
            "mom60": _num(s.get("f24")),
            "ytd": _num(s.get("f25")),
        })
    print("  快照有效 %d 只(已剔除ST)" % len(out))
    return out


# ---------------- 2b. ROE / 股息率(akshare 优先, 筛选器快照兜底) ----------------
ROE_DATE = "20260630"   # 2026年半年报
DIV_DATE = "20251231"   # 2025年报


def _screener_fallback():
    if not os.path.exists(SCREENER_JSON):
        return {}, {}
    j = load_json(SCREENER_JSON)
    roe, div = {}, {}
    for s in j.get("stocks", []):
        if s.get("roe") is not None:
            roe[s["code"]] = s["roe"]
        if s.get("div") is not None:
            div[s["code"]] = s["div"]
    return roe, div


def fetch_roe_div():
    fb_roe, fb_div = _screener_fallback()
    roe_map, div_map = {}, {}
    print("抓取ROE(半年报)...")
    for attempt in range(3):
        try:
            df = ak.stock_yjbb_em(date=ROE_DATE)
            df = df.dropna(subset=["股票代码"]).copy()
            df["股票代码"] = df["股票代码"].astype(str).str.zfill(6)
            df = df.sort_values("最新公告日期").drop_duplicates("股票代码", keep="last")
            for _, r in df.iterrows():
                v = _num(r.get("净资产收益率"))
                if v is not None:
                    roe_map[r["股票代码"]] = round(v, 2)
            break
        except Exception as e:
            print("  ROE第%d次失败: %s" % (attempt + 1, type(e).__name__))
            time.sleep(5)
    if roe_map:
        print("  ROE覆盖 %d 只(akshare)" % len(roe_map))
    elif fb_roe:
        roe_map = fb_roe
        print("  ROE改用选股筛选器快照兜底, 覆盖 %d 只" % len(roe_map))

    print("抓取股息率(2025年报分红)...")
    for attempt in range(3):
        try:
            df = ak.stock_fhps_em(date=DIV_DATE)
            df = df.dropna(subset=["代码"]).copy()
            df["代码"] = df["代码"].astype(str).str.zfill(6)
            df = df.sort_values("最新公告日期").drop_duplicates("代码", keep="last")
            for _, r in df.iterrows():
                v = _num(r.get("现金分红-股息率"))
                if v is not None:
                    div_map[r["代码"]] = round(v * 100, 2)
            break
        except Exception as e:
            print("  股息率第%d次失败: %s" % (attempt + 1, type(e).__name__))
            time.sleep(5)
    if div_map:
        print("  股息率覆盖 %d 只(akshare)" % len(div_map))
    elif fb_div:
        div_map = fb_div
        print("  股息率改用选股筛选器快照兜底, 覆盖 %d 只" % len(div_map))
    return roe_map, div_map


# ---------------- 基准指数 ----------------
def fetch_benchmark_today():
    """今日中证500收盘: 东方财富 82.push2 单指数行情(f43收盘 f60昨收 f170涨跌幅%)。"""
    url = "https://82.push2.eastmoney.com/api/qt/stock/get"
    params = {"secid": "1." + BENCH_CODE, "ut": "bd1d9ddb04089700cf9c27f6f7426281",
              "fields": "f43,f57,f58,f60,f169,f170", "fltt": 2, "invt": 2}
    for i in range(6):
        try:
            r = requests.get(url, params=params, timeout=20)
            d = r.json().get("data")
            if d and _num(d.get("f43")):
                return {"code": BENCH_CODE, "name": BENCH_NAME,
                        "close": _num(d["f43"]), "prev_close": _num(d.get("f60")),
                        "chg_pct": _num(d.get("f170"))}
        except Exception:
            pass
        time.sleep(1.5 + i)
    # 兜底: 新浪指数日线(需已有今日行)
    df = ak.stock_zh_index_daily(symbol="sh" + BENCH_CODE)
    df["date"] = df["date"].astype(str)
    today = datetime.date.today().isoformat()
    row = df[df["date"] == today]
    if len(row):
        close = float(row.iloc[-1]["close"])
        prev = float(df[df["date"] < today].iloc[-1]["close"])
        return {"code": BENCH_CODE, "name": BENCH_NAME, "close": round(close, 2),
                "prev_close": round(prev, 2), "chg_pct": round((close / prev - 1) * 100, 2)}
    raise RuntimeError("中证500今日收盘获取失败(东财现货与新浪日线均不可用)")


# ---------------- 因子综合分 ----------------
def score_stocks(stocks):
    """五因子齐全且 PE>0 参与排名; 返回 (参与排名的DataFrame, ) 。"""
    elig = [s for s in stocks
            if s.get("pe") is not None and s["pe"] > 0
            and s.get("pb") is not None and s.get("roe") is not None
            and s.get("div") is not None and s.get("mom60") is not None]
    df = pd.DataFrame(elig)
    if df.empty:
        return df
    # 百分位"优度"(0-100): PE/PB 越低越好, 其余越高越好
    df["g_pe"] = (1 - df["pe"].rank(pct=True)) * 100
    df["g_pb"] = (1 - df["pb"].rank(pct=True)) * 100
    df["g_roe"] = df["roe"].rank(pct=True) * 100
    df["g_div"] = df["div"].rank(pct=True) * 100
    df["g_mom"] = df["mom60"].rank(pct=True) * 100
    df["score"] = df[["g_pe", "g_pb", "g_roe", "g_div", "g_mom"]].mean(axis=1).round(2)
    return df


# ---------------- 3. 结算 ----------------
def settle_pending(today_str, price_map, bench_today_close):
    """结算 picks/ 下所有 date<today 且未结算的预测文件。返回结算摘要列表。"""
    summaries = []
    if not os.path.isdir(PICKS_DIR):
        return summaries
    files = sorted(f for f in os.listdir(PICKS_DIR)
                   if f.startswith("picks-") and f.endswith(".json"))
    for fn in files:
        path = os.path.join(PICKS_DIR, fn)
        j = load_json(path)
        if j.get("settled") or j.get("date", "") >= today_str:
            continue
        base_close = j.get("benchmark_close")
        if not base_close:
            print("  跳过 %s: 缺 benchmark_close" % fn)
            continue
        bench_ret = (bench_today_close / base_close - 1) * 100
        n_win = n_loss = n_flat = n_nodata = 0
        excess_list = []
        for p in j["picks"]:
            cur = price_map.get(p["code"])
            if cur is None:
                p["settle"] = {"settle_date": today_str, "close": None,
                               "ret_pct": None, "bench_ret_pct": round(bench_ret, 2),
                               "excess_pct": None, "result": "无数据"}
                n_nodata += 1
                continue
            ret = (cur / p["price"] - 1) * 100
            excess = ret - bench_ret
            if excess > 0:
                result, n_win = "跑赢", n_win + 1
            elif excess < 0:
                result, n_loss = "跑输", n_loss + 1
            else:
                result, n_flat = "持平", n_flat + 1
            excess_list.append(excess)
            p["settle"] = {"settle_date": today_str, "close": cur,
                           "ret_pct": round(ret, 2), "bench_ret_pct": round(bench_ret, 2),
                           "excess_pct": round(excess, 2), "result": result}
        n_data = n_win + n_loss + n_flat
        j["settled"] = True
        j["settled_on"] = today_str
        j["settlement"] = {
            "bench_close_then": base_close, "bench_close_now": bench_today_close,
            "bench_ret_pct": round(bench_ret, 2),
            "count": len(j["picks"]), "with_data": n_data,
            "win": n_win, "loss": n_loss, "flat": n_flat, "no_data": n_nodata,
            "win_rate": round(n_win / n_data * 100, 1) if n_data else None,
            "avg_excess_pct": round(sum(excess_list) / len(excess_list), 2) if excess_list else None,
        }
        save_json(j, path)
        summaries.append(j)
        print("  已结算 %s: %d只, 跑赢%d/跑输%d, 平均超额%s%%"
              % (fn, n_data, n_win, n_loss, j["settlement"]["avg_excess_pct"]))
    return summaries


def rebuild_scorecard():
    """由全部已结算预测文件汇总累计战绩(幂等)。"""
    records = []
    if os.path.isdir(PICKS_DIR):
        for fn in sorted(os.listdir(PICKS_DIR)):
            if not (fn.startswith("picks-") and fn.endswith(".json")):
                continue
            j = load_json(os.path.join(PICKS_DIR, fn))
            if not j.get("settled"):
                continue
            for p in j["picks"]:
                st = p.get("settle") or {}
                if st.get("excess_pct") is None:
                    continue
                records.append({"date": j["date"], "code": p["code"], "name": p["name"],
                                "excess_pct": st["excess_pct"], "result": st["result"]})
    total = len(records)
    wins = sum(1 for r in records if r["excess_pct"] > 0)
    card = {
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "benchmark": "%s(%s)" % (BENCH_NAME, BENCH_CODE),
        "total_settled": total,
        "win": wins,
        "loss": sum(1 for r in records if r["excess_pct"] < 0),
        "flat": sum(1 for r in records if r["excess_pct"] == 0),
        "win_rate": round(wins / total * 100, 1) if total else None,
        "avg_excess_pct": round(sum(r["excess_pct"] for r in records) / total, 2) if total else None,
        "best3": sorted(records, key=lambda r: -r["excess_pct"])[:3],
        "worst3": sorted(records, key=lambda r: r["excess_pct"])[:3],
    }
    save_json(card, SCORECARD)
    return card


# ---------------- 报告 ----------------
def fmt(v, suffix=""):
    return "—" if v is None else ("%s%s" % (v, suffix))


def write_report(today_str, settled_list, card, picks_j, bench):
    lines = []
    lines.append("# 每日选股验证报告 %s" % today_str)
    lines.append("")
    lines.append("基准：%s（%s）今日收盘 %.2f，涨跌幅 %s%%。预测定义：入选股在次一交易日跑赢中证500（超额>0）。"
                 % (BENCH_NAME, BENCH_CODE, bench["close"], fmt(bench.get("chg_pct"))))
    lines.append("")
    lines.append("## 昨日预测结算")
    lines.append("")
    if not settled_list:
        lines.append("无待结算的预测（首日运行或此前预测已全部结算）。")
        lines.append("")
    for j in settled_list:
        sm = j["settlement"]
        lines.append("### %s 的预测（%s 结算）" % (j["date"], j["settled_on"]))
        lines.append("")
        lines.append("中证500同期涨跌 %s%%；本批 %d 只，跑赢 %d / 跑输 %d，胜率 %s%%，平均超额 %s%%。"
                     % (fmt(sm["bench_ret_pct"]), sm["with_data"], sm["win"], sm["loss"],
                        fmt(sm["win_rate"]), fmt(sm["avg_excess_pct"])))
        lines.append("")
        lines.append("| 代码 | 名称 | 买入价 | 结算价 | 涨跌% | 超额% | 结果 |")
        lines.append("|---|---|---|---|---|---|---|")
        for p in j["picks"]:
            st = p.get("settle") or {}
            lines.append("| %s | %s | %s | %s | %s | %s | %s |"
                         % (p["code"], p["name"], fmt(p["price"]), fmt(st.get("close")),
                            fmt(st.get("ret_pct")), fmt(st.get("excess_pct")), st.get("result", "—")))
        lines.append("")
    lines.append("## 累计记分牌")
    lines.append("")
    if card["total_settled"]:
        lines.append("已结算 %d 只，跑赢 %d 只，胜率 %s%%，平均超额 %s%%。"
                     % (card["total_settled"], card["win"], fmt(card["win_rate"]), fmt(card["avg_excess_pct"])))
        if card["best3"]:
            lines.append("最佳3只：" + "；".join(
                "%s(%s, %s, 超额%s%%)" % (r["name"], r["code"], r["date"], r["excess_pct"]) for r in card["best3"]))
        if card["worst3"]:
            lines.append("最差3只：" + "；".join(
                "%s(%s, %s, 超额%s%%)" % (r["name"], r["code"], r["date"], r["excess_pct"]) for r in card["worst3"]))
    else:
        lines.append("尚无已结算记录（首日运行，记分牌为空属正常）。")
    lines.append("")
    lines.append("## 今日预测 Top 20（%s）" % today_str)
    lines.append("")
    lines.append("综合分 = PE/PB/ROE/股息率/60日动量 五因子百分位均值（PE、PB 越低越好，其余越高越好）；"
                 "参与排名 %d 只（五因子齐全且 PE>0、已剔除ST）。" % picks_j["universe"])
    lines.append("")
    lines.append("| # | 代码 | 名称 | 收盘价 | 综合分 | PE | PB | ROE% | 股息率% | 60日涨幅% |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, p in enumerate(picks_j["picks"], 1):
        lines.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
                     % (i, p["code"], p["name"], fmt(p["price"]), fmt(p["score"]),
                        fmt(p["pe"]), fmt(p["pb"]), fmt(p["roe"]), fmt(p["div"]), fmt(p["mom60"])))
    lines.append("")
    lines.append("下个交易日收盘后结算，看这 20 只里有几只跑赢中证500。")
    path = os.path.join(BASE, "report-%s.md" % today_str)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


# ---------------- 主流程 ----------------
def main():
    today = datetime.date.today()
    today_str = today.isoformat()
    print("日期: %s" % today_str)
    if not is_trading_day(today):
        print("SKIP: %s 不是 A 股交易日" % today_str)
        return 0
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PICKS_DIR, exist_ok=True)

    stocks = fetch_spot()
    roe_map, div_map = fetch_roe_div()
    n_roe = n_div = 0
    for s in stocks:
        s["roe"] = roe_map.get(s["code"])
        s["div"] = div_map.get(s["code"])
        if s["roe"] is not None:
            n_roe += 1
        if s["div"] is not None:
            n_div += 1

    df = score_stocks(stocks)
    score_map = {}
    if not df.empty:
        for _, r in df.iterrows():
            score_map[r["code"]] = float(r["score"])
    for s in stocks:
        s["score"] = score_map.get(s["code"])
    snap = {
        "date": today_str,
        "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "东方财富行情快照+半年报ROE+2025年报股息率; 已剔除ST",
        "count": len(stocks),
        "coverage": {"roe": n_roe, "div": n_div},
        "universe": len(score_map),
        "stocks": stocks,
    }
    snap_path = os.path.join(DATA_DIR, "snapshot-%s.json" % today_str)
    save_json(snap, snap_path)
    print("快照已存 %s (参与排名 %d 只)" % (snap_path, len(score_map)))

    bench = fetch_benchmark_today()
    print("中证500今日收盘 %.2f (%s%%)" % (bench["close"], bench.get("chg_pct")))

    price_map = {s["code"]: s["price"] for s in stocks}
    print("结算未结算的预测...")
    settled_list = settle_pending(today_str, price_map, bench["close"])
    card = rebuild_scorecard()
    print("累计记分牌: 已结算%d只 胜率%s%% 平均超额%s%%"
          % (card["total_settled"], card["win_rate"], card["avg_excess_pct"]))

    top = df.sort_values(["score", "mcap", "code"], ascending=[False, False, True]).head(20)
    picks = []
    for _, r in top.iterrows():
        picks.append({
            "code": r["code"], "name": r["name"], "price": float(r["price"]),
            "score": float(r["score"]), "pe": float(r["pe"]), "pb": float(r["pb"]),
            "roe": float(r["roe"]), "div": float(r["div"]), "mom60": float(r["mom60"]),
        })
    picks_j = {
        "date": today_str,
        "definition": "次一交易日跑赢中证500(超额收益>0)",
        "benchmark": BENCH_CODE,
        "benchmark_close": bench["close"],
        "benchmark_chg_pct": bench.get("chg_pct"),
        "universe": len(score_map),
        "picks": picks,
        "settled": False,
    }
    picks_path = os.path.join(PICKS_DIR, "picks-%s.json" % today_str)
    save_json(picks_j, picks_path)
    print("今日预测已存 %s" % picks_path)

    report_path = write_report(today_str, settled_list, card, picks_j, bench)
    print("报告已存 %s" % report_path)
    print("今日 Top 20:")
    for i, p in enumerate(picks, 1):
        print("  %2d. %s %s 分%.2f 价%.2f" % (i, p["code"], p["name"], p["score"], p["price"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
