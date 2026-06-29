from __future__ import annotations

from .utils import clamp, safe_float


def calculate_market_score(market_data):
    up = safe_float(market_data.get("up_count"))
    down = safe_float(market_data.get("down_count"))
    amount_yi = safe_float(market_data.get("amount_yi"))
    limit_up = safe_float(market_data.get("limit_up_count"))
    limit_down = safe_float(market_data.get("limit_down_count"))
    index_avg = safe_float(market_data.get("index_avg_pct"))

    breadth = 50 if up + down == 0 else up / (up + down) * 100
    amount_score = clamp((amount_yi - 6000) / 6000 * 40 + 50)
    emotion_score = clamp(50 + (limit_up - limit_down * 2))
    index_score = clamp(50 + index_avg * 12)
    score = clamp(breadth * 0.35 + amount_score * 0.25 + emotion_score * 0.2 + index_score * 0.2)

    reasons = [
        f"上涨家数 {int(up)}、下跌家数 {int(down)}",
        f"两市成交额约 {amount_yi:.0f} 亿",
        f"主要指数平均涨跌幅 {index_avg:.2f}%",
        f"涨停 {int(limit_up)} 家、跌停 {int(limit_down)} 家",
    ]
    return {"score": round(score, 1), "reason": "；".join(reasons)}


def calculate_sector_score(sector_data):
    pct = safe_float(sector_data.get("pct_chg"))
    pct_5 = safe_float(sector_data.get("pct_chg_5d", pct))
    pct_10 = safe_float(sector_data.get("pct_chg_10d", pct_5))
    amount_ratio = safe_float(sector_data.get("amount_ratio", 1))
    limit_up = safe_float(sector_data.get("limit_up_count"))
    relative = safe_float(sector_data.get("relative_market_pct", pct))

    today_score = clamp(50 + pct * 10)
    five_score = clamp(50 + pct_5 * 6)
    ten_score = clamp(50 + pct_10 * 4)
    amount_score = clamp(50 + (amount_ratio - 1) * 50)
    limit_score = clamp(45 + limit_up * 8)
    relative_score = clamp(50 + relative * 10)

    score = (
        today_score * 0.25
        + five_score * 0.20
        + ten_score * 0.15
        + amount_score * 0.20
        + limit_score * 0.10
        + relative_score * 0.10
    )
    reason = f"今日涨跌幅 {pct:.2f}%，5日 {pct_5:.2f}%，成交额变化 {amount_ratio:.2f} 倍"
    return {"score": round(clamp(score), 1), "reason": reason}


def calculate_stock_trend_score(stock_data):
    pct_10 = safe_float(stock_data.get("pct_chg_10d"))
    price = safe_float(stock_data.get("price"))
    ma20 = safe_float(stock_data.get("ma20"), price)
    ma60 = safe_float(stock_data.get("ma60"), ma20)
    above_ma20 = price >= ma20
    ma_order = ma20 >= ma60
    score = 45 + pct_10 * 4 + (18 if above_ma20 else -12) + (12 if ma_order else -8)
    reason = f"近10日涨跌幅 {pct_10:.2f}%，{'站上' if above_ma20 else '跌破'}20日均线，20日均线{'高于' if ma_order else '低于'}60日均线"
    return {"score": round(clamp(score), 1), "reason": reason}


def calculate_volume_score(stock_data):
    ratio = safe_float(stock_data.get("volume_ratio"), 1)
    amount = safe_float(stock_data.get("amount_yi"))
    score = clamp(45 + (ratio - 1) * 35 + min(amount, 20))
    return {"score": round(score, 1), "reason": f"量比/成交额放大约 {ratio:.2f} 倍，成交额 {amount:.2f} 亿"}


def calculate_basic_score(stock_data):
    is_st = bool(stock_data.get("is_st", False))
    is_delist = bool(stock_data.get("is_delist", False))
    score = 20 if is_st or is_delist else 70
    reason = "存在 ST 或退市风险标识" if score < 60 else "未发现 ST 或退市风险标识"
    return {"score": score, "reason": reason}


def calculate_risk_score(stock_data):
    risk = 0
    items = []
    if stock_data.get("is_st", False):
        risk += 35
        items.append("ST 风险")
    if safe_float(stock_data.get("pct_chg_20d")) > 35:
        risk += 25
        items.append("短期涨幅偏大")
    if safe_float(stock_data.get("price")) < safe_float(stock_data.get("ma20"), 0):
        risk += 20
        items.append("跌破20日均线")
    if safe_float(stock_data.get("pct_chg")) < -5 and safe_float(stock_data.get("volume_ratio"), 1) > 1.5:
        risk += 20
        items.append("放量下跌")
    return {"score": round(clamp(risk), 1), "reason": "；".join(items) if items else "未触发主要技术风险"}


def calculate_final_stock_score(market_score, sector_score, stock_score, volume_score, basic_score, risk_score):
    score = (
        safe_float(market_score) * 0.25
        + safe_float(sector_score) * 0.30
        + safe_float(stock_score) * 0.25
        + safe_float(volume_score) * 0.10
        + safe_float(basic_score) * 0.10
        - safe_float(risk_score)
    )
    score = clamp(score)
    if score >= 85:
        label = "强候选，重点观察"
    elif score >= 70:
        label = "候选，等待买点"
    elif score >= 60:
        label = "观察，不急买"
    elif score >= 40:
        label = "偏弱，不买"
    else:
        label = "回避"
    return {"score": round(score, 1), "reason": label}
