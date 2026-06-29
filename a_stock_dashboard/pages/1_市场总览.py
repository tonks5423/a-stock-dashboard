from __future__ import annotations

import streamlit as st

from config import APP_TITLE, current_refresh_bucket, refresh_schedule_caption
from modules.data_fetcher import fetch_market_overview
from modules.display import inject_page_style, metric_card, show_table, signal_legend
from modules.market_analyzer import summarize_market


st.set_page_config(page_title=f"{APP_TITLE} · 市场总览", layout="wide")
inject_page_style()


@st.cache_data
def load_data(refresh_bucket: str):
    result = fetch_market_overview()
    return result, summarize_market(result.data)


result, summary = load_data(current_refresh_bucket())
st.title("市场总览")
st.caption(f"数据更新时间：{result.update_time} · 数据源：{result.source} · {refresh_schedule_caption()}")
signal_legend()
if result.warning:
    st.warning(result.warning)

cols = st.columns(5)
with cols[0]:
    metric_card("市场温度", f"{summary['score']:.1f} / 100")
with cols[1]:
    metric_card("市场状态", summary["state"])
with cols[2]:
    metric_card("成交额", f"{result.data['amount_yi']:.0f} 亿")
with cols[3]:
    metric_card("上涨家数", result.data["up_count"])
with cols[4]:
    metric_card("下跌家数", result.data["down_count"])

st.info(summary["conclusion"])
show_table(result.data["indices"], ["name", "code", "pct_chg"])
