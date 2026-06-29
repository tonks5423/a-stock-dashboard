from __future__ import annotations

from .utils import safe_float


def analyze_stock_risk(stock_data, sector_data, market_data, holding_data=None):
    risk_items = []
    price = safe_float(stock_data.get("price"))
    ma10 = safe_float(stock_data.get("ma10"), price)
    ma20 = safe_float(stock_data.get("ma20"), price)
    pct = safe_float(stock_data.get("pct_chg"))
    pct20 = safe_float(stock_data.get("pct_chg_20d"))
    volume_ratio = safe_float(stock_data.get("volume_ratio"), 1)
    sector_score = safe_float(sector_data.get("score", stock_data.get("sector_score", 50)))

    if price < ma10:
        risk_items.append("股价跌破10日均线")
    if price < ma20:
        risk_items.append("股价跌破20日均线")
    if pct < -3 and volume_ratio > 1.5:
        risk_items.append("成交额放大但股价下跌")
    if sector_score < 50:
        risk_items.append("所属板块跌出强势区")
    if pct20 > 35:
        risk_items.append("短期涨幅过大，存在高位追涨风险")
    if stock_data.get("is_st", False) or stock_data.get("is_delist", False):
        risk_items.append("存在 ST 或退市风险标识")
    if holding_data is not None:
        stop_loss = safe_float(holding_data.get("stop_loss_price"))
        if stop_loss and price <= stop_loss * 1.03:
            risk_items.append("当前价格接近或跌破止损价")
    if safe_float(market_data.get("down_count")) > safe_float(market_data.get("up_count")) * 1.4:
        risk_items.append("两市下跌家数明显多于上涨家数")
    if safe_float(market_data.get("limit_down_count")) >= 30:
        risk_items.append("跌停家数明显增加")

    count = len(risk_items)
    if count >= 5:
        level = "极高风险"
    elif count >= 3:
        level = "高风险"
    elif count >= 1:
        level = "中风险"
    else:
        level = "低风险"
    return {"risk_level": level, "risk_items": risk_items or ["未触发主要风险项"]}
