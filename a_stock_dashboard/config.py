from __future__ import annotations

from pathlib import Path
import os
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"

HOLDINGS_FILE = DATA_DIR / "holdings.csv"
PUBLIC_HOLDINGS_FILE = DATA_DIR / "public_holdings.csv"
WATCHLIST_FILE = DATA_DIR / "watchlist.csv"
STOCK_LIST_FILE = DATA_DIR / "stock_list.csv"
TRADING_PROFILE_FILE = DATA_DIR / "trading_profile.json"

APP_TIMEZONE = ZoneInfo("Asia/Shanghai")
DATA_REFRESH_TIMES = (time(11, 30), time(14, 30))
APP_TITLE = "A 股交易数据面板"


def _setting(name: str, default: str = "0") -> str:
    value = os.getenv(name)
    if value is not None:
        return str(value)
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # noqa: BLE001
        return default
    return default


USE_LIVE_DATA = _setting("A_STOCK_USE_LIVE_DATA") == "1"

_public_mode_setting = _setting("A_STOCK_PUBLIC_MODE", "auto").lower()
PUBLIC_MODE = (
    not HOLDINGS_FILE.exists()
    if _public_mode_setting == "auto"
    else _public_mode_setting == "1"
)


def current_refresh_bucket(now: datetime | None = None) -> str:
    now = now or datetime.now(APP_TIMEZONE)
    if now.tzinfo is None:
        now = now.replace(tzinfo=APP_TIMEZONE)

    refresh_date = now.date()
    if now.time() < DATA_REFRESH_TIMES[0]:
        slot = "pre_1130"
    elif now.time() < DATA_REFRESH_TIMES[1]:
        slot = "after_1130"
    else:
        slot = "after_1430"
    return f"{refresh_date.isoformat()}:{slot}"


def next_refresh_time(now: datetime | None = None) -> datetime:
    now = now or datetime.now(APP_TIMEZONE)
    if now.tzinfo is None:
        now = now.replace(tzinfo=APP_TIMEZONE)

    for refresh_time in DATA_REFRESH_TIMES:
        candidate = datetime.combine(now.date(), refresh_time, tzinfo=APP_TIMEZONE)
        if now < candidate:
            return candidate
    return datetime.combine(now.date() + timedelta(days=1), DATA_REFRESH_TIMES[0], tzinfo=APP_TIMEZONE)


def refresh_schedule_caption(now: datetime | None = None) -> str:
    next_time = next_refresh_time(now)
    label = "今日" if next_time.date() == datetime.now(APP_TIMEZONE).date() else "明日"
    return f"数据计划刷新：每日 11:30、14:30；下次刷新窗口：{label} {next_time:%H:%M}"
