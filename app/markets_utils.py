# =========================
# File: app/markets_utils.py
# 說明：自動判斷市場 + 回補最近交易日 + 即時回補重試（環境變數可調）
# =========================
from __future__ import annotations

import os
import asyncio
import datetime as dt
from typing import Any, Dict, Generator, Optional, Tuple

from app.tw_markets import fetch_daily, fetch_realtime


def _env_int(name: str, default: int) -> int:
    """讀取整數環境變數；不合法時回預設"""
    try:
        v = int(os.getenv(name, "").strip() or default)
        return v if v >= 0 else default
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    """讀取浮點數環境變數；不合法時回預設"""
    try:
        v = float(os.getenv(name, "").strip() or default)
        return v if v >= 0 else default
    except Exception:
        return default


# 可配置常數：不同環境（節能/測試）可調整回溯範圍與重試成本
MAX_BACKTRACK_DAYS: int = _env_int("MARKETS_MAX_BACKTRACK_DAYS", 14)
REALTIME_MAX_MINUTES_DEFAULT: int = _env_int("REALTIME_MAX_MINUTES", 3)
REALTIME_INTERVAL_SEC_DEFAULT: float = _env_float("REALTIME_INTERVAL_SEC", 15.0)


def _iter_dates(base: dt.date, days: int) -> Generator[dt.date, None, None]:
    """從 base 往前回溯最多 days 天（含 base）。"""
    for delta in range(0, max(0, int(days)) + 1):
        yield base - dt.timedelta(days=delta)


async def auto_daily(
    symbol: str,
    date: Optional[dt.date] = None,
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    對單一日期依序嘗試 TWSE → TPEX。
    成功回傳 (市場, payload)，否則 (None, None)。
    """
    when = date or dt.date.today()
    for market in ("TWSE", "TPEX"):
        try:
            payload = await fetch_daily(symbol, market, when)
        except Exception:
            # 避免單一市場錯誤中斷整體流程
            continue
        if payload and payload.get("record"):
            return market, payload
    return None, None


async def find_last_daily(
    symbol: str,
    date: Optional[dt.date],
) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[dt.date]]:
    """
    回補日線：對 base, base-1, ... 呼叫 auto_daily（TWSE→TPEX），最多回溯 MAX_BACKTRACK_DAYS。
    回傳 (市場/None, payload/None, 使用到的日期/None)
    """
    base = date or dt.date.today()
    for d in _iter_dates(base, MAX_BACKTRACK_DAYS):
        market, payload = await auto_daily(symbol, d)
        if market and payload and payload.get("record"):
            return market, payload, d
    return None, None, None


def _has_tick(data: Optional[Dict[str, Any]]) -> bool:
    """
    判斷 TWSE MIS 回傳是否含有效成交價（欄位名稱可能為 price 或 z），時間欄位寬鬆檢查。
    """
    if not data:
        return False
    price = data.get("price") or data.get("z")
    t = data.get("time") or data.get("t") or data.get("ts")
    try:
        if price is None:
            return False
        s = str(price).strip().replace(",", "")
        if s in {"", "-", "—", "--", "NaN"}:
            return False
        float(s)
        return True if t is None else (str(t).strip() != "")
    except Exception:
        return False


async def find_last_realtime(
    symbol: str,
    max_minutes: Optional[int] = None,
    interval_sec: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    以「時間窗口重試」近似回補最近一筆即時報價（MIS 無歷史分鐘 API）。
    - max_minutes: 窗口分鐘（預設取 REALTIME_MAX_MINUTES；預設 3）
    - interval_sec: 重試間隔秒（預設取 REALTIME_INTERVAL_SEC；預設 15.0）
    成功回傳資料 dict，逾時回傳 None。
    """
    max_minutes = REALTIME_MAX_MINUTES_DEFAULT if max_minutes is None else max(0, int(max_minutes))
    interval_sec = REALTIME_INTERVAL_SEC_DEFAULT if interval_sec is None else max(0.2, float(interval_sec))

    attempts = max(1, int((max_minutes * 60) // interval_sec) + 1)
    for i in range(attempts):
        try:
            data = await fetch_realtime(symbol)
        except Exception:
            data = None

        if _has_tick(data):
            return data

        if i < attempts - 1:
            try:
                await asyncio.sleep(interval_sec)
            except Exception:
                break
    return None
