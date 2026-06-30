from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st


COLUMN_LABELS = {
    "name": "名字",
    "symbol": "代码",
    "category": "类别",
    "value": "数值",
    "note": "说明",
    "impact": "影响方向",
    "code": "代码",
    "pct_chg": "涨跌幅(%)",
    "pct_chg_5d": "5日涨跌幅(%)",
    "pct_chg_10d": "10日涨跌幅(%)",
    "pct_chg_20d": "20日涨跌幅(%)",
    "amount": "成交额",
    "amount_yi": "成交额(亿)",
    "amount_5d_avg_yi": "5日均成交额(亿)",
    "amount_20d_avg_yi": "20日均成交额(亿)",
    "amount_ratio": "成交额变化",
    "vs_5d_pct": "较5日均量(%)",
    "vs_20d_pct": "较20日均量(%)",
    "liquidity_state": "资金状态",
    "flow_state": "放量状态",
    "money_flow_state": "资金信号",
    "money_flow_hint": "资金提示",
    "up_count": "上涨家数",
    "down_count": "下跌家数",
    "limit_up_count": "涨停家数",
    "limit_down_count": "跌停家数",
    "sector_name": "板块名称",
    "sector_type": "板块类型",
    "leading_stock": "领涨股票",
    "score": "评分",
    "state": "状态",
    "score_reason": "评分原因",
    "stock_code": "股票代码",
    "stock_name": "股票名称",
    "industry": "所属行业",
    "concept": "所属概念",
    "price": "当前价格",
    "turnover_rate": "换手率(%)",
    "volume_ratio": "量比",
    "above_ma5": "站上5日线",
    "above_ma10": "站上10日线",
    "above_ma20": "站上20日线",
    "above_ma60": "站上60日线",
    "new_high_20d": "突破20日新高",
    "new_high_60d": "突破60日新高",
    "dist_limit_up_pct": "距涨停(%)",
    "dist_limit_down_pct": "距跌停(%)",
    "sector_score": "板块强度分",
    "trend_score": "趋势分",
    "volume_score": "量能分",
    "basic_score": "基本面分",
    "risk_score": "风险分",
    "final_score": "最终评分",
    "score_label": "评分解释",
    "buy_price": "买入价格",
    "shares": "持仓数量",
    "market_value": "持仓市值",
    "profit": "浮动盈亏",
    "profit_pct": "浮动盈亏(%)",
    "stop_loss_price": "止损价格",
    "target_price": "目标价格",
    "current_price": "当前市价",
    "current_market_value": "当前市值",
    "dist_stop_loss_pct": "距止损(%)",
    "dist_target_pct": "距目标(%)",
    "sector": "所属板块",
    "stock_score": "个股强度分",
    "status": "持仓状态",
    "suggestion": "辅助建议",
    "reason": "原因",
    "risk_level": "风险等级",
    "risk_items": "风险项",
    "item": "项目",
    "content": "内容",
    "action": "辅助动作",
    "scenario": "开盘剧本",
    "condition": "触发条件",
    "watch": "观察重点",
    "protect_price": "保护价",
    "trigger": "触发条件",
    "data_gap": "数据缺口",
    "plan": "优化方案",
    "priority": "优先级",
    "style": "交易风格",
    "review_time": "复盘时间",
}

PERCENT_COLUMNS = {
    "涨跌幅(%)",
    "5日涨跌幅(%)",
    "10日涨跌幅(%)",
    "20日涨跌幅(%)",
    "浮动盈亏(%)",
    "较5日均量(%)",
    "较20日均量(%)",
}

DISTANCE_PERCENT_COLUMNS = {
    "换手率(%)",
    "距涨停(%)",
    "距跌停(%)",
    "距止损(%)",
    "距目标(%)",
}

MONEY_COLUMNS = {
    "成交额",
    "成交额(亿)",
    "5日均成交额(亿)",
    "20日均成交额(亿)",
    "买入价格",
    "当前价格",
    "当前市价",
    "持仓市值",
    "当前市值",
    "浮动盈亏",
    "止损价格",
    "目标价格",
    "数值",
    "保护价",
}

SCORE_COLUMNS = {
    "评分",
    "板块强度分",
    "趋势分",
    "量能分",
    "基本面分",
    "风险分",
    "最终评分",
    "个股强度分",
}


def inject_page_style() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            max-width: 1380px;
        }
        h1, h2, h3 {
            letter-spacing: 0;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e6eaf0;
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetricLabel"] p {
            color: #64748b;
            font-size: 0.88rem;
        }
        div[data-testid="stMetricValue"] {
            color: #0f172a;
            font-weight: 700;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #e6eaf0;
            border-radius: 8px;
            overflow: hidden;
        }
        .stAlert {
            border-radius: 8px;
        }
        .metric-card {
            min-height: 92px;
            background: #ffffff;
            border: 1px solid #e6eaf0;
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 6px;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        .metric-card__label {
            color: #64748b;
            font-size: 0.88rem;
            line-height: 1.25;
            white-space: normal;
        }
        .metric-card__value {
            color: #0f172a;
            font-size: 1.55rem;
            line-height: 1.15;
            font-weight: 750;
            white-space: normal;
        }
        .metric-card__sub {
            color: #475569;
            font-size: 0.86rem;
            line-height: 1.25;
            white-space: normal;
        }
        .signal-legend {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
            margin: 4px 0 10px 0;
            color: #64748b;
            font-size: 0.86rem;
        }
        .signal-legend span {
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }
        .signal-up {
            color: #dc2626;
            font-weight: 700;
        }
        .signal-down {
            color: #059669;
            font-weight: 700;
        }
        .signal-flat {
            color: #64748b;
            font-weight: 700;
        }
        .action-panel {
            border: 1px solid #dbe3ee;
            border-radius: 8px;
            background: #f8fafc;
            padding: 16px 18px;
            margin: 8px 0 14px 0;
        }
        .action-panel__head {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
            flex-wrap: wrap;
        }
        .action-panel__decision {
            font-size: 1.2rem;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.25;
        }
        .action-panel__meta {
            color: #64748b;
            font-size: .86rem;
            line-height: 1.35;
        }
        .action-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 10px;
            margin-top: 12px;
        }
        .action-tile {
            background: #ffffff;
            border: 1px solid #e6eaf0;
            border-radius: 8px;
            padding: 12px 14px;
        }
        .action-tile__label {
            color: #64748b;
            font-size: .84rem;
            margin-bottom: 6px;
        }
        .action-tile__value {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.45;
        }
        .scenario-grid,
        .holding-action-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
            margin: 8px 0 18px 0;
        }
        .scenario-card,
        .holding-action-card {
            background: #ffffff;
            border: 1px solid #e6eaf0;
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .scenario-card__title,
        .holding-action-card__title {
            color: #0f172a;
            font-size: 1.02rem;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .card-line {
            color: #334155;
            font-size: .9rem;
            line-height: 1.55;
            margin-top: 6px;
        }
        .card-label {
            color: #64748b;
            font-weight: 650;
        }
        .status-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 2px 8px;
            font-size: .78rem;
            font-weight: 750;
            background: #f1f5f9;
            color: #475569;
            margin-left: 6px;
        }
        .status-chip--warn {
            background: #fef3c7;
            color: #92400e;
        }
        .status-chip--risk {
            background: #fee2e2;
            color: #991b1b;
        }
        .status-chip--ok {
            background: #dcfce7;
            color: #166534;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _smart_number(value: float, digits: int = 2) -> str:
    if abs(value) >= 1000:
        return f"{value:,.{digits}f}"
    if abs(value) >= 100:
        return f"{value:.2f}"
    if abs(value) >= 10:
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return f"{value:.4f}".rstrip("0").rstrip(".")


def _is_number(value) -> bool:
    try:
        return pd.notna(value) and isinstance(float(value), float)
    except (TypeError, ValueError):
        return False


def _format_directional(value: float, suffix: str = "") -> str:
    if value > 0:
        return f"↑ +{_smart_number(value)}{suffix}"
    if value < 0:
        return f"↓ {_smart_number(value)}{suffix}"
    return f"→ {_smart_number(value)}{suffix}"


def _format_cell(column: str, value):
    if pd.isna(value):
        return ""
    if column in PERCENT_COLUMNS and _is_number(value):
        return _format_directional(float(value), "%")
    if column in DISTANCE_PERCENT_COLUMNS and _is_number(value):
        return f"{_smart_number(float(value))}%"
    if column == "成交额变化" and _is_number(value):
        return f"{_smart_number(float(value))} 倍"
    if column == "浮动盈亏" and _is_number(value):
        return _format_directional(float(value))
    if column in MONEY_COLUMNS and _is_number(value):
        return _smart_number(float(value))
    if column in SCORE_COLUMNS and _is_number(value):
        return _smart_number(float(value), 1)
    if column == "持仓数量" and _is_number(value):
        return f"{float(value):,.0f}"
    return value


def display_df(data, columns: list[str] | None = None) -> pd.DataFrame:
    frame = pd.DataFrame(data).copy()
    if columns is not None:
        frame = frame[columns]
    bool_columns = frame.select_dtypes(include=["bool"]).columns
    for column in bool_columns:
        frame[column] = frame[column].map({True: "是", False: "否"})
    frame = frame.rename(columns=COLUMN_LABELS)
    for column in frame.columns:
        frame[column] = frame[column].map(lambda value, column=column: _format_cell(column, value))
    return frame


def _cell_style(value) -> str:
    text = str(value)
    if text.startswith("↑") or text.startswith("+"):
        return "color: #dc2626; font-weight: 700;"
    if text.startswith("↓") or text.startswith("-"):
        return "color: #059669; font-weight: 700;"
    if text.startswith("→"):
        return "color: #64748b; font-weight: 650;"
    if text in {"极高风险", "高风险", "止损", "减仓"}:
        return "color: #991b1b; background-color: #fee2e2; font-weight: 700;"
    if text in {"中风险", "警惕", "换股风险"}:
        return "color: #92400e; background-color: #fef3c7; font-weight: 700;"
    if text in {"低风险", "强势持有", "可加仓观察", "主线强板块", "活跃板块", "强候选，重点观察", "增量资金活跃", "资金面可交易", "明显放量", "温和放量", "放量上涨", "资金活跃"}:
        return "color: #166534; background-color: #dcfce7; font-weight: 700;"
    if text in {"弱势板块", "偏弱，不买", "回避", "缩量谨慎", "明显缩量", "温和缩量", "放量下跌"}:
        return "color: #991b1b; background-color: #fee2e2; font-weight: 700;"
    return ""


def show_table(data, columns: list[str] | None = None) -> None:
    frame = display_df(data, columns)
    styled = frame.style.map(_cell_style)
    st.dataframe(styled, width="stretch", hide_index=True)


def signal_legend() -> None:
    st.html(
        """
        <div class="signal-legend">
            <span><b>颜色说明：</b></span>
            <span class="signal-up">↑ 上涨 / 盈利</span>
            <span class="signal-down">↓ 下跌 / 亏损</span>
            <span class="signal-flat">→ 持平</span>
            <span>风险和状态会用底色提示优先级</span>
        </div>
        """
    )


def holding_summary_cards(reports: list[dict]) -> None:
    if not reports:
        return
    cards = []
    for item in reports:
        profit = float(item.get("profit", 0) or 0)
        profit_pct = float(item.get("profit_pct", 0) or 0)
        signal_class = "signal-up" if profit > 0 else "signal-down" if profit < 0 else "signal-flat"
        arrow = "↑" if profit > 0 else "↓" if profit < 0 else "→"
        status = str(item.get("status", ""))
        risk = str(item.get("risk_level", ""))
        cards.append(
            f"""
            <div style="
                background:#fff;
                border:1px solid #e6eaf0;
                border-radius:8px;
                padding:14px 16px;
                min-height:138px;
                box-shadow:0 1px 2px rgba(15,23,42,.04);
            ">
                <div style="font-size:1rem;font-weight:750;color:#0f172a;">{escape(str(item.get("stock_name", "")))}</div>
                <div style="font-size:.82rem;color:#64748b;margin-top:2px;">{escape(str(item.get("stock_code", "")))}</div>
                <div class="{signal_class}" style="font-size:1.18rem;font-weight:800;margin-top:10px;">
                    {arrow} {_smart_number(profit)} / {_smart_number(profit_pct)}%
                </div>
                <div style="font-size:.9rem;color:#475569;margin-top:8px;">
                    市值 {_smart_number(float(item.get("market_value", 0) or 0))} · 现价 {_smart_number(float(item.get("price", 0) or 0))}
                </div>
                <div style="font-size:.86rem;color:#64748b;margin-top:8px;">
                    {escape(status)} · {escape(risk)}
                </div>
            </div>
            """
        )
    st.html(
        f"""
        <div style="
            display:grid;
            grid-template-columns:repeat(auto-fit, minmax(210px, 1fr));
            gap:12px;
            margin:6px 0 14px 0;
        ">
            {''.join(cards)}
        </div>
        """
    )


def metric_card(label: str, value, sub: str | None = None) -> None:
    sub_html = f'<div class="metric-card__sub">{escape(str(sub))}</div>' if sub else ""
    value_text = str(value)
    value_class = "metric-card__value"
    if value_text.startswith("+") or value_text.startswith("↑"):
        value_class += " signal-up"
    elif value_text.startswith("-") or value_text.startswith("↓"):
        value_class += " signal-down"
    st.html(
        f"""
        <div class="metric-card">
            <div class="metric-card__label">{escape(str(label))}</div>
            <div class="{value_class}">{escape(value_text)}</div>
            {sub_html}
        </div>
        """
    )


def guidance_panel(guidance: dict) -> None:
    items = "".join(f"<li>{escape(str(line))}</li>" for line in guidance.get("lines", []))
    st.html(
        f"""
        <div style="
            margin-top: 18px;
            padding: 18px 20px;
            border: 1px solid #dbe3ee;
            border-radius: 8px;
            background: #f8fafc;
        ">
            <div style="display:flex; justify-content:space-between; gap:12px; align-items:flex-start; flex-wrap:wrap;">
                <div style="font-size:1.15rem; font-weight:750; color:#0f172a;">{escape(str(guidance.get("title", "当前操作指导")))}</div>
                <div style="font-size:0.86rem; color:#64748b;">生成时间：{escape(str(guidance.get("generated_at", "")))}</div>
            </div>
            <ol style="margin:12px 0 10px 1.2rem; padding:0; color:#1e293b; line-height:1.75;">
                {items}
            </ol>
            <div style="font-size:0.86rem; color:#64748b; border-top:1px solid #e2e8f0; padding-top:10px;">
                {escape(str(guidance.get("disclaimer", "")))}
            </div>
        </div>
        """
    )


def action_plan_panel(plan: dict) -> None:
    focus = plan.get("watch_focus", [])
    tiles = [
        ("建议仓位", plan.get("position_advice", "")),
        ("交易风格", plan.get("style", "")),
        ("复盘时间", plan.get("review_time", "")),
    ]
    for item in focus[:3]:
        tiles.append((item.get("item", "观察重点"), item.get("content", "")))
    tile_html = "".join(
        f"""
        <div class="action-tile">
            <div class="action-tile__label">{escape(str(label))}</div>
            <div class="action-tile__value">{escape(str(value))}</div>
        </div>
        """
        for label, value in tiles
    )
    st.html(
        f"""
        <div class="action-panel">
            <div class="action-panel__head">
                <div>
                    <div class="action-panel__meta">今日行动清单</div>
                    <div class="action-panel__decision">{escape(str(plan.get("decision", "")))}</div>
                </div>
                <div class="action-panel__meta">生成时间：{escape(str(plan.get("generated_at", "")))}</div>
            </div>
            <div class="action-grid">{tile_html}</div>
            <div class="action-panel__meta" style="margin-top:10px;">{escape(str(plan.get("disclaimer", "")))}</div>
        </div>
        """
    )


def compact_list_panel(title: str, rows: list[dict], columns: list[str] | None = None) -> None:
    st.subheader(title)
    if rows:
        show_table(rows, columns)
    else:
        st.info("暂无数据。")


def scenario_cards(rows: list[dict]) -> None:
    st.subheader("开盘三剧本")
    if not rows:
        st.info("暂无开盘剧本。")
        return
    cards = []
    for row in rows:
        cards.append(
            f"""
            <div class="scenario-card">
                <div class="scenario-card__title">{escape(str(row.get("scenario", "")))}</div>
                <div class="card-line"><span class="card-label">触发：</span>{escape(str(row.get("condition", "")))}</div>
                <div class="card-line"><span class="card-label">动作：</span>{escape(str(row.get("action", "")))}</div>
                <div class="card-line"><span class="card-label">观察：</span>{escape(str(row.get("watch", "")))}</div>
            </div>
            """
        )
    st.html(f'<div class="scenario-grid">{"".join(cards)}</div>')


def holding_action_cards(rows: list[dict]) -> None:
    st.subheader("持仓处理方案")
    if not rows:
        st.info("暂无持仓处理方案。")
        return
    cards = []
    for row in rows:
        profit_pct = safe_profit_pct(row.get("profit_pct"))
        profit_class = "signal-up" if profit_pct > 0 else "signal-down" if profit_pct < 0 else "signal-flat"
        status = str(row.get("status", ""))
        risk = str(row.get("risk_level", ""))
        money_flow = str(row.get("money_flow_state", ""))
        chip_class = "status-chip--risk" if status in {"止损", "减仓"} or risk in {"高风险", "极高风险"} else "status-chip--warn" if status in {"警惕", "换股风险"} else "status-chip--ok"
        cards.append(
            f"""
            <div class="holding-action-card">
                <div class="holding-action-card__title">
                    {escape(str(row.get("stock_name", "")))}
                    <span class="status-chip {chip_class}">{escape(status)} · {escape(risk)}</span>
                </div>
                <div class="card-line">
                    <span class="card-label">现价：</span>{escape(_smart_number(float(row.get("price", 0) or 0)))}
                    <span class="{profit_class}" style="margin-left:10px;">{escape(_format_directional(profit_pct, "%"))}</span>
                </div>
                <div class="card-line"><span class="card-label">保护价：</span>{escape(_smart_number(float(row.get("protect_price", 0) or 0)))}</div>
                <div class="card-line"><span class="card-label">资金：</span>{escape(money_flow)}</div>
                <div class="card-line"><span class="card-label">触发：</span>{escape(str(row.get("trigger", "")))}</div>
                <div class="card-line"><span class="card-label">动作：</span>{escape(str(row.get("action", "")))}</div>
            </div>
            """
        )
    st.html(f'<div class="holding-action-grid">{"".join(cards)}</div>')


def safe_profit_pct(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
