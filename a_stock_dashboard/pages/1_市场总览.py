from __future__ import annotations

import streamlit as st

from config import APP_TITLE, current_refresh_bucket, refresh_schedule_caption
from modules import data_fetcher
from modules.data_fetcher import fetch_market_overview, fetch_sector_rank, get_sample_stocks
from modules.display import inject_page_style, metric_card, show_table, signal_legend
from modules.funds_analyzer import summarize_funds
from modules.market_analyzer import summarize_market
from modules.on_open_refresh import refresh_on_open_if_due
from modules.sector_analyzer import add_sector_state
from modules.stock_analyzer import score_stocks


st.set_page_config(page_title=f"{APP_TITLE} · 市场总览", layout="wide")
inject_page_style()
refresh_status = refresh_on_open_if_due()
if refresh_status.get("attempted_this_load"):
    st.cache_data.clear()


def safe_live_cache_status() -> str:
    if hasattr(data_fetcher, "live_cache_status"):
        return data_fetcher.live_cache_status()
    return "行情缓存：状态函数暂不可用，请等待云端完成最新部署"


@st.cache_data
def load_data(refresh_bucket: str):
    result = fetch_market_overview()
    sectors = add_sector_state(fetch_sector_rank().data)
    summary = summarize_market(result.data)
    stocks = score_stocks(get_sample_stocks(sectors), summary["score"])
    funds = summarize_funds(result.data, sectors, stocks)
    return result, summary, funds


result, summary, funds = load_data(current_refresh_bucket())
st.title("市场总览")
st.caption(f"数据更新时间：{result.update_time} · 数据源：{result.source} · {safe_live_cache_status()} · {refresh_schedule_caption()}")
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

st.subheader("资金流向")
f1, f2, f3, f4 = st.columns(4)
with f1:
    metric_card("资金评分", f"{funds['score']:.1f} / 100")
with f2:
    metric_card("资金状态", funds["liquidity_state"], funds["flow_state"])
with f3:
    metric_card("成交额 / 5日均", f"{funds['amount_yi']:.0f} 亿", f"{funds['vs_5d_pct']:+.1f}%")
with f4:
    metric_card("成交额 / 20日均", f"{funds['amount_20d_avg_yi']:.0f} 亿", f"{funds['vs_20d_pct']:+.1f}%")
st.info(funds["conclusion"])
show_table(funds["hot_money_sectors"], ["sector_name", "sector_type", "pct_chg", "amount_yi", "amount_ratio", "score"])
