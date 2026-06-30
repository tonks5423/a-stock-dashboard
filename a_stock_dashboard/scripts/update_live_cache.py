from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd


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
        import akshare as ak

        spot = ak.stock_zh_a_spot_em()
    except Exception as exc:  # noqa: BLE001
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
    return FetchResult(stocks, now_text(), "AKShare")


def write_cache_if_useful(name: str, result: FetchResult) -> None:
    if result.source in {"示例数据", "公开持仓兜底"}:
        print(f"skip {name}: source={result.source}, keep previous cache")
        return
    write_fetch_cache(name, result)


def main() -> None:
    market = fetch_market_overview()
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
