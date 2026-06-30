from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .score_engine import calculate_sector_score
from .utils import amount_yi, now_text

try:
    from config import LIVE_CACHE_DIR, PUBLIC_HOLDINGS_FILE, PUBLIC_MODE, USE_CACHED_DATA, USE_LIVE_DATA
except ImportError:
    LIVE_CACHE_DIR = Path("data/live_cache")
    PUBLIC_HOLDINGS_FILE = Path("data/public_holdings.csv")
    PUBLIC_MODE = False
    USE_CACHED_DATA = True
    USE_LIVE_DATA = False


@dataclass
class FetchResult:
    data: Any
    update_time: str
    source: str
    warning: str | None = None


def _live_data_warning(data_name: str, exc: Exception) -> str:
    return f"AKShare {data_name}接口暂不可用，已自动切换到示例数据。详情：{type(exc).__name__}"


def _cache_path(name: str) -> Path:
    return Path(LIVE_CACHE_DIR) / f"{name}.json"


def live_cache_status() -> str:
    names = ["market", "sectors", "overseas", "stocks"]
    existing = []
    for name in names:
        cached = read_fetch_cache(name)
        if cached is not None:
            existing.append(f"{name}:{cached.update_time}")
    if not existing:
        return "行情缓存：暂无，当前会回退示例数据"
    latest = max(item.split(":", 1)[1] for item in existing)
    return f"行情缓存：已生成，最近更新时间 {latest}"


def _serialize(value):
    if isinstance(value, pd.DataFrame):
        return {"__type__": "dataframe", "records": value.to_dict("records")}
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def _deserialize(value):
    if isinstance(value, dict) and value.get("__type__") == "dataframe":
        return pd.DataFrame(value.get("records", []))
    if isinstance(value, dict):
        return {key: _deserialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_deserialize(item) for item in value]
    return value


def read_fetch_cache(name: str) -> FetchResult | None:
    path = _cache_path(name)
    if not path.exists():
        return None
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        return FetchResult(
            data=_deserialize(payload.get("data")),
            update_time=payload.get("update_time", now_text()),
            source=payload.get("source", "定时真实缓存"),
            warning=payload.get("warning"),
        )
    except Exception:  # noqa: BLE001
        return None


def write_fetch_cache(name: str, result: FetchResult) -> None:
    import json

    Path(LIVE_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    payload = {
        "update_time": result.update_time,
        "source": result.source,
        "warning": result.warning,
        "data": _serialize(result.data),
    }
    _cache_path(name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _cached_or_sample(name: str, sample_data, update_time: str) -> FetchResult:
    if USE_CACHED_DATA:
        cached = read_fetch_cache(name)
        if cached is not None:
            cached.source = f"{cached.source}缓存"
            return cached
    return FetchResult(sample_data, update_time, "示例数据")


def _sample_indices() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"name": "上证指数", "code": "000001", "pct_chg": 0.78},
            {"name": "深成指", "code": "399001", "pct_chg": 1.06},
            {"name": "创业板指", "code": "399006", "pct_chg": 1.34},
            {"name": "科创50", "code": "000688", "pct_chg": 0.42},
            {"name": "沪深300", "code": "000300", "pct_chg": 0.63},
            {"name": "中证1000", "code": "000852", "pct_chg": 1.18},
        ]
    )


def _sample_market() -> dict:
    indices = _sample_indices()
    return {
        "indices": indices,
        "amount_yi": 9480,
        "amount_5d_avg_yi": 8720,
        "amount_20d_avg_yi": 8150,
        "up_count": 3270,
        "down_count": 1780,
        "limit_up_count": 62,
        "limit_down_count": 8,
        "index_avg_pct": float(indices["pct_chg"].mean()),
    }


def _sample_overseas_market() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"name": "纳斯达克指数", "symbol": "NASDAQ", "category": "美股", "value": 19680.2, "pct_chg": 0.95, "note": "科技股风险偏好"},
            {"name": "标普500指数", "symbol": "S&P 500", "category": "美股", "value": 5482.1, "pct_chg": 0.52, "note": "美股整体风险偏好"},
            {"name": "道琼斯指数", "symbol": "DJIA", "category": "美股", "value": 39280.4, "pct_chg": 0.18, "note": "传统蓝筹表现"},
            {"name": "罗素2000指数", "symbol": "RUT", "category": "美股", "value": 2078.6, "pct_chg": 0.30, "note": "美国小盘股风险偏好"},
            {"name": "费城半导体指数", "symbol": "SOX", "category": "美股科技", "value": 5580.4, "pct_chg": 1.85, "note": "半导体链条映射，影响A股芯片、算力、AI硬件"},
            {"name": "英伟达", "symbol": "NVDA", "category": "美股科技", "value": 126.8, "pct_chg": 2.10, "note": "AI算力链核心风向"},
            {"name": "特斯拉", "symbol": "TSLA", "category": "美股科技", "value": 202.4, "pct_chg": -0.65, "note": "新能源车和机器人情绪参考"},
            {"name": "苹果", "symbol": "AAPL", "category": "美股科技", "value": 214.1, "pct_chg": 0.42, "note": "消费电子链参考"},
            {"name": "VIX波动率指数", "symbol": "VIX", "category": "风险偏好", "value": 13.6, "pct_chg": -3.20, "note": "负数通常代表恐慌下降、风险偏好改善"},
            {"name": "富时中国A50期货", "symbol": "A50", "category": "A股映射", "value": 12680.0, "pct_chg": 0.35, "note": "A股盘前情绪参考"},
            {"name": "恒生指数", "symbol": "HSI", "category": "港股", "value": 18420.6, "pct_chg": 0.72, "note": "港股整体表现"},
            {"name": "恒生科技指数", "symbol": "HSTECH", "category": "港股", "value": 3920.8, "pct_chg": 1.10, "note": "中概/科技映射"},
            {"name": "纳斯达克中国金龙指数", "symbol": "HXC", "category": "中概股", "value": 6680.5, "pct_chg": 1.25, "note": "中概股情绪"},
            {"name": "阿里巴巴", "symbol": "BABA", "category": "中概股", "value": 78.2, "pct_chg": 1.05, "note": "互联网平台和港股科技参考"},
            {"name": "拼多多", "symbol": "PDD", "category": "中概股", "value": 142.3, "pct_chg": 0.88, "note": "中概消费和平台经济参考"},
            {"name": "离岸人民币 USD/CNH", "symbol": "USD/CNH", "category": "汇率", "value": 7.245, "pct_chg": -0.12, "note": "负数通常代表人民币升值"},
            {"name": "美元指数", "symbol": "DXY", "category": "汇率", "value": 104.2, "pct_chg": -0.18, "note": "美元走弱通常利于风险资产"},
            {"name": "美债10年收益率", "symbol": "US10Y", "category": "利率", "value": 4.23, "pct_chg": -0.05, "note": "利率下行通常缓和估值压力"},
            {"name": "黄金", "symbol": "XAU", "category": "商品", "value": 2368.0, "pct_chg": 0.28, "note": "避险和通胀预期"},
            {"name": "原油", "symbol": "WTI", "category": "商品", "value": 81.2, "pct_chg": -0.40, "note": "通胀与周期情绪"},
            {"name": "铜", "symbol": "COPPER", "category": "商品", "value": 4.58, "pct_chg": 0.65, "note": "全球制造业预期"},
        ]
    )


def fetch_overseas_market() -> FetchResult:
    update_time = now_text()
    if not USE_LIVE_DATA:
        return _cached_or_sample("overseas", _sample_overseas_market(), update_time)
    try:
        # AKShare global interfaces are not uniform across assets. Keep the live
        # path conservative so page rendering never depends on one fragile source.
        import akshare as ak

        global_index = ak.index_investing_global(country="美国", index_name="美国标普500指数", period="每日", start_date="20240101", end_date="20261231")
        data = _sample_overseas_market()
        if not global_index.empty and "涨跌幅" in global_index.columns:
            data.loc[data["symbol"].eq("S&P 500"), "pct_chg"] = float(str(global_index["涨跌幅"].iloc[-1]).replace("%", ""))
        return FetchResult(data, update_time, "AKShare + 示例补全")
    except Exception as exc:  # noqa: BLE001
        if USE_CACHED_DATA:
            cached = read_fetch_cache("overseas")
            if cached is not None:
                cached.warning = _live_data_warning("外围市场", exc)
                return cached
        return FetchResult(_sample_overseas_market(), update_time, "示例数据", _live_data_warning("外围市场", exc))


def fetch_market_overview() -> FetchResult:
    update_time = now_text()
    if not USE_LIVE_DATA:
        return _cached_or_sample("market", _sample_market(), update_time)
    try:
        import akshare as ak

        spot = ak.stock_zh_a_spot_em()
        pct_col = "涨跌幅"
        amount_col = "成交额"
        name_col = "名称"
        up_count = int((spot[pct_col] > 0).sum())
        down_count = int((spot[pct_col] < 0).sum())
        limit_up_count = int((spot[pct_col] >= 9.8).sum())
        limit_down_count = int((spot[pct_col] <= -9.8).sum())
        total_amount_yi = amount_yi(spot[amount_col].sum())

        index_codes = {
            "上证指数": "000001",
            "深成指": "399001",
            "创业板指": "399006",
            "科创50": "000688",
            "沪深300": "000300",
            "中证1000": "000852",
        }
        indices = []
        for name, code in index_codes.items():
            row = spot.loc[spot[name_col].eq(name)]
            pct = float(row[pct_col].iloc[0]) if not row.empty else np.nan
            indices.append({"name": name, "code": code, "pct_chg": pct})
        index_df = pd.DataFrame(indices).fillna(0)
        return FetchResult(
            {
                "indices": index_df,
                "amount_yi": total_amount_yi,
                "amount_5d_avg_yi": 9000,
                "amount_20d_avg_yi": 8500,
                "up_count": up_count,
                "down_count": down_count,
                "limit_up_count": limit_up_count,
                "limit_down_count": limit_down_count,
                "index_avg_pct": float(index_df["pct_chg"].mean()),
            },
            update_time,
            "AKShare",
        )
    except Exception as exc:  # noqa: BLE001
        if USE_CACHED_DATA:
            cached = read_fetch_cache("market")
            if cached is not None:
                cached.warning = _live_data_warning("实时行情", exc)
                return cached
        return FetchResult(_sample_market(), update_time, "示例数据", _live_data_warning("实时行情", exc))


def fetch_sector_rank() -> FetchResult:
    update_time = now_text()
    if not USE_LIVE_DATA:
        return _cached_or_sample("sectors", _sample_sectors(), update_time)
    try:
        import akshare as ak

        frames = []
        for sector_type, func in {
            "行业": ak.stock_board_industry_name_em,
            "概念": ak.stock_board_concept_name_em,
        }.items():
            raw = func()
            frame = pd.DataFrame(
                {
                    "sector_name": raw["板块名称"],
                    "sector_type": sector_type,
                    "pct_chg": raw["涨跌幅"].astype(float),
                    "amount": raw["成交额"].astype(float),
                    "amount_ratio": 1 + raw["涨跌幅"].astype(float).abs() / 12,
                    "up_count": raw.get("上涨家数", 0),
                    "down_count": raw.get("下跌家数", 0),
                    "limit_up_count": 0,
                    "limit_down_count": 0,
                    "leading_stock": raw.get("领涨股票", ""),
                }
            )
            frame["pct_chg_5d"] = frame["pct_chg"] * 1.8
            frame["pct_chg_10d"] = frame["pct_chg"] * 2.5
            frame["relative_market_pct"] = frame["pct_chg"] - frame["pct_chg"].mean()
            frames.append(frame)
        data = pd.concat(frames, ignore_index=True)
        return FetchResult(_score_sectors(data), update_time, "AKShare")
    except Exception as exc:  # noqa: BLE001
        if USE_CACHED_DATA:
            cached = read_fetch_cache("sectors")
            if cached is not None:
                cached.warning = _live_data_warning("板块", exc)
                return cached
        return FetchResult(_sample_sectors(), update_time, "示例数据", _live_data_warning("板块", exc))


def _sample_sectors() -> pd.DataFrame:
    data = pd.DataFrame(
        [
            ["半导体", "概念", 3.8, 1880e8, 1.55, 82, 21, 9, 0, "中芯国际"],
            ["机器人", "概念", 2.9, 940e8, 1.42, 67, 28, 6, 0, "汇川技术"],
            ["银行", "行业", 0.9, 760e8, 1.04, 29, 13, 0, 0, "平安银行"],
            ["白酒", "行业", -0.6, 520e8, 0.88, 8, 18, 0, 0, "贵州茅台"],
            ["新能源", "概念", 1.7, 1200e8, 1.20, 54, 36, 3, 0, "宁德时代"],
        ],
        columns=[
            "sector_name",
            "sector_type",
            "pct_chg",
            "amount",
            "amount_ratio",
            "up_count",
            "down_count",
            "limit_up_count",
            "limit_down_count",
            "leading_stock",
        ],
    )
    data["pct_chg_5d"] = [7.8, 6.3, 2.1, -1.8, 4.6]
    data["pct_chg_10d"] = [12.5, 9.2, 3.4, -2.5, 6.8]
    data["relative_market_pct"] = data["pct_chg"] - 0.8
    return _score_sectors(data)


def _score_sectors(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    scores = data.apply(lambda row: calculate_sector_score(row.to_dict()), axis=1)
    data["score"] = [item["score"] for item in scores]
    data["score_reason"] = [item["reason"] for item in scores]
    return data.sort_values("score", ascending=False).reset_index(drop=True)


def load_holdings(path) -> pd.DataFrame:
    if PUBLIC_MODE:
        try:
            from config import PUBLIC_HOLDINGS_FILE

            return pd.read_csv(PUBLIC_HOLDINGS_FILE, dtype={"stock_code": str})
        except FileNotFoundError:
            return _sample_public_holdings()
    try:
        return pd.read_csv(path, dtype={"stock_code": str})
    except FileNotFoundError:
        return pd.DataFrame(columns=["stock_code", "stock_name", "buy_price", "shares", "buy_date", "stop_loss_price", "target_price", "note"])


def _sample_public_holdings() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "stock_code": "688981",
                "stock_name": "中芯国际",
                "buy_price": 61.2,
                "shares": 1000,
                "buy_date": "2026-06-20",
                "stop_loss_price": 57.8,
                "target_price": 72.0,
                "current_price": 66.8,
                "current_market_value": 66800,
                "note": "公开展示",
            },
            {
                "stock_code": "510300",
                "stock_name": "沪深300ETF",
                "buy_price": 3.82,
                "shares": 10000,
                "buy_date": "2026-06-10",
                "stop_loss_price": 3.58,
                "target_price": 4.18,
                "current_price": 3.95,
                "current_market_value": 39500,
                "note": "公开展示",
            },
        ]
    )


def get_sample_stocks(sectors: pd.DataFrame) -> pd.DataFrame:
    if USE_CACHED_DATA:
        cached = read_fetch_cache("stocks")
        if cached is not None and isinstance(cached.data, pd.DataFrame) and not cached.data.empty:
            return cached.data

    sector_lookup = dict(zip(sectors["sector_name"], sectors["score"]))
    return pd.DataFrame(
        [
            {"stock_code": "300750", "stock_name": "宁德时代", "industry": "新能源", "concept": "新能源", "price": 208.5, "pct_chg": 2.4, "pct_chg_5d": 5.8, "pct_chg_10d": 8.6, "pct_chg_20d": 14.2, "amount_yi": 82.4, "turnover_rate": 1.9, "volume_ratio": 1.7, "ma5": 202, "ma10": 198, "ma20": 190, "ma60": 176, "sector_score": sector_lookup.get("新能源", 70), "is_st": False, "is_delist": False},
            {"stock_code": "000001", "stock_name": "平安银行", "industry": "银行", "concept": "金融", "price": 11.12, "pct_chg": 0.8, "pct_chg_5d": 2.2, "pct_chg_10d": 3.8, "pct_chg_20d": 5.1, "amount_yi": 34.1, "turnover_rate": 0.7, "volume_ratio": 1.1, "ma5": 10.95, "ma10": 10.82, "ma20": 10.55, "ma60": 10.10, "sector_score": sector_lookup.get("银行", 60), "is_st": False, "is_delist": False},
            {"stock_code": "600519", "stock_name": "贵州茅台", "industry": "白酒", "concept": "消费", "price": 1488.0, "pct_chg": -1.2, "pct_chg_5d": -2.0, "pct_chg_10d": -3.5, "pct_chg_20d": -4.8, "amount_yi": 42.5, "turnover_rate": 0.3, "volume_ratio": 1.4, "ma5": 1510, "ma10": 1522, "ma20": 1530, "ma60": 1560, "sector_score": sector_lookup.get("白酒", 45), "is_st": False, "is_delist": False},
            {"stock_code": "688981", "stock_name": "中芯国际", "industry": "半导体", "concept": "半导体", "price": 66.8, "pct_chg": 4.2, "pct_chg_5d": 9.1, "pct_chg_10d": 13.5, "pct_chg_20d": 28.0, "amount_yi": 96.0, "turnover_rate": 3.6, "volume_ratio": 2.0, "ma5": 62, "ma10": 59, "ma20": 54, "ma60": 48, "sector_score": sector_lookup.get("半导体", 85), "is_st": False, "is_delist": False},
            {"stock_code": "601236", "stock_name": "红塔证券", "industry": "证券", "concept": "金融", "price": 6.83, "pct_chg": -1.15, "pct_chg_5d": -4.6, "pct_chg_10d": -7.8, "pct_chg_20d": -12.4, "amount_yi": 3.8, "turnover_rate": 2.1, "volume_ratio": 1.62, "ma5": 7.05, "ma10": 7.22, "ma20": 7.68, "ma60": 8.15, "sector_score": sector_lookup.get("证券", 58), "is_st": False, "is_delist": False},
            {"stock_code": "510330", "stock_name": "华夏300", "industry": "沪深300ETF", "concept": "宽基ETF", "price": 5.176, "pct_chg": 0.42, "pct_chg_5d": 1.6, "pct_chg_10d": 2.4, "pct_chg_20d": 3.8, "amount_yi": 7.2, "turnover_rate": 0.8, "volume_ratio": 1.08, "ma5": 5.12, "ma10": 5.08, "ma20": 4.98, "ma60": 4.72, "sector_score": 66, "is_st": False, "is_delist": False},
            {"stock_code": "518800", "stock_name": "黄金基金", "industry": "黄金ETF", "concept": "黄金", "price": 8.856, "pct_chg": -0.28, "pct_chg_5d": -1.1, "pct_chg_10d": 0.6, "pct_chg_20d": 4.2, "amount_yi": 5.6, "turnover_rate": 1.2, "volume_ratio": 0.86, "ma5": 8.91, "ma10": 8.84, "ma20": 8.62, "ma60": 8.18, "sector_score": 62, "is_st": False, "is_delist": False},
            {"stock_code": "400219", "stock_name": "碳元5", "industry": "退市整理", "concept": "高风险", "price": 0.37, "pct_chg": 0.0, "pct_chg_5d": -8.5, "pct_chg_10d": -16.2, "pct_chg_20d": -28.0, "amount_yi": 0.04, "turnover_rate": 0.3, "volume_ratio": 0.52, "ma5": 0.39, "ma10": 0.42, "ma20": 0.49, "ma60": 0.66, "sector_score": 20, "is_st": False, "is_delist": True},
        ]
    )
