from __future__ import annotations

from .funds_analyzer import label_stock_money_flow
from .risk_analyzer import analyze_stock_risk
from .utils import safe_float


def stock_data_from_holding(holding):
    price = safe_float(holding.get("current_price"), safe_float(holding.get("buy_price")))
    return {
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
        "trend_score": 50,
        "final_score": 50,
        "is_st": False,
        "is_delist": False,
    }


def analyze_holding(holding, stock_data, sector_data, market_data):
    price = safe_float(holding.get("current_price"), safe_float(stock_data.get("price")))
    buy_price = safe_float(holding.get("buy_price"))
    shares = safe_float(holding.get("shares"))
    market_value = safe_float(holding.get("current_market_value"), price * shares)
    profit = market_value - buy_price * shares if market_value else (price - buy_price) * shares
    profit_pct = 0 if buy_price == 0 else (price - buy_price) / buy_price * 100
    sector_score = safe_float(sector_data.get("score", stock_data.get("sector_score", 50)))
    stock_strength = safe_float(stock_data.get("final_score", stock_data.get("trend_score", 50)))
    ma10 = safe_float(stock_data.get("ma10"), price)
    ma20 = safe_float(stock_data.get("ma20"), price)
    stop_loss = safe_float(holding.get("stop_loss_price"))
    target = safe_float(holding.get("target_price"))

    if stop_loss and price <= stop_loss:
        status = "止损"
        suggestion = "警惕止损条件"
        reason = "当前价格已经触及或跌破用户设置的止损价。"
    elif price < ma20 and stock_data.get("volume_ratio", 1) > 1.4:
        status = "减仓"
        suggestion = "谨慎降低风险暴露"
        reason = "股价跌破20日均线，且成交量明显放大。"
    elif price < ma10:
        status = "警惕"
        suggestion = "暂不建议加仓"
        reason = "股价跌破10日均线，需要观察能否重新转强。"
    elif price >= ma20 and sector_score >= 70 and stock_strength >= 70:
        status = "强势持有"
        suggestion = "继续观察持有条件"
        reason = "股价仍在20日均线上方，所属板块和个股评分较高。"
    elif sector_score >= 70 and price >= ma10:
        status = "可加仓观察"
        suggestion = "等待低风险买点"
        reason = "所属板块仍强，股价保持在短期均线上方。"
    else:
        status = "换股风险" if sector_score >= 70 else "警惕"
        suggestion = "观察是否弱于所属板块"
        reason = "个股表现不够突出，需关注是否持续弱于板块。"

    risk = analyze_stock_risk(stock_data, sector_data, market_data, holding)
    money_flow = label_stock_money_flow(stock_data)
    return {
        "stock_code": holding.get("stock_code"),
        "stock_name": holding.get("stock_name", stock_data.get("stock_name")),
        "buy_price": buy_price,
        "price": price,
        "shares": shares,
        "market_value": market_value,
        "profit": round(profit, 2),
        "profit_pct": round(profit_pct, 2),
        "stop_loss_price": stop_loss,
        "target_price": target,
        "dist_stop_loss_pct": round((price - stop_loss) / stop_loss * 100, 2) if stop_loss else None,
        "dist_target_pct": round((target - price) / price * 100, 2) if target and price else None,
        "sector": stock_data.get("industry") or stock_data.get("concept"),
        "sector_score": sector_score,
        "stock_score": stock_strength,
        "status": status,
        "suggestion": suggestion,
        "reason": reason,
        "risk_level": risk["risk_level"],
        "risk_items": "；".join(risk["risk_items"]),
        "money_flow_state": money_flow["money_flow_state"],
        "amount_yi": money_flow["amount_yi"],
        "volume_ratio": money_flow["volume_ratio"],
        "turnover_rate": money_flow["turnover_rate"],
        "money_flow_hint": money_flow["money_flow_hint"],
    }
