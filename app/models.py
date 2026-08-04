"""
app/models.py - SQLAlchemy 数据模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app import Base


class Account(Base):
    """资金账户（对应不同基金平台）"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    remark = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.now)

    funds = relationship("Fund", back_populates="account", cascade="all, delete-orphan")


class Fund(Base):
    """基金持仓记录"""
    __tablename__ = "funds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    fund_code = Column(String(10), nullable=False)
    fund_name = Column(String(200), default="")
    buy_price = Column(Float, nullable=False)
    shares = Column(Float, nullable=False)
    buy_date = Column(String(20), default="")
    created_at = Column(DateTime, default=datetime.now)

    account = relationship("Account", back_populates="funds")


class FundNavHistory(Base):
    """历史净值快照"""
    __tablename__ = "nav_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fund_code = Column(String(10), nullable=False, index=True)
    nav = Column(Float, nullable=False)
    nav_date = Column(String(20), nullable=False)
    fetched_at = Column(DateTime, default=datetime.now)


class PushLog(Base):
    """推送日志"""
    __tablename__ = "push_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    push_time = Column(DateTime, default=datetime.now)
    status = Column(String(20), nullable=False)  # success / failed
    content = Column(Text, default="")
    error_msg = Column(Text, default="")


class Setting(Base):
    """系统设置（键值对）"""
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, default="")
