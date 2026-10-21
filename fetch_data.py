#!/home/hatch/workspace/.venv-stock/bin/python
# -*- coding: utf-8 -*-
"""
A股因子选股筛选器 - 数据抓取脚本
================================
数据源(全部来自东方财富, akshare 接口底层同源):
  1. 行情快照: 东方财富 clist API(直连, 逐页重试)
     -> 代码/名称/最新价/涨跌幅/动态PE/市净率PB/总市值/60日涨跌幅
  2. ROE: akshare.stock_yjbb_em(2026年半年报"净资产收益率")
  3. 股息率: akshare.stock_fhps_em(2025年报"现金分红-股息率")

输出: 同目录 data.json, 结构:
  {"fetched_at": "2026-10-20 10:30:00", "count": N,
   "coverage": {"roe": n1, "div": n2}, "stocks": [...]}

规则: 排除 ST 股(含*ST); 缺失字段记为 null; PE<=0 视为无效(前端过滤时不通过PE上限条件)。
刷新: 直接运行 ./fetch_data.py (或 python3 fetch_data.py, 需 akshare+pandas)。
"""
import json
import math
import os
import sys
import time
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "data.json")

try:
    import requests
    import pandas as pd
except ImportError as e:
    sys.exit("缺少依赖: %s。请用自带 venv 运行: /home/hatch/workspace/.venv-stock/bin/python fetch_data.py" % e)

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    print("警告: 未安装 akshare, ROE/股息率将为空, 仅抓行情快照。")

# ---------------- 1. 行情快照(东方财富 clist, 逐页+重试) ----------------
CLIST_URL = "https://82.push2.eastmoney.com/api/qt/clist/get"
CLIST_PARAMS = {
    "po": 1, "np": 1,
    "ut": "bd1d9ddb04089700cf9c27f6f7426281",
    "fltt": 2, "invt": 2, "fid": "f12",
    "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",  # 深A/沪A/科创/北交所
    "fields": "f12,f14,f2,f3,f9,f20,f21,f23,f24,f25",
}
# f12代码 f14名称 f2最新价 f3涨跌幅% f9动态PE f20总市值(元) f21流通市值(元)
# f23市净率 f24 60日涨跌幅% f25 年初至今涨跌幅%

def _get_page(pn, pz=100, tries=8):
    for i in range(tries):
        try:
            r = requests.get(CLIST_URL, params={**CLIST_PARAMS, "pn": pn, "pz": pz}, timeout=25)
            j = r.json()
            if j.get("data") and isinstance(j["data"].get("diff"), list):
                return j["data"]
        except Exception as e:
            if i == tries - 1:
                print("  第%d页最终失败: %s" % (pn, type(e).__name__))
        time.sleep(0.6 + i * 0.8)
    return None

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
        if pn % 15 == 0:
            print("  已抓 %d/%d 页" % (pn, pages))
        time.sleep(0.15)
    out = []
    for s in rows:
        code = str(s.get("f12", "")).strip()
        name = str(s.get("f14", "")).strip()
        price = _num(s.get("f2"))
        if not code or not name or price is None:
            continue
        if "ST" in name.upper():  # 排除 ST/*ST
            continue
        mcap = _num(s.get("f20"))
        out.append({
            "code": code, "name": name, "price": round(price, 2),
            "chg": _num(s.get("f3")),
            "pe": _num(s.get("f9")),
            "pb": _num(s.get("f23")),
            "mcap": round(mcap / 1e8, 1) if mcap else None,  # 亿元
            "mom60": _num(s.get("f24")),   # 60日涨跌幅 %
            "ytd": _num(s.get("f25")),
        })
    print("  快照有效 %d 只(已剔除ST)" % len(out))
    return out

# ---------------- 2. ROE(半年报) ----------------
REPORT_DATE = "20260630"  # 2026年半年报(最新完整季报; 三季报10月底才披露完)

def fetch_roe():
    if not HAS_AKSHARE:
        return {}
    print("抓取ROE(半年报)...")
    for attempt in range(3):
        try:
            df = ak.stock_yjbb_em(date=REPORT_DATE)
            break
        except Exception as e:
            print("  ROE第%d次失败: %s" % (attempt + 1, type(e).__name__))
            time.sleep(5)
    else:
        print("  ROE抓取失败, 置空")
        return {}
    df = df.dropna(subset=["股票代码"]).copy()
    df["股票代码"] = df["股票代码"].astype(str).str.zfill(6)
    df = df.sort_values("最新公告日期").drop_duplicates("股票代码", keep="last")
    m = {}
    for _, r in df.iterrows():
        v = _num(r.get("净资产收益率"))
        if v is not None:
            m[r["股票代码"]] = round(v, 2)  # 已是%
    print("  ROE覆盖 %d 只" % len(m))
    return m

# ---------------- 3. 股息率(2025年报现金分红) ----------------
DIV_DATE = "20251231"

def fetch_div():
    if not HAS_AKSHARE:
        return {}
    print("抓取股息率(2025年报分红)...")
    for attempt in range(3):
        try:
            df = ak.stock_fhps_em(date=DIV_DATE)
            break
        except Exception as e:
            print("  股息率第%d次失败: %s" % (attempt + 1, type(e).__name__))
            time.sleep(5)
    else:
        print("  股息率抓取失败, 置空")
        return {}
    df = df.dropna(subset=["代码"]).copy()
    df["代码"] = df["代码"].astype(str).str.zfill(6)
    df = df.sort_values("最新公告日期").drop_duplicates("代码", keep="last")
    m = {}
    for _, r in df.iterrows():
        v = _num(r.get("现金分红-股息率"))
        if v is not None:
            m[r["代码"]] = round(v * 100, 2)  # 转为%
    print("  股息率覆盖 %d 只" % len(m))
    return m

# ---------------- 主流程 ----------------
def main():
    t0 = time.time()
    stocks = fetch_spot()
    roe_map = fetch_roe()
    div_map = fetch_div()
    n_roe = n_div = 0
    for s in stocks:
        r = roe_map.get(s["code"])
        d = div_map.get(s["code"])
        s["roe"] = r
        s["div"] = d
        if r is not None: n_roe += 1
        if d is not None: n_div += 1
    payload = {
        "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "东方财富(行情快照/60日涨跌幅)+半年报ROE+2025年报股息率; 已剔除ST",
        "count": len(stocks),
        "coverage": {"roe": n_roe, "div": n_div},
        "stocks": stocks,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, allow_nan=False)
    print("写入 %s, 共 %d 只, ROE覆盖%d, 股息率覆盖%d, 用时%.0f秒"
          % (OUT, len(stocks), n_roe, n_div, time.time() - t0))

if __name__ == "__main__":
    main()
