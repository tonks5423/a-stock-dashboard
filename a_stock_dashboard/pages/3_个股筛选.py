from __future__ import annotations

import streamlit as st

from config import APP_TITLE, current_refresh_bucket, refresh_schedule_caption
from modules.data_fetcher import fetch_market_overview, fetch_sector_rank, get_sample_stocks
from modules.display import inject_page_style, show_table, signal_legend
from modules.market_analyzer import summarize_market
from modules.sector_analyzer import add_sector_state
from modules.stock_analyzer import score_stocks, screen_candidates


st.set_page_config(page_title=f"{APP_TITLE} · 个股筛选", layout="wide")
inject_page_style()


@st.cache_data
def load_data(refresh_bucket: str):
    market = fetch_market_overview()
    sectors = add_sector_state(fetch_sector_rank().data)
    summary = summarize_market(market.data)
    stocks = score_stocks(get_sample_stocks(sectors), summary["score"])
    return market, sectors, stocks, screen_candidates(stocks)


market, sectors, stocks, candidates = load_data(current_refresh_bucket())
st.title("个股筛选")
st.caption(f"数据更新时间：{market.update_time} · {refresh_schedule_caption()}")
signal_legend()

min_score = st.slider("最低最终评分", 0, 100, 60)
show_all = st.toggle("显示全部样本股票", value=False)
data = stocks if show_all else candidates
data = data.loc[data["final_score"] >= min_score]

columns = [
    "stock_code",
    "stock_name",
    "industry",
    "concept",
    "price",
    "pct_chg",
    "pct_chg_5d",
    "pct_chg_10d",
    "pct_chg_20d",
    "amount_yi",
    "turnover_rate",
    "volume_ratio",
    "above_ma5",
    "above_ma10",
    "above_ma20",
    "above_ma60",
    "new_high_20d",
    "new_high_60d",
    "dist_limit_up_pct",
    "dist_limit_down_pct",
    "sector_score",
    "trend_score",
    "risk_score",
    "final_score",
    "score_label",
]
show_table(data, columns)
with st.expander("评分原因"):
    show_table(data, ["stock_code", "stock_name", "score_reason"])
