from __future__ import annotations

from .utils import safe_float


def _score_to_label(score: float) -> str:
    if score >= 62:
        return "偏强"
    if score <= 42:
        return "偏弱"
    return "中性"


def analyze_overseas_sentiment(overseas_data):
    lookup = {row["symbol"]: row for _, row in overseas_data.iterrows()}

    score = 50
    reasons = []

    nasdaq = safe_float(lookup.get("NASDAQ", {}).get("pct_chg"))
    sp500 = safe_float(lookup.get("S&P 500", {}).get("pct_chg"))
    rut = safe_float(lookup.get("RUT", {}).get("pct_chg"))
    sox = safe_float(lookup.get("SOX", {}).get("pct_chg"))
    nvda = safe_float(lookup.get("NVDA", {}).get("pct_chg"))
    tsla = safe_float(lookup.get("TSLA", {}).get("pct_chg"))
    aapl = safe_float(lookup.get("AAPL", {}).get("pct_chg"))
    vix = safe_float(lookup.get("VIX", {}).get("pct_chg"))
    a50 = safe_float(lookup.get("A50", {}).get("pct_chg"))
    hstech = safe_float(lookup.get("HSTECH", {}).get("pct_chg"))
    hxc = safe_float(lookup.get("HXC", {}).get("pct_chg"))
    baba = safe_float(lookup.get("BABA", {}).get("pct_chg"))
    pdd = safe_float(lookup.get("PDD", {}).get("pct_chg"))
    usdcnh = safe_float(lookup.get("USD/CNH", {}).get("pct_chg"))
    dxy = safe_float(lookup.get("DXY", {}).get("pct_chg"))
    us10y = safe_float(lookup.get("US10Y", {}).get("pct_chg"))
    copper = safe_float(lookup.get("COPPER", {}).get("pct_chg"))

    us_tech_score = 50 + nasdaq * 8 + sox * 7 + nvda * 4 + tsla * 2 + aapl * 2
    a_share_map_score = 50 + a50 * 16 + hstech * 7 + hxc * 7 + baba * 2 + pdd * 2
    fx_rate_score = 50 + (-usdcnh) * 12 + (-dxy) * 5 + (-us10y) * 5
    risk_appetite_score = 50 + sp500 * 5 + rut * 4 + (-vix) * 3 + copper * 2

    dimensions = {
        "美股科技": round(max(0, min(100, us_tech_score)), 1),
        "A股映射": round(max(0, min(100, a_share_map_score)), 1),
        "汇率利率": round(max(0, min(100, fx_rate_score)), 1),
        "风险偏好": round(max(0, min(100, risk_appetite_score)), 1),
    }

    score = (
        dimensions["美股科技"] * 0.28
        + dimensions["A股映射"] * 0.34
        + dimensions["汇率利率"] * 0.20
        + dimensions["风险偏好"] * 0.18
    )

    if nasdaq > 0 and a50 > 0:
        reasons.append("纳指和 A50 同时上涨")
    if sox > 1:
        reasons.append("费城半导体明显走强，利好芯片、算力、AI硬件情绪")
    if vix < -2:
        reasons.append("VIX回落，隔夜风险偏好改善")
    if hstech > 0 or hxc > 0:
        reasons.append("港股科技或中概股表现偏强")
    if usdcnh < 0:
        reasons.append("离岸人民币相对走强")
    if dxy > 0.5 or us10y > 0.08:
        reasons.append("美元或美债收益率上行带来压力")
    if sox > 1 and a50 <= 0:
        reasons.append("美股科技强但 A50 未跟随，需防外强内弱")
    if nasdaq < -1 or a50 < -0.8:
        reasons.append("美股科技或 A50 明显走弱")

    score = max(0, min(100, round(score, 1)))
    sentiment = _score_to_label(score)

    if sentiment == "偏强" and a50 > 0 and usdcnh <= 0:
        opening_bias = "高开或偏强开盘概率较高"
        premarket_action = "若明显高开，先看前15到30分钟承接和成交额，不建议无脑追高；若强板块放量承接，再从板块龙头或高评分候选里观察低风险机会。"
    elif sentiment == "偏强":
        opening_bias = "情绪偏暖但需要 A 股自身确认"
        premarket_action = "开盘先看 A50、人民币和强板块是否同步；若只有美股强而 A股映射弱，优先等回踩确认。"
    elif sentiment == "偏弱":
        opening_bias = "低开或弱开概率上升"
        premarket_action = "不要急着补仓，先看低开后是否放量修复；若跌停家数或下跌家数快速扩大，优先降低风险暴露。"
    else:
        opening_bias = "开盘方向不确定"
        premarket_action = "把隔夜美股只当背景，重点等 A 股开盘后的成交额、上涨家数和主线板块确认。"

    conclusion = f"外围情绪：{sentiment}。"
    if reasons:
        conclusion += "参考因素：" + "；".join(reasons) + "。"
    conclusion += f"{opening_bias}。外围市场只作为盘前情绪参考，不作为单独买入依据。"
    return {
        "score": score,
        "sentiment": sentiment,
        "reason": "；".join(reasons) or "主要外围指标分化不明显",
        "conclusion": conclusion,
        "dimensions": dimensions,
        "opening_bias": opening_bias,
        "premarket_action": premarket_action,
    }
