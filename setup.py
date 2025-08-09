from __future__ import annotations
import sys
from pathlib import Path
import subprocess

# -------------------- templates --------------------
REQ_TXT = """python-dotenv>=1.0.1
discord.py>=2.4.0
"""

ENV_EXAMPLE = """DISCORD_TOKEN=your_discord_bot_token_here
"""

README_MD = """# TWSE/TPEX Stock Discord Bot (Step 1)
最小可運行範例，只有 `/ping` 指令。
"""

GITIGNORE = ".venv/\n__pycache__/\n*.pyc\n.env\n"

CONFIG_PY = """from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass(frozen=True)
class Settings:
    discord_token: str

def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("請先在 .env 設定 DISCORD_TOKEN")
    return Settings(discord_token=token)
"""

BOT_PY = """from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from app.config import load_settings

INTENTS = discord.Intents.default()
BOT = commands.Bot(command_prefix="!", intents=INTENTS)

@BOT.event
async def on_ready():
    try:
        await BOT.tree.sync()
    except Exception as e:
        print("Slash sync failed:", e)
    print(f"Logged in as {BOT.user} (ID: {BOT.user.id})")

@BOT.tree.command(name="ping", description="連線測試")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("pong")

if __name__ == "__main__":
    settings = load_settings()
    BOT.run(settings.discord_token)
"""

# -------------------- helpers --------------------
def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"[OK] 建立 {path}")


def create_venv(root: Path) -> None:
    try:
        subprocess.run([sys.executable, "-m", "venv", str(root/".venv")], check=True)
        print("[OK] 已建立 .venv")
    except subprocess.CalledProcessError as e:
        print("[WARN] 建立 venv 失敗：", e)


# -------------------- main flow --------------------
def main() -> None:
    print("=== TW Stock Bot Setup (Step 1) ===")
    root = Path.cwd()

    # 預設建立 venv
    create_venv(root)
    print("[提示] PowerShell 啟用 venv: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned; ./.venv/Scripts/Activate.ps1")

    # 預設不產生 token，使用者後續自行編輯 .env
    write_text(root/"requirements.txt", REQ_TXT)
    write_text(root/".env.example", ENV_EXAMPLE)
    write_text(root/"README.md", README_MD)
    write_text(root/".gitignore", GITIGNORE)

    # app package
    app_dir = root/"app"
    app_dir.mkdir(exist_ok=True)
    write_text(app_dir/"__init__.py", "")
    write_text(app_dir/"config.py", CONFIG_PY)
    write_text(root/"bot.py", BOT_PY)

    print("\n=== 建置完成 ===")
    print("接下來指令（PowerShell）：")
    print("Set-ExecutionPolicy -Scope CurrentUser RemoteSigned   # 第一次需要")
    print("./.venv/Scripts/Activate.ps1")
    print("pip install -r requirements.txt")
    print("copy .env.example .env  &&  notepad .env   # 貼上 DISCORD_TOKEN")
    print("python bot.py")
    print("\n* 第二步（稍後）：加入 TWSE/TPEX 抓取功能與指令。")


if __name__ == "__main__":
    main()
