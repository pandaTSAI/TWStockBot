# =========================
# File: bot.py
# =========================
from __future__ import annotations
import datetime as dt
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from app.config import load_settings
from app.tw_markets import fetch_daily, fetch_realtime
from app.formatting import (
    ohlc_embed,
    realtime_embed,
    gainers_embed,
    losers_embed,
    actives_embed,
)
from app.markets_utils import auto_daily, find_last_daily, find_last_realtime
from app.rankings import (
    top_gainers as svc_top_gainers,
    top_losers as svc_top_losers,
    most_actives as svc_most_actives,
)

INTENTS = discord.Intents.default()
BOT = commands.Bot(command_prefix="!", intents=INTENTS)


def _parse_date(s: Optional[str]) -> Optional[dt.date]:
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise commands.BadArgument("日期格式錯誤，請用 YYYY-MM-DD。")


@BOT.event
async def on_ready():
    try:
        await BOT.tree.sync()
    except Exception as e:
        print("Slash sync failed:", e)
    print(f"Logged in as {BOT.user} (ID: {BOT.user.id})")


@BOT.tree.command(name="search", description="自動判斷市場（可回補最近有資料的交易日）")
@app_commands.describe(
    symbol="股票代碼，例如 2330",
    date="日期 YYYY-MM-DD，預設今天",
    auto_previous="若無資料，自動往前回補（預設開）",
)
async def search_cmd(
    interaction: discord.Interaction,
    symbol: str,
    date: Optional[str] = None,
    auto_previous: Optional[bool] = True,
):
    await interaction.response.defer(thinking=True)
    try:
        d = _parse_date(date)
        if auto_previous:
            market, payload, used_date = await find_last_daily(symbol, d)
            if not market:
                await interaction.followup.send("找不到最近的日線資料。")
                return
            embed = ohlc_embed(f"{symbol} {market} 日線", payload, actual_date=str(used_date))
            await interaction.followup.send(embed=embed)
        else:
            market, payload = await auto_daily(symbol, d)
            if not market:
                await interaction.followup.send("找不到該日期的資料。")
                return
            embed = ohlc_embed(f"{symbol} {market} 日線", payload)
            await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"查詢失敗：{e}")


@BOT.tree.command(name="daily", description="查詢日線 (TWSE/TPEX)")
@app_commands.describe(
    symbol="股票代碼",
    market="TWSE 或 TPEX",
    date="日期 YYYY-MM-DD，預設今天",
)
@app_commands.choices(market=[
    app_commands.Choice(name="TWSE", value="TWSE"),
    app_commands.Choice(name="TPEX", value="TPEX"),
])
async def daily(
    interaction: discord.Interaction,
    symbol: str,
    market: app_commands.Choice[str],
    date: Optional[str] = None,
):
    await interaction.response.defer(thinking=True)
    try:
        d = _parse_date(date)
        payload = await fetch_daily(symbol, market.value, d)
        embed = ohlc_embed(f"{symbol} {market.value} 日線", payload)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"查詢失敗：{e}")


@BOT.tree.command(name="realtime", description="查詢即時報價 (TWSE, 自動回補)")
@app_commands.describe(
    symbol="股票代碼",
    max_minutes="回補分鐘數 (預設環境值, 1-10)",
    interval_sec="重試間隔秒 (預設環境值, 2-30)",
)
async def realtime(
    interaction: discord.Interaction,
    symbol: str,
    max_minutes: Optional[int] = None,
    interval_sec: Optional[float] = None,
):
    await interaction.response.defer(thinking=True)
    try:
        data = await fetch_realtime(symbol)
        if not data:
            data = await find_last_realtime(symbol, max_minutes=max_minutes, interval_sec=interval_sec)
        if not data:
            await interaction.followup.send("找不到有效的即時報價。")
            return
        embed = realtime_embed(symbol, data)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"查詢失敗：{e}")


# ---- 排行指令 ----
MARKET_CHOICES = [
    app_commands.Choice(name="TWSE", value="TWSE"),
    app_commands.Choice(name="TPEX", value="TPEX"),
    app_commands.Choice(name="ALL", value="ALL"),
]

def _rank_common_args():
    return dict(
        market=app_commands.describe(market="市場 (TWSE/TPEX/ALL)"),
        limit=app_commands.describe(limit="顯示前 N 名 (1-50, 預設 10)"),
        exclude_warrants=app_commands.describe(exclude_warrants="排除權證/牛熊證 (預設 True)"),
        exclude_etf=app_commands.describe(exclude_etf="排除 ETF (預設 True)"),
    )


@BOT.tree.command(name="top_gainers", description="漲幅排行")
@app_commands.choices(market=MARKET_CHOICES)
async def top_gainers(
    interaction: discord.Interaction,
    market: app_commands.Choice[str],
    limit: Optional[int] = 10,
    exclude_warrants: bool = True,
    exclude_etf: bool = True,
):
    await interaction.response.defer(thinking=True)
    try:
        payload = await svc_top_gainers(
            market=market.value,
            limit=limit,
            exclude_warrants=exclude_warrants,
            exclude_etf=exclude_etf,
        )
        await interaction.followup.send(embed=gainers_embed(payload))
    except Exception as e:
        await interaction.followup.send(f"查詢失敗：{e}")


@BOT.tree.command(name="top_losers", description="跌幅排行")
@app_commands.choices(market=MARKET_CHOICES)
async def top_losers(
    interaction: discord.Interaction,
    market: app_commands.Choice[str],
    limit: Optional[int] = 10,
    exclude_warrants: bool = True,
    exclude_etf: bool = True,
):
    await interaction.response.defer(thinking=True)
    try:
        payload = await svc_top_losers(
            market=market.value,
            limit=limit,
            exclude_warrants=exclude_warrants,
            exclude_etf=exclude_etf,
        )
        await interaction.followup.send(embed=losers_embed(payload))
    except Exception as e:
        await interaction.followup.send(f"查詢失敗：{e}")


@BOT.tree.command(name="actives", description="成交量排行")
@app_commands.choices(market=MARKET_CHOICES)
async def actives(
    interaction: discord.Interaction,
    market: app_commands.Choice[str],
    limit: Optional[int] = 10,
    exclude_warrants: bool = True,
    exclude_etf: bool = True,
):
    await interaction.response.defer(thinking=True)
    try:
        payload = await svc_most_actives(
            market=market.value,
            limit=limit,
            exclude_warrants=exclude_warrants,
            exclude_etf=exclude_etf,
        )
        await interaction.followup.send(embed=actives_embed(payload))
    except Exception as e:
        await interaction.followup.send(f"查詢失敗：{e}")


if __name__ == "__main__":
    settings = load_settings()
    BOT.run(settings.discord_token)
