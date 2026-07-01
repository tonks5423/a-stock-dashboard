from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

import pandas as pd


def now_text() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def score_label(score: float, levels: tuple[tuple[float, str], ...]) -> str:
    for threshold, label in levels:
        if score >= threshold:
            return label
    return levels[-1][1]


def pct_text(value: float) -> str:
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def amount_yi(value: float) -> float:
    return round(safe_float(value) / 100_000_000, 2)
