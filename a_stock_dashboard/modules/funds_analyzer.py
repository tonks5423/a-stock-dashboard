from __future__ import annotations

import pandas as pd

from .utils import safe_float


def _market_liquidity(amount_yi: float) -> tuple[str, int]:
    if amount_yi >= 11000:
        return "增量资金活跃", 85
    if amount_yi >= 9000:
        return "资金面可交易", 72
    if amount_yi >= 7000:
        return "存量博弈", 55
    return "缩量谨慎", 38


def summarize_funds(market_data: dict, sectors: pd.DataFrame, stocks: pd.DataFrame) -> dict:
    amount_yi = safe_float(market_data.get("amount_yi"))
    amount_5d_avg = safe_float(market_data.get("amount_5d_avg_yi"), amount_yi)
    amount_20d_avg = safe_float(market_data.get("amount_20d_avg_yi"), amount_5d_avg)
    vs_5d_pct = 0 if amount_5d_avg == 0 else (amount_yi / amount_5d_avg - 1) * 100
    vs_20d_pct = 0 if amount_20d_avg == 0 else (amount_yi / amount_20d_avg - 1) * 100

    liquidity_state, base_score = _market_liquidity(amount_yi)
    if vs_5d_pct >= 12:
        flow_state = "明显放量"
        score = min(100, base_score + 12)
    elif vs_5d_pct >= 3:
        flow_state = "温和放量"
        score = min(100, base_score + 5)
    elif vs_5d_pct <= -12:
        flow_state = "明显缩量"
        score = max(0, base_score - 14)
    elif vs_5d_pct <= -3:
        flow_state = "温和缩量"
        score = max(0, base_score - 6)
    else:
        flow_state = "量能持平"
        score = base_score

    sector_frame = sectors.copy() if sectors is not None else pd.DataFrame()
    if not sector_frame.empty and "amount" in sector_frame:
        sector_frame["amount_yi"] = sector_frame["amount"].map(lambda value: safe_float(value) / 100000000)
        hot_money = sector_frame.sort_values(["amount_ratio", "amount_yi", "score"], ascending=False).head(3)
        top_sector_names = hot_money["sector_name"].astype(str).tolist()
    else:
        hot_money = pd.DataFrame()
        top_sector_names = []

    stock_frame = stocks.copy() if stocks is not None else pd.DataFrame()
    if not stock_frame.empty and {"amount_yi", "volume_ratio"}.issubset(stock_frame.columns):
        active_stocks = stock_frame.sort_values(["amount_yi", "volume_ratio", "final_score"], ascending=False).head(5)
    else:
        active_stocks = pd.DataFrame()

    if score >= 80:
        conclusion = "资金面支持进攻，但只追随放量主线，不追连续急拉。"
    elif score >= 60:
        conclusion = "资金面可以交易，适合等回踩承接或放量突破确认。"
    elif score >= 45:
        conclusion = "资金面偏存量博弈，仓位和买点都要保守。"
    else:
        conclusion = "资金面偏弱，优先处理持仓风险，不主动扩大仓位。"

    return {
        "score": round(score, 1),
        "liquidity_state": liquidity_state,
        "flow_state": flow_state,
        "amount_yi": amount_yi,
        "amount_5d_avg_yi": amount_5d_avg,
        "amount_20d_avg_yi": amount_20d_avg,
        "vs_5d_pct": round(vs_5d_pct, 2),
        "vs_20d_pct": round(vs_20d_pct, 2),
        "top_sector_names": top_sector_names,
        "hot_money_sectors": hot_money,
        "active_stocks": active_stocks,
        "conclusion": conclusion,
        "reason": f"两市成交额 {amount_yi:.0f} 亿，较5日均量 {vs_5d_pct:+.1f}%，较20日均量 {vs_20d_pct:+.1f}%。",
    }


def label_stock_money_flow(stock_data: dict) -> dict:
    pct_chg = safe_float(stock_data.get("pct_chg"))
    amount_yi = safe_float(stock_data.get("amount_yi"))
    volume_ratio = safe_float(stock_data.get("volume_ratio"), 1)
    turnover_rate = safe_float(stock_data.get("turnover_rate"))

    if pct_chg > 1 and volume_ratio >= 1.5:
        label = "放量上涨"
        action_hint = "资金配合上涨，强于缩量反弹；回踩不破时更值得观察。"
    elif pct_chg < -1 and volume_ratio >= 1.5:
        label = "放量下跌"
        action_hint = "资金放大但价格下跌，优先看风险，别急着补仓。"
    elif pct_chg > 0 and volume_ratio < 0.9:
        label = "缩量反弹"
        action_hint = "上涨缺少成交确认，适合观察，不适合追高。"
    elif pct_chg < 0 and volume_ratio < 0.9:
        label = "缩量回落"
        action_hint = "抛压不重但承接也弱，等待方向明确。"
    elif amount_yi >= 20 or turnover_rate >= 3:
        label = "资金活跃"
        action_hint = "交易活跃，盘中波动可能加大，按保护价执行。"
    else:
        label = "量能普通"
        action_hint = "资金信号不突出，更多参考板块和均线。"

    return {
        "money_flow_state": label,
        "amount_yi": amount_yi,
        "volume_ratio": volume_ratio,
        "turnover_rate": turnover_rate,
        "money_flow_hint": action_hint,
    }
