"""
config.py - 配置管理
从 .env 文件加载配置项
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "16888"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fund_monitor.db")
    SERVERCHAN_SENDKEY: str = os.getenv("SERVERCHAN_SENDKEY", "")
    PUSH_TIME: str = os.getenv("PUSH_TIME", "20:00")
    SKIP_WEEKEND: bool = os.getenv("SKIP_WEEKEND", "true").lower() == "true"
