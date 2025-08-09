# =========================
# File: app/formatting.py
# =========================
from __future__ import annotations
from typing import Any, Dict, List
import discord

def _fmt_num(v: Any) -> str:
    try:
        if isinstance(v, (int, float)):
            return f"{int(v):,}" if float(v).is_integer() else f"{v:,}"
        if isinstance(v, str):
            s = v.replace(",", "").strip()
            if s.replace(".", "", 1).isdigit():
                f = float(s)
                return f"{int(f):,}" if f.is_integer() else f"{f:,}"
        return str(v)
    except Exception:
        return str(v)

def _lines_from_items(items: List[Dict[str, Any]], mode: str) -> List[str]:
    lines: List[str] = []
    for idx, it in enumerate(items, 1):
        tag = it.get("market", "")
        tag_s = f"[{tag}] " if tag else ""
        if mode == "movers":
            pct = it.get("change_pct")
            pct_str = f"{pct:.2f}%" if isinstance(pct, (int, float)) else str(pct)
            change = it.get("change")
            chg_str = (f"{change:+.2f}" if isinstance(change, (int, float)) else str(change)) if change is not None else "-"
            lines.append(
                f"**{idx}. {tag_s}{it['symbol']} {it.get('name','')}**\n"
                f"收盤 {it['close']:.2f}｜漲跌 {chg_str}｜漲幅 {pct_str}"
            )
        elif mode == "actives":
            vol = it.get("volume")
            val = it.get("value")
            vol_s = _fmt_num(vol) if vol is not None else "-"
            val_s = _fmt_num(val) if val is not None else "-"
            lines.append(
                f"**{idx}. {tag_s}{it['symbol']} {it.get('name','')}**\n"
                f"收盤 {it['close']:.2f}｜量 {vol_s}｜額 {val_s}"
            )
    return lines

def rank_embed(payload: Dict[str, Any], title: str, mode: str, color: int) -> discord.Embed:
    items: List[Dict[str, Any]] = payload.get("items", [])
    date_str = payload.get("date", "")
    source = payload.get("source", "")
    embed = discord.Embed(title=title, description=f"日期：{date_str}", color=color)
    lines = _lines_from_items(items, mode)
    embed.add_field(name="前幾名", value="\n".join(lines) if lines else "無資料", inline=False)
    if source:
        embed.set_footer(text=f"來源：{source}")
    return embed

def gainers_embed(payload: Dict[str, Any], title: str = "漲幅排行") -> discord.Embed:
    return rank_embed(payload, title, mode="movers", color=0xE74C3C)

def losers_embed(payload: Dict[str, Any], title: str = "跌幅排行") -> discord.Embed:
    return rank_embed(payload, title, mode="movers", color=0x95A5A6)

def actives_embed(payload: Dict[str, Any], title: str = "成交量排行") -> discord.Embed:
    return rank_embed(payload, title, mode="actives", color=0x3498DB)
