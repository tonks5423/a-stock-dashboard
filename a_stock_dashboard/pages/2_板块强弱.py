from __future__ import annotations

import streamlit as st

from config import APP_TITLE, REFRESH_SECONDS
from modules.data_fetcher import fetch_sector_rank
from modules.display import inject_page_style, show_table, signal_legend
from modules.sector_analyzer import add_sector_state


st.set_page_config(page_title=f"{APP_TITLE} · 板块强弱", layout="wide")
inject_page_style()


@st.cache_data(ttl=REFRESH_SECONDS)
def load_data():
    result = fetch_sector_rank()
    return result, add_sector_state(result.data)


result, sectors = load_data()
st.title("板块强弱")
st.caption(f"数据更新时间：{result.update_time} · 数据源：{result.source}")
signal_legend()
if result.warning:
    st.warning(result.warning)

tabs = st.tabs(["今日最强", "近5日最强", "近10日最强", "成交额放大", "涨停数量"])
columns = ["sector_name", "sector_type", "pct_chg", "pct_chg_5d", "pct_chg_10d", "amount_ratio", "limit_up_count", "leading_stock", "score", "state"]
sorts = ["score", "pct_chg_5d", "pct_chg_10d", "amount_ratio", "limit_up_count"]
for tab, sort_col in zip(tabs, sorts):
    with tab:
        show_table(sectors.sort_values(sort_col, ascending=False).head(10), columns)
