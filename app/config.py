# =========================
# File: app/config.py
# =========================
from __future__ import annotations
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
