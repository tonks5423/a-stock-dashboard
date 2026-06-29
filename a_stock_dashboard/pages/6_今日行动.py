from __future__ import annotations

import streamlit as st

from config import APP_TITLE, HOLDINGS_FILE, PUBLIC_MODE, REFRESH_SECONDS, TRADING_PROFILE_FILE
from modules.action_engine import build_trade_plan, load_trading_profile
from modules.data_fetcher import fetch_market_overview, fetch_overseas_market, fetch_sector_rank, get_sample_stocks, load_holdings
from modules.display import action_plan_panel, compact_list_panel, holding_action_cards, inject_page_style, scenario_cards, signal_legend
from modules.holding_analyzer import analyze_holding, stock_data_from_holding
from modules.market_analyzer import summarize_market
from modules.overseas_analyzer import analyze_overseas_sentiment
from modules.sector_analyzer import add_sector_state
from modules.stock_analyzer import score_stocks, screen_candidates


st.set_page_config(page_title=f"{APP_TITLE} · 今日行动", layout="wide")
inject_page_style()


@st.cache_data(ttl=REFRESH_SECONDS)
def load_data():
    market_result = fetch_market_overview()
    overseas_result = fetch_overseas_market()
    sectors_result = fetch_sector_rank()
    market_summary = summarize_market(market_result.data)
    overseas_summary = analyze_overseas_sentiment(overseas_result.data)
    sectors = add_sector_state(sectors_result.data)
    stocks = score_stocks(get_sample_stocks(sectors), market_summary["score"])
    candidates = screen_candidates(stocks)
    holdings = load_holdings(HOLDINGS_FILE)
    return market_result, overseas_result, sectors_result, market_summary, overseas_summary, sectors, stocks, candidates, holdings


market_result, overseas_result, sectors_result, market_summary, overseas_summary, sectors, stocks, candidates, holdings = load_data()

st.title("今日行动")
mode_label = "公开展示模式" if PUBLIC_MODE else "私人本地模式"
st.caption(f"数据更新时间：{market_result.update_time} · 行情源：{market_result.source} · {mode_label} · 配置：{TRADING_PROFILE_FILE}")
signal_legend()
if PUBLIC_MODE:
    st.info("当前为公开展示模式：行动方案基于示例持仓生成，不暴露你的真实持仓。")
for warning in [market_result.warning, overseas_result.warning, sectors_result.warning]:
    if warning:
        st.warning(warning)

reports = []
for _, holding in holdings.iterrows():
    stock_row = stocks.loc[stocks["stock_code"].eq(str(holding["stock_code"]).zfill(6))]
    stock_data = stock_row.iloc[0].to_dict() if not stock_row.empty else stock_data_from_holding(holding.to_dict())
    sector_row = sectors.loc[sectors["sector_name"].eq(stock_data.get("industry"))]
    sector_data = sector_row.iloc[0].to_dict() if not sector_row.empty else {"score": stock_data.get("sector_score", 50)}
    reports.append(analyze_holding(holding.to_dict(), stock_data, sector_data, market_result.data))

risk_rows = []
for _, row in stocks.iterrows():
    if row["risk_score"] > 0 or row["final_score"] < 60:
        risk_rows.append(
            {
                "stock_code": row["stock_code"],
                "stock_name": row["stock_name"],
                "risk_score": row["risk_score"],
                "final_score": row["final_score"],
                "reason": row["score_reason"],
            }
        )

trade_plan = build_trade_plan(
    market_summary=market_summary,
    overseas_summary=overseas_summary,
    sectors=sectors,
    candidates=candidates,
    holding_reports=reports,
    risk_rows=risk_rows,
    profile=load_trading_profile(TRADING_PROFILE_FILE),
)

action_plan_panel(trade_plan)

left, right = st.columns([1, 1])
with left:
    scenario_cards(trade_plan["opening_scenarios"])
with right:
    compact_list_panel("观察重点", trade_plan["watch_focus"], ["item", "content", "action"])

holding_action_cards(trade_plan["holding_actions"])

rule_col, gap_col = st.columns([1, 1])
with rule_col:
    compact_list_panel("买卖纪律", trade_plan["buy_sell_rules"], ["item", "content"])
with gap_col:
    compact_list_panel("仍需补齐的数据", trade_plan["data_gaps"], ["priority", "data_gap", "plan"])
