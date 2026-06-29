from __future__ import annotations

from .score_engine import calculate_market_score


def market_state(score: float) -> str:
    if score >= 80:
        return "强势"
    if score >= 60:
        return "可交易"
    if score >= 40:
        return "震荡"
    return "弱势"


def summarize_market(market_data: dict) -> dict:
    result = calculate_market_score(market_data)
    score = result["score"]
    state = market_state(score)
    if score >= 80:
        action = "可以积极寻找机会，但仍需避免高位追涨。"
    elif score >= 60:
        action = "市场具备交易条件，适合轻仓或中仓关注强板块。"
    elif score >= 40:
        action = "市场分歧较大，优先只看强板块龙头。"
    else:
        action = "市场偏弱，建议少交易并控制仓位。"
    conclusion = f"当前市场温度 {score:.1f} 分，属于{state}市场。{action}"
    return {"score": score, "state": state, "reason": result["reason"], "conclusion": conclusion}
