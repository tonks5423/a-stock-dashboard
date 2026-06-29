from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .utils import now_text, safe_float


DEFAULT_PROFILE = {
    "style": "波段交易",
    "risk_tolerance": "中等",
    "max_total_position_pct": 60,
    "max_single_position_pct": 15,
    "prefer_etf": True,
    "allow_intraday_chase": False,
    "review_time": "盘前、10:00、14:30、收盘后",
}


def load_trading_profile(path: Path | str | None) -> dict:
    if not path:
        return DEFAULT_PROFILE.copy()
    file_path = Path(path)
    if not file_path.exists():
        return DEFAULT_PROFILE.copy()
    try:
        loaded = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_PROFILE.copy()
    profile = DEFAULT_PROFILE.copy()
    profile.update({key: value for key, value in loaded.items() if value is not None})
    return profile


def _overseas_is_weak(summary: dict) -> bool:
    return summary.get("sentiment") == "偏弱" or safe_float(summary.get("score")) < 45


def _position_band(market_score: float, overseas_summary: dict, risk_count: int, profile: dict) -> tuple[str, str]:
    max_total = int(safe_float(profile.get("max_total_position_pct"), 60))
    max_single = int(safe_float(profile.get("max_single_position_pct"), 15))
    overseas_weak = _overseas_is_weak(overseas_summary)

    if market_score >= 80 and not overseas_weak and risk_count <= 3:
        return "积极寻找机会", f"建议总仓位 {min(60, max_total)}%-{min(80, max_total)}%，单一标的不超过 {max_single}%"
    if market_score >= 60 and not overseas_weak:
        return "可交易但控制节奏", f"建议总仓位 30%-{min(60, max_total)}%，单一标的不超过 {min(max_single, 15)}%"
    if market_score >= 40:
        return "轻仓观察为主", f"建议总仓位 0%-{min(30, max_total)}%，单一标的不超过 {min(max_single, 10)}%"
    return "只处理持仓，暂不主动开新仓", f"建议总仓位 0%-{min(20, max_total)}%，单一标的不超过 {min(max_single, 8)}%"


def _top_names(frame: pd.DataFrame, name_col: str, count: int = 3) -> list[str]:
    if frame is None or frame.empty or name_col not in frame:
        return []
    return [str(name) for name in frame.head(count)[name_col].tolist() if str(name)]


def _opening_scenarios(market_score: float, overseas_summary: dict, sectors: pd.DataFrame) -> list[dict]:
    top_sectors = "、".join(_top_names(sectors, "sector_name", 3)) or "最先放量走强的板块"
    overseas_action = overseas_summary.get("premarket_action", "以开盘后成交和板块承接为准。")
    return [
        {
            "scenario": "高开剧本",
            "condition": "指数高开且 10:00 前成交放大，强板块没有冲高回落。",
            "action": f"只看 {top_sectors} 的回踩承接，不追连续急拉；若外围偏弱，高开更要等二次确认。",
            "watch": overseas_action,
        },
        {
            "scenario": "平开剧本",
            "condition": "指数小幅波动，涨跌家数接近，量能未明显萎缩。",
            "action": "先观察 30-60 分钟，等板块强弱排序稳定后再决定是否小仓试错。",
            "watch": "优先看上涨家数、成交额、强板块是否持续在前排。",
        },
        {
            "scenario": "低开剧本",
            "condition": "指数低开，A50、人民币或科技映射继续走弱。",
            "action": "先处理弱持仓和破位风险，不急着抄底；只有放量收回关键位置才考虑观察仓。",
            "watch": "若市场温度低于 60 分，低开修复也先按反抽看待。",
        },
    ]


def _holding_action(item: dict) -> dict:
    price = safe_float(item.get("price"))
    buy_price = safe_float(item.get("buy_price"))
    stop_loss = safe_float(item.get("stop_loss_price"))
    target = safe_float(item.get("target_price"))
    profit_pct = safe_float(item.get("profit_pct"))
    status = str(item.get("status", ""))

    if stop_loss:
        protect_price = stop_loss
        protect_reason = "用户设置止损价"
    elif buy_price > 0:
        protect_price = round(buy_price * 0.92, 3)
        protect_reason = "按成本回撤 8% 估算保护线"
    else:
        protect_price = round(price * 0.92, 3) if price else 0
        protect_reason = "缺少成本，按现价回撤 8% 估算"

    if protect_price and price and price < protect_price:
        action = "已经低于保护线，优先降风险或等待有效收回后再评估。"
        trigger = f"有效收回 {protect_price} 前，不把它当作加仓对象。"
    elif status in {"止损", "减仓"}:
        action = "优先降风险，反弹不能收回关键价位时不加仓。"
        trigger = f"跌破或无法收回 {protect_price}"
    elif status in {"警惕", "换股风险"} or profit_pct < -8:
        action = "暂停加仓，观察是否重新站回短期强弱线。"
        if buy_price > 0:
            trigger = f"站回成本 {buy_price:g} 且板块转强，才恢复观察。"
        else:
            trigger = "补录真实成本后再判断盈亏；现价守住保护线且板块转强，才恢复观察。"
    elif status in {"强势持有", "可加仓观察"}:
        action = "继续观察持有条件，只在回踩不破且放量转强时考虑小仓。"
        trigger = f"守住 {protect_price}，向上接近 {target:g} 时分批评估。" if target else f"守住 {protect_price}，放量突破近期高点再评估。"
    else:
        action = "按普通观察仓处理，等待市场和板块给出方向。"
        trigger = "跌破保护线降低暴露，放量转强再观察。"

    return {
        "stock_code": item.get("stock_code"),
        "stock_name": item.get("stock_name"),
        "price": price,
        "profit_pct": profit_pct,
        "status": status,
        "risk_level": item.get("risk_level"),
        "protect_price": protect_price,
        "trigger": trigger,
        "action": action,
        "reason": f"{protect_reason}；{item.get('reason', '')}",
    }


def _data_gaps() -> list[dict]:
    return [
        {"priority": "高", "data_gap": "实时行情", "plan": "设置 A_STOCK_USE_LIVE_DATA=1 后请求 AKShare；若接口不稳定继续使用示例数据做流程演练。"},
        {"priority": "高", "data_gap": "新闻/公告/财报风险", "plan": "当前没有接入公告和舆情，临近开盘或盘中异动仍需人工复核。"},
        {"priority": "中", "data_gap": "历史回测", "plan": "当前规则没有历史胜率统计，仓位建议按保守上限执行。"},
        {"priority": "中", "data_gap": "个人交易风格", "plan": "可在 data/trading_profile.json 调整总仓位、单票上限和交易周期。"},
    ]


def build_trade_plan(
    market_summary: dict,
    overseas_summary: dict,
    sectors: pd.DataFrame,
    candidates: pd.DataFrame,
    holding_reports: list[dict],
    risk_rows: list[dict],
    profile: dict,
) -> dict:
    market_score = safe_float(market_summary.get("score"))
    decision, position_advice = _position_band(market_score, overseas_summary, len(risk_rows), profile)
    top_sectors = _top_names(sectors, "sector_name", 4)
    top_candidates = _top_names(candidates, "stock_name", 4)
    overseas_bias = overseas_summary.get("opening_bias", "中性")

    holding_actions = [_holding_action(item) for item in holding_reports]
    risky_holding_count = sum(1 for item in holding_reports if item.get("risk_level") in {"高风险", "极高风险"} or item.get("status") in {"止损", "减仓", "警惕"})
    if risky_holding_count >= 2 and "积极" in decision:
        decision = "先修复持仓，再寻找机会"

    watch_focus = []
    if top_sectors:
        watch_focus.append({"item": "板块主线", "content": "、".join(top_sectors), "action": "只在前排板块里找机会，弱板块反弹不优先。"})
    if top_candidates:
        watch_focus.append({"item": "候选池", "content": "、".join(top_candidates), "action": "等待回踩承接、放量突破或评分继续改善。"})
    watch_focus.append({"item": "外围映射", "content": overseas_bias, "action": overseas_summary.get("premarket_action", "以盘中确认信号为准。")})

    return {
        "generated_at": now_text(),
        "decision": decision,
        "position_advice": position_advice,
        "style": profile.get("style", "波段交易"),
        "review_time": profile.get("review_time", "盘前、盘中、收盘后"),
        "watch_focus": watch_focus,
        "opening_scenarios": _opening_scenarios(market_score, overseas_summary, sectors),
        "holding_actions": holding_actions,
        "buy_sell_rules": [
            {"item": "买入触发", "content": "市场温度不低于 60，目标板块仍在强势前排，个股放量突破或回踩不破。"},
            {"item": "禁止追高", "content": "连续急拉、距涨停太近、板块冲高回落时不新增仓位。"},
            {"item": "减仓触发", "content": "跌破保护线、放量跌破 20 日线、或明显弱于同板块前排。"},
            {"item": "换股触发", "content": "持仓弱于板块，同时候选池出现更高评分且风险更低的标的。"},
            {"item": "复盘纪律", "content": "每次操作后记录触发条件、仓位、止损线和复盘结论。"},
        ],
        "data_gaps": _data_gaps(),
        "disclaimer": "以上为数据面板生成的辅助分析，不构成投资建议，也不是买卖指令。",
    }
