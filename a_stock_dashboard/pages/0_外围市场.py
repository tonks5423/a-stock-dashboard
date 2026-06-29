from __future__ import annotations

import streamlit as st

from config import APP_TITLE, REFRESH_SECONDS
from modules.data_fetcher import fetch_overseas_market
from modules.display import inject_page_style, metric_card, show_table, signal_legend
from modules.overseas_analyzer import analyze_overseas_sentiment


st.set_page_config(page_title=f"{APP_TITLE} · 外围市场", layout="wide")
inject_page_style()


@st.cache_data(ttl=REFRESH_SECONDS)
def load_data():
    result = fetch_overseas_market()
    return result, analyze_overseas_sentiment(result.data)


result, summary = load_data()

st.title("外围市场")
st.caption(f"数据更新时间：{result.update_time} · 数据源：{result.source} · 外围市场只作为盘前情绪参考")
signal_legend()
if result.warning:
    st.warning(result.warning)

cols = st.columns(4)
with cols[0]:
    metric_card("外围情绪", summary["sentiment"])
with cols[1]:
    metric_card("情绪分", f"{summary['score']:.1f} / 100")
with cols[2]:
    metric_card("开盘倾向", summary["opening_bias"])
with cols[3]:
    metric_card("A50", f"{float(result.data.loc[result.data['symbol'].eq('A50'), 'pct_chg'].iloc[0]):+.2f}%")

st.info(summary["conclusion"])
st.warning(f"盘前操作参考：{summary['premarket_action']}")

st.subheader("外围分项")
dimension_cols = st.columns(4)
for column, (name, score) in zip(dimension_cols, summary["dimensions"].items()):
    with column:
        metric_card(name, f"{score:.1f} / 100")

tabs = st.tabs(["全部", "美股", "美股科技", "A股映射", "港股", "中概股", "汇率利率", "商品", "风险偏好"])
filters = [
    None,
    ["美股"],
    ["美股科技"],
    ["A股映射"],
    ["港股"],
    ["中概股"],
    ["汇率", "利率"],
    ["商品"],
    ["风险偏好"],
]
for tab, categories in zip(tabs, filters):
    with tab:
        data = result.data if categories is None else result.data.loc[result.data["category"].isin(categories)]
        show_table(data, ["name", "symbol", "category", "value", "pct_chg", "note"])
