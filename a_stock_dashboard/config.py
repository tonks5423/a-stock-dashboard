from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"

HOLDINGS_FILE = DATA_DIR / "holdings.csv"
WATCHLIST_FILE = DATA_DIR / "watchlist.csv"
STOCK_LIST_FILE = DATA_DIR / "stock_list.csv"
TRADING_PROFILE_FILE = DATA_DIR / "trading_profile.json"

REFRESH_SECONDS = 180
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
