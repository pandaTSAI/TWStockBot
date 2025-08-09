# TW Stock Bot

查詢台股 **TWSE/TPEX** 日線與即時報價，並提供：

- 📈 漲幅/跌幅/成交量排行
- 🔁 自動回補最近交易日
- 🔍 模糊搜尋公司名稱或股票代碼
- 🧾 匯出排行、即時報價、日線資料為 CSV
- 🕓 每日盤後自動公告排行

---

## 🚀 安裝與執行

```bash
python -m venv .venv && . .venv/Scripts/activate  # Windows
# 或: source .venv/bin/activate                   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，至少填入 DISCORD_TOKEN
python main.py
