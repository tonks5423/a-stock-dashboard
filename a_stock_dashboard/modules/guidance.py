from __future__ import annotations

import pandas as pd

from .utils import now_text, safe_float


def generate_operation_guidance(
    market_summary: dict,
    overseas_summary: dict,
    sectors: pd.DataFrame,
    candidates: pd.DataFrame,
    holding_reports: list[dict],
    risk_rows: list[dict],
) -> dict:
    market_score = safe_float(market_summary.get("score"))
    overseas_sentiment = overseas_summary.get("sentiment", "中性")
    top_sectors = sectors.head(3)["sector_name"].tolist() if not sectors.empty else []
    strong_candidates = candidates.head(3)["stock_name"].tolist() if not candidates.empty else []

    lines = []
    if market_score >= 80:
        lines.append("市场温度处于强势区，可积极寻找机会，但不宜追高连续大涨个股。")
    elif market_score >= 60:
        lines.append("市场温度处于可交易区，优先轻仓或中仓关注强板块里的高评分个股。")
    elif market_score >= 40:
        lines.append("市场处于震荡区，优先观察，不宜扩大仓位，只看最强板块龙头。")
    else:
        lines.append("市场处于弱势区，重点是控制回撤，减少新开仓和高波动追涨。")

    if overseas_sentiment == "偏强":
        lines.append(f"外围情绪偏强，{overseas_summary.get('premarket_action', '盘前情绪有支撑，但仍需要以 A 股开盘后的成交和板块承接为准。')}")
    elif overseas_sentiment == "偏弱":
        lines.append(f"外围情绪偏弱，{overseas_summary.get('premarket_action', '盘前先降低预期，观察 A50、汇率和开盘后指数承接。')}")
    else:
        lines.append(f"外围情绪中性，{overseas_summary.get('premarket_action', '今天更应以盘中板块强弱和市场广度作为判断依据。')}")

    if top_sectors:
        lines.append(f"板块观察顺序：{'、'.join(top_sectors)}。优先看强板块内趋势和量能同步的个股。")
    else:
        lines.append("当前没有明确强板块，暂时不要为了交易而交易。")

    if strong_candidates:
        lines.append(f"候选观察：{'、'.join(strong_candidates)}。只作为观察池，等待低风险买点，不作为直接买入指令。")
    else:
        lines.append("当前严格筛选下没有强候选，先复盘板块和持仓，不急于新增标的。")

    risky_holdings = [item for item in holding_reports if item.get("risk_level") in {"高风险", "极高风险"} or item.get("status") in {"警惕", "减仓", "止损"}]
    if risky_holdings:
        names = "、".join(item.get("stock_name", "") for item in risky_holdings[:3])
        lines.append(f"持仓重点检查：{names}。关注是否接近止损、跌破均线或持续弱于所属板块。")
    elif holding_reports:
        lines.append("持仓暂无高风险信号，继续观察是否维持在关键均线和强板块内。")
    else:
        lines.append("当前未维护持仓，建议先在 holdings.csv 中补充持仓后再做诊断。")

    if risk_rows:
        lines.append(f"风险提醒共有 {len(risk_rows)} 条，先处理风险分较高或评分偏低的标的。")
    else:
        lines.append("当前未触发主要风险提醒，但仍需控制单票仓位和追高冲动。")

    return {
        "generated_at": now_text(),
        "title": "当前操作指导",
        "lines": lines,
        "disclaimer": "以上为数据面板生成的辅助分析，不构成投资建议，也不是买卖指令。",
    }
