from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from config import APP_TIMEZONE, BASE_DIR, REFRESH_ON_OPEN, REFRESH_STATUS_FILE, current_on_open_refresh_slot
from modules.data_fetcher import read_fetch_cache
from modules.utils import now_text


RETRY_AFTER = timedelta(minutes=5)
SCRIPT_PATH = BASE_DIR / "scripts" / "update_live_cache.py"


def read_refresh_status() -> dict[str, Any]:
    if not REFRESH_STATUS_FILE.exists():
        return {}
    try:
        return json.loads(REFRESH_STATUS_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def write_refresh_status(status: dict[str, Any]) -> None:
    Path(REFRESH_STATUS_FILE).parent.mkdir(parents=True, exist_ok=True)
    REFRESH_STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        return parsed.replace(tzinfo=APP_TIMEZONE)
    except ValueError:
        return None


def _cache_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for name in ["market", "stocks", "sectors", "overseas"]:
        cached = read_fetch_cache(name)
        if cached is None:
            snapshot[name] = None
        else:
            snapshot[name] = {
                "source": cached.source,
                "update_time": cached.update_time,
                "warning": cached.warning,
            }
    return snapshot


def _is_successful_cache() -> bool:
    market = read_fetch_cache("market")
    stocks = read_fetch_cache("stocks")
    if market is None or stocks is None:
        return False
    return market.source != "示例数据" and stocks.source not in {"示例数据", "公开持仓兜底"}


def refresh_on_open_if_due(now: datetime | None = None, force: bool = False, source: str = "网页打开时刷新") -> dict[str, Any]:
    now = now or datetime.now(APP_TIMEZONE)
    slot = current_on_open_refresh_slot(now)
    if force and slot is None:
        slot = f"{now.date().isoformat()}:manual_test"
    previous = read_refresh_status()

    if not force and not REFRESH_ON_OPEN:
        return {**previous, "attempted_this_load": False, "reason": "open_refresh_disabled"}
    if not force and slot is None:
        return {**previous, "attempted_this_load": False, "reason": "before_first_refresh_time"}
    if not force and previous.get("slot") == slot and previous.get("ok") is True:
        return {**previous, "attempted_this_load": False, "reason": "slot_already_refreshed"}

    last_attempt = _parse_time(previous.get("attempt_time"))
    if not force and previous.get("slot") == slot and last_attempt and now - last_attempt < RETRY_AFTER:
        return {**previous, "attempted_this_load": False, "reason": "recent_attempt"}

    env = os.environ.copy()
    env["A_STOCK_USE_LIVE_DATA"] = "1"
    env["A_STOCK_USE_CACHED_DATA"] = "0"

    status: dict[str, Any] = {
        "slot": slot,
        "attempt_time": now_text(),
        "attempted_this_load": True,
        "ok": False,
        "source": source,
    }
    try:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=str(BASE_DIR),
            env=env,
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
        status.update(
            {
                "returncode": completed.returncode,
                "stdout": completed.stdout[-3000:],
                "stderr": completed.stderr[-3000:],
                "cache": _cache_snapshot(),
            }
        )
        status["ok"] = completed.returncode == 0 and _is_successful_cache()
        if not status["ok"]:
            status["error"] = "刷新脚本已运行，但没有生成有效的 market/stocks 真实缓存。"
    except Exception as exc:  # noqa: BLE001
        status.update({"error": f"{type(exc).__name__}: {exc}", "cache": _cache_snapshot()})

    write_refresh_status(status)
    return status


def refresh_status_caption(status: dict[str, Any]) -> str:
    if not status:
        return "网页打开刷新：暂无运行记录"
    slot = status.get("slot", "暂无刷新窗口")
    attempt_time = status.get("attempt_time", "未知时间")
    if status.get("ok"):
        return f"{status.get('source', '网页打开刷新')}：已执行成功 · {attempt_time} · {slot}"
    if status.get("attempted_this_load"):
        return f"{status.get('source', '网页打开刷新')}：本次已尝试但失败 · {attempt_time} · {status.get('error', '原因未知')}"
    reason_map = {
        "before_first_refresh_time": "未到 11:30/14:30",
        "slot_already_refreshed": "本时段已刷新",
        "recent_attempt": "5 分钟内已尝试，暂不重复请求",
        "open_refresh_disabled": "已关闭",
    }
    reason = reason_map.get(str(status.get("reason")), str(status.get("reason", "原因未知")))
    return f"网页打开刷新：未执行 · {reason} · 最近记录 {attempt_time} · {slot}"
