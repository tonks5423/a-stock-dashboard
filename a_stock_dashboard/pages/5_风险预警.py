from __future__ import annotations

import streamlit as st

from config import APP_TITLE, HOLDINGS_FILE, current_refresh_bucket, refresh_schedule_caption
from modules.data_fetcher import fetch_market_overview, fetch_sector_rank, get_sample_stocks, load_holdings
from modules.display import inject_page_style, show_table, signal_legend
from modules.market_analyzer import summarize_market
from modules.on_open_refresh import refresh_on_open_if_due
from modules.risk_analyzer import analyze_stock_risk
from modules.sector_analyzer import add_sector_state
from modules.stock_analyzer import score_stocks


st.set_page_config(page_title=f"{APP_TITLE} · 风险预警", layout="wide")
inject_page_style()
refresh_status = refresh_on_open_if_due()
if refresh_status.get("attempted_this_load"):
    st.cache_data.clear()


@st.cache_data
def load_data(refresh_bucket: str):
    market = fetch_market_overview()
    sectors = add_sector_state(fetch_sector_rank().data)
    summary = summarize_market(market.data)
    stocks = score_stocks(get_sample_stocks(sectors), summary["score"])
    holdings = load_holdings(HOLDINGS_FILE)
    return market, sectors, stocks, holdings


market, sectors, stocks, holdings = load_data(current_refresh_bucket())
st.title("风险预警")
st.caption(f"数据更新时间：{market.update_time} · {refresh_schedule_caption()}")
signal_legend()

rows = []
for _, stock in stocks.iterrows():
    sector_row = sectors.loc[sectors["sector_name"].eq(stock.get("industry"))]
    sector_data = sector_row.iloc[0].to_dict() if not sector_row.empty else {"score": stock.get("sector_score", 50)}
    holding_row = holdings.loc[holdings["stock_code"].astype(str).str.zfill(6).eq(stock["stock_code"])]
    holding_data = holding_row.iloc[0].to_dict() if not holding_row.empty else None
    risk = analyze_stock_risk(stock.to_dict(), sector_data, market.data, holding_data)
    rows.append(
        {
            "股票代码": stock["stock_code"],
            "股票名称": stock["stock_name"],
            "风险等级": risk["risk_level"],
            "风险项": "；".join(risk["risk_items"]),
            "最终评分": stock["final_score"],
        }
    )

show_table(rows)
