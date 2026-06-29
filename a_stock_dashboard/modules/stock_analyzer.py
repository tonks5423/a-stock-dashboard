from __future__ import annotations

from .score_engine import (
    calculate_basic_score,
    calculate_final_stock_score,
    calculate_risk_score,
    calculate_stock_trend_score,
    calculate_volume_score,
)


def score_stocks(stocks, market_score: float):
    rows = []
    for _, row in stocks.iterrows():
        stock = row.to_dict()
        trend = calculate_stock_trend_score(stock)
        volume = calculate_volume_score(stock)
        basic = calculate_basic_score(stock)
        risk = calculate_risk_score(stock)
        final = calculate_final_stock_score(
            market_score,
            stock.get("sector_score", 50),
            trend["score"],
            volume["score"],
            basic["score"],
            risk["score"],
        )
        stock.update(
            {
                "trend_score": trend["score"],
                "volume_score": volume["score"],
                "basic_score": basic["score"],
                "risk_score": risk["score"],
                "final_score": final["score"],
                "score_label": final["reason"],
                "score_reason": "；".join([trend["reason"], volume["reason"], basic["reason"], risk["reason"]]),
                "above_ma5": stock["price"] >= stock["ma5"],
                "above_ma10": stock["price"] >= stock["ma10"],
                "above_ma20": stock["price"] >= stock["ma20"],
                "above_ma60": stock["price"] >= stock["ma60"],
                "new_high_20d": stock.get("pct_chg_20d", 0) > 12,
                "new_high_60d": stock.get("pct_chg_20d", 0) > 25,
                "dist_limit_up_pct": max(0, 10 - stock.get("pct_chg", 0)),
                "dist_limit_down_pct": max(0, stock.get("pct_chg", 0) + 10),
            }
        )
        rows.append(stock)
    return stocks.__class__(rows).sort_values("final_score", ascending=False).reset_index(drop=True)


def screen_candidates(scored_stocks):
    data = scored_stocks.copy()
    mask = (
        (~data["is_st"])
        & (~data["is_delist"])
        & (data["amount_yi"] > 1)
        & (data["price"] > data["ma20"])
        & (data["ma20"] > data["ma60"])
        & (data["volume_ratio"] > 1.5)
        & (data["sector_score"] > 70)
        & (data["risk_score"] < 30)
    )
    return data.loc[mask].sort_values("final_score", ascending=False).reset_index(drop=True)
