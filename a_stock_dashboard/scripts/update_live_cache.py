from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests


os.environ["A_STOCK_USE_LIVE_DATA"] = "1"
os.environ["A_STOCK_USE_CACHED_DATA"] = "0"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import PUBLIC_HOLDINGS_FILE  # noqa: E402
from modules.data_fetcher import FetchResult, fetch_market_overview, fetch_overseas_market, fetch_sector_rank, write_fetch_cache  # noqa: E402
from modules.sector_analyzer import add_sector_state  # noqa: E402
from modules.stock_analyzer import score_stocks  # noqa: E402
from modules.market_analyzer import summarize_market  # noqa: E402
from modules.utils import now_text, safe_float  # noqa: E402


EASTMONEY_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://quote.eastmoney.com/center/gridlist.html",
}


def _empty_stock_rows() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "stock_code",
            "stock_name",
            "industry",
            "concept",
            "price",
            "pct_chg",
            "pct_chg_5d",
            "pct_chg_10d",
            "pct_chg_20d",
            "amount_yi",
            "turnover_rate",
            "volume_ratio",
            "ma5",
            "ma10",
            "ma20",
            "ma60",
            "sector_score",
            "is_st",
            "is_delist",
        ]
    )


def fetch_public_holding_stocks(sectors: pd.DataFrame, market_score: float) -> FetchResult:
    if not PUBLIC_HOLDINGS_FILE.exists():
        return FetchResult(_empty_stock_rows(), now_text(), "AKShare")

    holdings = pd.read_csv(PUBLIC_HOLDINGS_FILE, dtype={"stock_code": str})
    codes = set(holdings["stock_code"].astype(str).str.zfill(6))
    if not codes:
        return FetchResult(_empty_stock_rows(), now_text(), "AKShare")

    try:
        spot = fetch_tencent_holding_quotes(codes)
        quote_source = "腾讯行情"
    except Exception as tencent_exc:  # noqa: BLE001
        try:
            spot = fetch_public_holding_quotes(codes)
            quote_source = "东方财富"
        except Exception as eastmoney_exc:  # noqa: BLE001
            spot = pd.DataFrame()
            quote_source = ""
            exc = RuntimeError(f"腾讯行情失败：{type(tencent_exc).__name__}；东方财富失败：{type(eastmoney_exc).__name__}")

    if spot.empty:
        rows = []
        for _, holding in holdings.iterrows():
            price = safe_float(holding.get("current_price"), safe_float(holding.get("buy_price")))
            rows.append(
                {
                    "stock_code": str(holding.get("stock_code", "")).zfill(6),
                    "stock_name": holding.get("stock_name", ""),
                    "industry": "持仓导入",
                    "concept": "持仓导入",
                    "price": price,
                    "pct_chg": 0,
                    "pct_chg_5d": 0,
                    "pct_chg_10d": 0,
                    "pct_chg_20d": 0,
                    "amount_yi": 0,
                    "turnover_rate": 0,
                    "volume_ratio": 1,
                    "ma5": price,
                    "ma10": price,
                    "ma20": price,
                    "ma60": price,
                    "sector_score": 50,
                    "is_st": False,
                    "is_delist": False,
                }
            )
        stocks = score_stocks(pd.DataFrame(rows), market_score)
        return FetchResult(stocks, now_text(), "公开持仓兜底", f"持仓实时行情接口失败，保留公开持仓价格。详情：{type(exc).__name__}")

    sector_lookup = dict(zip(sectors["sector_name"], sectors["score"]))
    rows = []
    for _, holding in holdings.iterrows():
        code = str(holding.get("stock_code", "")).zfill(6)
        raw = spot.loc[spot["代码"].astype(str).str.zfill(6).eq(code)]
        if raw.empty:
            price = safe_float(holding.get("current_price"), safe_float(holding.get("buy_price")))
            rows.append(
                {
                    "stock_code": code,
                    "stock_name": holding.get("stock_name", ""),
                    "industry": "持仓导入",
                    "concept": "持仓导入",
                    "price": price,
                    "pct_chg": 0,
                    "pct_chg_5d": 0,
                    "pct_chg_10d": 0,
                    "pct_chg_20d": 0,
                    "amount_yi": 0,
                    "turnover_rate": 0,
                    "volume_ratio": 1,
                    "ma5": price,
                    "ma10": price,
                    "ma20": price,
                    "ma60": price,
                    "sector_score": 50,
                    "is_st": False,
                    "is_delist": False,
                }
            )
            continue

        item = raw.iloc[0]
        price = safe_float(item.get("最新价"), safe_float(holding.get("current_price"), safe_float(holding.get("buy_price"))))
        amount_yi = safe_float(item.get("成交额")) / 100000000
        industry = str(item.get("所属行业", "") or "持仓导入")
        rows.append(
            {
                "stock_code": code,
                "stock_name": str(item.get("名称", holding.get("stock_name", ""))),
                "industry": industry,
                "concept": industry,
                "price": price,
                "pct_chg": safe_float(item.get("涨跌幅")),
                "pct_chg_5d": safe_float(item.get("涨跌幅")),
                "pct_chg_10d": safe_float(item.get("涨跌幅")) * 1.2,
                "pct_chg_20d": safe_float(item.get("涨跌幅")) * 1.6,
                "amount_yi": amount_yi,
                "turnover_rate": safe_float(item.get("换手率")),
                "volume_ratio": safe_float(item.get("量比"), 1),
                "ma5": price,
                "ma10": price,
                "ma20": price,
                "ma60": price,
                "sector_score": sector_lookup.get(industry, 50),
                "is_st": "ST" in str(item.get("名称", "")),
                "is_delist": False,
            }
        )

    stocks = score_stocks(pd.DataFrame(rows), market_score)
    return FetchResult(stocks, now_text(), quote_source)


def fetch_tencent_market_overview() -> FetchResult:
    symbols = {
        "上证指数": ("sh000001", "000001"),
        "深成指": ("sz399001", "399001"),
        "创业板指": ("sz399006", "399006"),
        "科创50": ("sh000688", "000688"),
        "沪深300": ("sh000300", "000300"),
        "中证1000": ("sh000852", "000852"),
    }
    query = ",".join(f"s_{symbol}" for symbol, _ in symbols.values())
    response = requests.get("https://qt.gtimg.cn/q=" + query, headers=EASTMONEY_HEADERS, timeout=12)
    response.raise_for_status()
    text = response.content.decode("gbk", errors="ignore")
    rows = []
    amount_yi = 0.0
    for line in text.splitlines():
        if '="' not in line:
            continue
        payload = line.split('="', 1)[1].rstrip('";')
        parts = payload.split("~")
        if len(parts) < 8 or not parts[2]:
            continue
        name = parts[1]
        code = parts[2]
        rows.append({"name": name, "code": code, "pct_chg": safe_float(parts[5])})
        if code in {"000001", "399001"}:
            amount_yi += safe_float(parts[7]) / 10000
    if not rows:
        raise RuntimeError("腾讯指数接口返回空数据")
    indices = pd.DataFrame(rows)
    return FetchResult(
        {
            "indices": indices,
            "amount_yi": round(amount_yi, 2),
            "amount_5d_avg_yi": round(amount_yi, 2),
            "amount_20d_avg_yi": round(amount_yi, 2),
            "up_count": 0,
            "down_count": 0,
            "limit_up_count": 0,
            "limit_down_count": 0,
            "index_avg_pct": float(indices["pct_chg"].mean()),
        },
        now_text(),
        "腾讯指数行情",
        "市场广度、涨跌停家数暂缺；指数和成交额来自腾讯行情兜底。",
    )


def write_cache_if_useful(name: str, result: FetchResult) -> None:
    if result.source in {"示例数据", "公开持仓兜底"}:
        print(f"skip {name}: source={result.source}, keep previous cache")
        return
    write_fetch_cache(name, result)


def _market_prefix(code: str) -> str:
    if code.startswith(("5", "6", "9")):
        return "1"
    return "0"


def _tencent_prefix(code: str) -> str:
    if code.startswith(("5", "6", "9")):
        return "sh"
    if code.startswith(("0", "1", "2", "3")):
        return "sz"
    return "sz"


def fetch_tencent_holding_quotes(codes: set[str]) -> pd.DataFrame:
    symbols = ",".join(f"s_{_tencent_prefix(code)}{code}" for code in sorted(codes))
    response = requests.get("https://qt.gtimg.cn/q=" + symbols, headers=EASTMONEY_HEADERS, timeout=12)
    response.raise_for_status()
    text = response.content.decode("gbk", errors="ignore")
    rows = []
    for line in text.splitlines():
        if '="' not in line:
            continue
        payload = line.split('="', 1)[1].rstrip('";')
        parts = payload.split("~")
        if len(parts) < 7 or not parts[2]:
            continue
        rows.append(
            {
                "代码": parts[2],
                "名称": parts[1],
                "最新价": safe_float(parts[3]),
                "涨跌幅": safe_float(parts[5]),
                "成交额": safe_float(parts[7]) * 10000 if len(parts) > 7 else 0,
                "换手率": 0,
                "量比": 1,
                "所属行业": "持仓导入",
            }
        )
    if not rows:
        raise RuntimeError("腾讯行情返回空数据")
    return pd.DataFrame(rows)


def fetch_public_holding_quotes(codes: set[str]) -> pd.DataFrame:
    secids = ",".join(f"{_market_prefix(code)}.{code}" for code in sorted(codes))
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f12,f14,f2,f3",
        "secids": secids,
    }
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers=EASTMONEY_HEADERS, timeout=12)
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("data", {}).get("diff", [])
            if not rows:
                raise RuntimeError("东方财富单票接口返回空数据")
            return pd.DataFrame(
                [
                    {
                        "代码": item.get("f12"),
                        "名称": item.get("f14"),
                        "最新价": item.get("f2"),
                        "涨跌幅": item.get("f3"),
                        "成交额": 0,
                        "换手率": 0,
                        "量比": 1,
                        "所属行业": "持仓导入",
                    }
                    for item in rows
                ]
            )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(2 + attempt * 3)
    raise last_exc or RuntimeError("东方财富单票接口失败")


def main() -> None:
    market = fetch_market_overview()
    if market.source == "示例数据":
        try:
            market = fetch_tencent_market_overview()
        except Exception as exc:  # noqa: BLE001
            print(f"skip tencent market fallback: {type(exc).__name__}")
    sectors = fetch_sector_rank()
    overseas = fetch_overseas_market()
    sector_data = add_sector_state(sectors.data)
    market_summary = summarize_market(market.data)
    stocks = fetch_public_holding_stocks(sector_data, market_summary["score"])

    write_cache_if_useful("market", market)
    write_cache_if_useful("sectors", FetchResult(sector_data, sectors.update_time, sectors.source, sectors.warning))
    write_cache_if_useful("overseas", overseas)
    write_cache_if_useful("stocks", stocks)

    print(f"updated live cache at {now_text()}")
    print(f"market source={market.source}, sectors source={sectors.source}, overseas source={overseas.source}")
    print(f"stocks={len(stocks.data)}")


if __name__ == "__main__":
    main()
