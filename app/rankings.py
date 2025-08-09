# =========================
# File: app/rankings.py
# =========================
from __future__ import annotations
from typing import Any, Dict, List, Optional
import aiohttp
import datetime as dt

CACHE: Dict[str, Any] = {}
CACHE_TTL = 60


def _filter_items(items: List[Dict[str, Any]], exclude_warrants: bool, exclude_etf: bool) -> List[Dict[str, Any]]:
    result = []
    for it in items:
        sym = it.get("symbol", "")
        name = it.get("name", "")
        if exclude_warrants and any(x in name for x in ("購", "售", "牛", "熊")):
            continue
        if exclude_etf and ("ETF" in name or sym.startswith("00")):
            continue
        result.append(it)
    return result


async def _fetch_market_data(market: str) -> List[Dict[str, Any]]:
    # 假 API 範例，實際要改為 TWSE/TPEX 即時排行 API
    url = f"https://example.com/{market}/rankings"
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
            return await resp.json()


async def _get_rank(
    rank_type: str,
    market: str,
    limit: int,
    exclude_warrants: bool,
    exclude_etf: bool,
) -> Dict[str, Any]:
    key = f"{rank_type}:{market}:{exclude_warrants}:{exclude_etf}"
    now = dt.datetime.now().timestamp()
    if key in CACHE and now - CACHE[key]["time"] < CACHE_TTL:
        return CACHE[key]["data"]

    if market == "ALL":
        markets = ["TWSE", "TPEX"]
    else:
        markets = [market]

    all_items = []
    for m in markets:
        items = await _fetch_market_data(m)
        items = _filter_items(items, exclude_warrants, exclude_etf)
        all_items.extend(items)

    if rank_type == "gainers":
        all_items.sort(key=lambda x: x.get("change_pct", 0), reverse=True)
    elif rank_type == "losers":
        all_items.sort(key=lambda x: x.get("change_pct", 0))
    elif rank_type == "actives":
        all_items.sort(key=lambda x: x.get("volume", 0), reverse=True)

    result = {
        "date": dt.date.today().isoformat(),
        "items": all_items[:limit],
        "source": "TWSE/TPEX",
    }
    CACHE[key] = {"time": now, "data": result}
    return result


async def top_gainers(**kwargs) -> Dict[str, Any]:
    return await _get_rank("gainers", **kwargs)


async def top_losers(**kwargs) -> Dict[str, Any]:
    return await _get_rank("losers", **kwargs)


async def most_actives(**kwargs) -> Dict[str, Any]:
    return await _get_rank("actives", **kwargs)
