# =========================
# File: README.md
# =========================
# TW Markets Discord Bot

查詢台股 **TWSE/TPEX** 日線、即時報價，以及 **漲/跌幅排行**、**成交量排行**。支援 **自動回補最近交易日**。

## 安裝

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env 填入 DISCORD_TOKEN
python bot.py