from __future__ import annotations

import streamlit as st

from config import APP_TITLE, HOLDINGS_FILE, PUBLIC_HOLDINGS_FILE, PUBLIC_MODE, TRADING_PROFILE_FILE, current_refresh_bucket, refresh_schedule_caption
from modules.action_engine import build_trade_plan, load_trading_profile
from modules import data_fetcher
from modules.data_fetcher import fetch_market_overview, fetch_overseas_market, fetch_sector_rank, get_sample_stocks, load_holdings
from modules.display import action_plan_panel, compact_list_panel, guidance_panel, holding_action_cards, holding_summary_cards, inject_page_style, metric_card, scenario_cards, show_table, signal_legend
from modules.funds_analyzer import summarize_funds
from modules.guidance import generate_operation_guidance
from modules.holding_analyzer import analyze_holding, stock_data_from_holding
from modules.market_analyzer import summarize_market
from modules.overseas_analyzer import analyze_overseas_sentiment
from modules.sector_analyzer import add_sector_state
from modules.stock_analyzer import score_stocks, screen_candidates


st.set_page_config(page_title=APP_TITLE, page_icon="📈", layout="wide")
inject_page_style()


def safe_live_cache_status() -> str:
    if hasattr(data_fetcher, "live_cache_status"):
        return data_fetcher.live_cache_status()
    return "行情缓存：状态函数暂不可用，请等待云端完成最新部署"


@st.cache_data
def load_dashboard_data(refresh_bucket: str):
    market_result = fetch_market_overview()
    overseas_result = fetch_overseas_market()
    sectors_result = fetch_sector_rank()
    market_summary = summarize_market(market_result.data)
    overseas_summary = analyze_overseas_sentiment(overseas_result.data)
    sectors = add_sector_state(sectors_result.data)
    stocks = score_stocks(get_sample_stocks(sectors), market_summary["score"])
    candidates = screen_candidates(stocks)
    funds_summary = summarize_funds(market_result.data, sectors, stocks)
    return market_result, overseas_result, sectors_result, market_summary, overseas_summary, funds_summary, sectors, stocks, candidates


market_result, overseas_result, sectors_result, market_summary, overseas_summary, funds_summary, sectors, stocks, candidates = load_dashboard_data(current_refresh_bucket())

st.title(APP_TITLE)
mode_label = "公开展示模式" if PUBLIC_MODE else "私人本地模式"
st.caption(f"数据更新时间：{market_result.update_time} · 行情源：{market_result.source} · {safe_live_cache_status()} · {mode_label} · {refresh_schedule_caption()} · 仅做辅助分析，不连接券商账户，不自动下单。")
signal_legend()
if PUBLIC_MODE:
    st.info(f"当前为公开展示模式：持仓读取 {PUBLIC_HOLDINGS_FILE.name}，用于给亲友查看。")
for warning in [market_result.warning, overseas_result.warning, sectors_result.warning]:
    if warning:
        st.warning(warning)

left, right = st.columns([1.15, 0.85])
with left:
    st.subheader("市场总览")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("市场温度", f"{market_summary['score']:.1f} / 100")
    with m2:
        metric_card("市场状态", market_summary["state"])
    with m3:
        metric_card("两市成交额", f"{market_result.data['amount_yi']:.0f} 亿")
    with m4:
        metric_card("涨停 / 跌停", f"{market_result.data['limit_up_count']} / {market_result.data['limit_down_count']}")
    st.info(market_summary["conclusion"])
    show_table(market_result.data["indices"], ["name", "code", "pct_chg"])

with right:
    st.subheader("市场广度")
    b1, b2 = st.columns(2)
    with b1:
        metric_card("上涨家数", market_result.data["up_count"])
    with b2:
        metric_card("下跌家数", market_result.data["down_count"])
    st.progress(min(market_summary["score"] / 100, 1.0), text=market_summary["reason"])

st.subheader("外围情绪")
o1, o2, o3, o4 = st.columns(4)
overseas_lookup = dict(zip(overseas_result.data["symbol"], overseas_result.data["pct_chg"]))
with o1:
    metric_card("外围结论", overseas_summary["sentiment"], f"{overseas_summary['score']:.1f} 分")
with o2:
    metric_card("开盘倾向", overseas_summary["opening_bias"])
with o3:
    metric_card("纳指 / 费半", f"{overseas_lookup.get('NASDAQ', 0):+.2f}% / {overseas_lookup.get('SOX', 0):+.2f}%")
with o4:
    metric_card("A50 / 人民币", f"{overseas_lookup.get('A50', 0):+.2f}% / {overseas_lookup.get('USD/CNH', 0):+.2f}%")
st.info(overseas_summary["conclusion"])

st.subheader("资金流向")
f1, f2, f3, f4 = st.columns(4)
with f1:
    metric_card("资金评分", f"{funds_summary['score']:.1f} / 100")
with f2:
    metric_card("资金状态", funds_summary["liquidity_state"], funds_summary["flow_state"])
with f3:
    metric_card("成交额 / 5日均", f"{funds_summary['amount_yi']:.0f} 亿", f"{funds_summary['vs_5d_pct']:+.1f}%")
with f4:
    metric_card("成交额 / 20日均", f"{funds_summary['amount_20d_avg_yi']:.0f} 亿", f"{funds_summary['vs_20d_pct']:+.1f}%")
st.info(funds_summary["conclusion"])
money_left, money_right = st.columns([1, 1])
with money_left:
    st.caption("资金活跃板块")
    show_table(funds_summary["hot_money_sectors"], ["sector_name", "sector_type", "pct_chg", "amount_yi", "amount_ratio", "score"])
with money_right:
    st.caption("成交活跃个股")
    show_table(funds_summary["active_stocks"], ["stock_code", "stock_name", "industry", "pct_chg", "amount_yi", "turnover_rate", "volume_ratio", "final_score"])

st.subheader("最强板块")
sector_view = sectors[["sector_name", "sector_type", "pct_chg", "pct_chg_5d", "pct_chg_10d", "amount_ratio", "leading_stock", "score", "state", "score_reason"]].head(10)
show_table(sector_view)

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("候选买入观察")
    candidate_view = candidates if not candidates.empty else stocks.head(5)
    show_table(
        candidate_view[["stock_code", "stock_name", "industry", "price", "pct_chg", "sector_score", "trend_score", "risk_score", "final_score", "score_label"]],
    )
with col_b:
    st.subheader("我的公开持仓" if PUBLIC_MODE else "我的持仓")
    holdings = load_holdings(HOLDINGS_FILE)
    reports = []
    for _, holding in holdings.iterrows():
        stock_row = stocks.loc[stocks["stock_code"].eq(str(holding["stock_code"]).zfill(6))]
        stock_data = stock_row.iloc[0].to_dict() if not stock_row.empty else stock_data_from_holding(holding.to_dict())
        sector_row = sectors.loc[sectors["sector_name"].eq(stock_data.get("industry"))]
        sector_data = sector_row.iloc[0].to_dict() if not sector_row.empty else {"score": stock_data.get("sector_score", 50)}
        reports.append(analyze_holding(holding.to_dict(), stock_data, sector_data, market_result.data))
    if reports:
        holding_summary_cards(reports)
        show_table(reports, ["stock_code", "stock_name", "profit", "profit_pct", "market_value", "status", "money_flow_state", "amount_yi", "volume_ratio", "turnover_rate", "money_flow_hint"])
    else:
        st.info("请在 data/holdings.csv 中维护持仓。")

st.subheader("风险提醒")
risk_rows = []
for _, row in stocks.iterrows():
    if row["risk_score"] > 0 or row["final_score"] < 60:
        risk_rows.append(
            {
                "股票代码": row["stock_code"],
                "股票名称": row["stock_name"],
                "风险分": row["risk_score"],
                "评分": row["final_score"],
                "提示": row["score_reason"],
            }
        )
if risk_rows:
    show_table(risk_rows)
else:
    st.success("未触发主要风险提醒。")

trading_profile = load_trading_profile(TRADING_PROFILE_FILE)
trade_plan = build_trade_plan(
    market_summary=market_summary,
    overseas_summary=overseas_summary,
    funds_summary=funds_summary,
    sectors=sectors,
    candidates=candidates,
    holding_reports=reports,
    risk_rows=risk_rows,
    profile=trading_profile,
)
action_plan_panel(trade_plan)

scenario_col, holding_action_col = st.columns([1, 1])
with scenario_col:
    scenario_cards(trade_plan["opening_scenarios"])
with holding_action_col:
    holding_action_cards(trade_plan["holding_actions"])

discipline_col, gap_col = st.columns([1, 1])
with discipline_col:
    compact_list_panel("买卖纪律", trade_plan["buy_sell_rules"], ["item", "content"])
with gap_col:
    compact_list_panel("仍需补齐的数据", trade_plan["data_gaps"], ["priority", "data_gap", "plan"])

guidance = generate_operation_guidance(
    market_summary=market_summary,
    overseas_summary=overseas_summary,
    funds_summary=funds_summary,
    sectors=sectors,
    candidates=candidates,
    holding_reports=reports,
    risk_rows=risk_rows,
)
guidance_panel(guidance)
