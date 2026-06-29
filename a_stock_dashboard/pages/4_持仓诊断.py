from __future__ import annotations

import streamlit as st

from config import APP_TITLE, HOLDINGS_FILE, PUBLIC_MODE, REFRESH_SECONDS
from modules.data_fetcher import fetch_market_overview, fetch_sector_rank, get_sample_stocks, load_holdings
from modules.display import holding_summary_cards, inject_page_style, show_table, signal_legend
from modules.holding_analyzer import analyze_holding, stock_data_from_holding
from modules.market_analyzer import summarize_market
from modules.sector_analyzer import add_sector_state
from modules.stock_analyzer import score_stocks


st.set_page_config(page_title=f"{APP_TITLE} · 持仓诊断", layout="wide")
inject_page_style()


@st.cache_data(ttl=REFRESH_SECONDS)
def load_data():
    market = fetch_market_overview()
    sectors = add_sector_state(fetch_sector_rank().data)
    summary = summarize_market(market.data)
    stocks = score_stocks(get_sample_stocks(sectors), summary["score"])
    holdings = load_holdings(HOLDINGS_FILE)
    return market, sectors, stocks, holdings


market, sectors, stocks, holdings = load_data()
st.title("持仓诊断")
mode_label = "公开展示模式，使用演示持仓" if PUBLIC_MODE else f"持仓文件：{HOLDINGS_FILE}"
st.caption(f"{mode_label} · 数据更新时间：{market.update_time}")
signal_legend()
if PUBLIC_MODE:
    st.info("当前为公开展示模式：这里展示的是演示持仓，不读取你的本地真实持仓文件。")

reports = []
for _, holding in holdings.iterrows():
    stock_row = stocks.loc[stocks["stock_code"].eq(str(holding["stock_code"]).zfill(6))]
    stock_data = stock_row.iloc[0].to_dict() if not stock_row.empty else stock_data_from_holding(holding.to_dict())
    sector_row = sectors.loc[sectors["sector_name"].eq(stock_data.get("industry"))]
    sector_data = sector_row.iloc[0].to_dict() if not sector_row.empty else {"score": stock_data.get("sector_score", 50)}
    reports.append(analyze_holding(holding.to_dict(), stock_data, sector_data, market.data))

if reports:
    holding_summary_cards(reports)
    show_table(reports)
else:
    st.info("暂无持仓，请维护 data/holdings.csv。")
