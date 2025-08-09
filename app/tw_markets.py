# =========================
# File: app/tw_markets.py
# =========================
from __future__ import annotations
import datetime as dt
import json
import re
from typing import Any, Dict, List, Optional

import aiohttp

ROC_START_YEAR = 1911


class HttpError(RuntimeError):
    pass


def _roc_date_str(d: dt.date) -> str:
    roc_year = d.year - ROC_START_YEAR
    return f"{roc_year:03d}/{d.month:02d}/{d.day:02d}"


def _roc_year_month(d: dt.date) -> str:
    roc_year = d.year - ROC_START_YEAR
    return f"{roc_year:03d}/{d.month:02d}"


def _normalize_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    return re.sub(r"[^0-9A-Z]", "", s)


def _parse_number(x: str) -> Optional[float]:
    try:
        x = x.replace(",", "").strip()
        if x in ("--", "-", "NaN", ""):
            return None
        return float(x)
    except Exception:
        return None


class TWSEClient:
    BASE = "https://www.twse.com.tw"
    MIS = "https://mis.twse.com.tw"

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def stock_day(self, symbol: str, date: dt.date) -> Dict[str, Any]:
        symbol = _normalize_symbol(symbol)
        url = (
            f"{self.BASE}/exchangeReport/STOCK_DAY?response=json&date="
            f"{date:%Y%m%d}&stockNo={symbol}"
        )
        async with self.session.get(url) as resp:
            if resp.status != 200:
                raise HttpError(f"TWSE stock_day HTTP {resp.status}")
            data = await resp.json(content_type=None)
        if data.get("stat") not in {"OK", "很抱歉，沒有符合條件的資料!"}:
            raise HttpError(f"TWSE unexpected stat: {data.get('stat')}")
        return data

    async def realtime(self, symbol: str) -> Optional[Dict[str, Any]]:
        symbol = _normalize_symbol(symbol)
        ex_ch = f"tse_{symbol}.tw"
        url = f"{self.MIS}/stock/api/getStockInfo.jsp?ex_ch={ex_ch}&json=1&delay=0"
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return None
                text = await resp.text()
                data = json.loads(text)
        except Exception:
            return None
        arr = data.get("msgArray") or []
        return arr[0] if arr else None


class TPEXClient:
    BASE = "https://www.tpex.org.tw"

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def stock_day(self, symbol: str, date: dt.date) -> Dict[str, Any]:
        symbol = _normalize_symbol(symbol)
        roc_ym = _roc_year_month(date)
        url = (
            f"{self.BASE}/web/stock/aftertrading/daily_trading_info/"
            f"st43_result.php?l=zh-tw&d={roc_ym}&stkno={symbol}"
        )
        async with self.session.get(url) as resp:
            if resp.status != 200:
                raise HttpError(f"TPEX stock_day HTTP {resp.status}")
            data = await resp.json(content_type=None)
        return data


async def pick_latest_record_from_twse_day(data: Dict[str, Any], target: dt.date) -> Optional[Dict[str, Any]]:
    rows: List[List[str]] = data.get("data") or []
    wanted = _roc_date_str(target)
    for row in rows:
        if not row:
            continue
        if row[0] == wanted:
            return {
                "date": row[0],
                "volume": _parse_number(row[1]),
                "turnover": _parse_number(row[2]),
                "open": _parse_number(row[3]),
                "high": _parse_number(row[4]),
                "low": _parse_number(row[5]),
                "close": _parse_number(row[6]),
                "change": row[7],
                "transactions": _parse_number(row[8]),
            }
    return None


async def pick_latest_record_from_tpex_day(data: Dict[str, Any], target: dt.date) -> Optional[Dict[str, Any]]:
    # TPEX: [日期, 成交仟股, 成交仟元, 開盤, 最高, 最低, 收盤, 漲跌, 筆數]
    wanted = _roc_date_str(target)
    rows: List[List[str]] = data.get("aaData") or data.get("data") or []
    for row in rows:
        if not row:
            continue
        if row[0] == wanted:
            vol = _parse_number(row[1])
            amt = _parse_number(row[2])
            return {
                "date": row[0],
                "volume": vol * 1000 if vol is not None else None,
                "turnover": amt * 1000 if amt is not None else None,
                "open": _parse_number(row[3]),
                "high": _parse_number(row[4]),
                "low": _parse_number(row[5]),
                "close": _parse_number(row[6]),
                "change": row[7],
                "transactions": _parse_number(row[8]),
            }
    return None


async def fetch_daily(symbol: str, market: str, date: Optional[dt.date] = None) -> Dict[str, Any]:
    symbol = _normalize_symbol(symbol)
    market = market.upper().strip()
    date = date or dt.date.today()

    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as sess:
        if market == "TWSE":
            twse = TWSEClient(sess)
            raw = await twse.stock_day(symbol, date)
            rec = await pick_latest_record_from_twse_day(raw, date)
            return {
                "market": "TWSE",
                "symbol": symbol,
                "date": date.isoformat(),
                "raw_date": rec.get("date") if rec else None,
                "record": rec,
            }
        elif market == "TPEX":
            tpex = TPEXClient(sess)
            raw = await tpex.stock_day(symbol, date)
            rec = await pick_latest_record_from_tpex_day(raw, date)
            return {
                "market": "TPEX",
                "symbol": symbol,
                "date": date.isoformat(),
                "raw_date": rec.get("date") if rec else None,
                "record": rec,
            }
        else:
            raise ValueError("market must be 'TWSE' or 'TPEX'")


async def fetch_realtime(symbol: str) -> Optional[Dict[str, Any]]:
    async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as sess:
        twse = TWSEClient(sess)
        return await twse.realtime(symbol)
