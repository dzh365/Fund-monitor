"""
app/services/calculator.py - 盈亏计算服务
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models import Fund, Account, FundNavHistory
from app.services.fund_api import search_fund


def calc_fund_profit(fund: Fund, latest_nav: float) -> dict:
    """
    计算单只基金盈亏

    返回:
    {
        "fund_id": 1,
        "fund_code": "000001",
        "fund_name": "华夏成长混合",
        "buy_price": 1.0,
        "shares": 1000,
        "latest_nav": 1.2345,
        "cost": 1000.0,
        "market_value": 1234.5,
        "profit": 234.5,
        "profit_pct": 23.45,
        "change_pct": 0.12,
        "nav_date": "2024-01-15",
    }
    """
    cost = fund.buy_price * fund.shares
    market_value = latest_nav * fund.shares
    profit = market_value - cost
    profit_pct = ((latest_nav - fund.buy_price) / fund.buy_price * 100) if fund.buy_price else 0

    return {
        "fund_id": fund.id,
        "fund_code": fund.fund_code,
        "fund_name": fund.fund_name or "未知",
        "buy_price": fund.buy_price,
        "shares": fund.shares,
        "buy_date": fund.buy_date or "",
        "latest_nav": latest_nav,
        "cost": round(cost, 2),
        "market_value": round(market_value, 2),
        "profit": round(profit, 2),
        "profit_pct": round(profit_pct, 2),
    }


def calc_account_summary(db: Session, account_id: int, nav_cache: dict = None) -> dict:
    """
    计算某账户下所有基金的盈亏汇总

    nav_cache: { "基金代码": 最新净值, ... } 避免重复请求

    返回:
    {
        "account_id": 1,
        "account_name": "支付宝",
        "total_cost": 10000,
        "total_market_value": 12345,
        "total_profit": 2345,
        "total_profit_pct": 23.45,
        "fund_count": 3,
        "funds": [...]
    }
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {}

    funds = db.query(Fund).filter(Fund.account_id == account_id).all()
    if nav_cache is None:
        nav_cache = {}

    fund_details = []
    total_cost = 0
    total_market_value = 0

    for fund in funds:
        code = fund.fund_code
        # 从缓存取净值，没有则请求
        if code not in nav_cache:
            try:
                info = search_fund(code)
                nav_cache[code] = info
            except Exception:
                nav_cache[code] = None

        nav_info = nav_cache.get(code)
        if nav_info:
            latest_nav = nav_info["nav"]
            change_pct = nav_info.get("change_pct", 0)
            nav_date = nav_info.get("nav_date", "")
            # 更新基金名称（可能之前为空）
            if not fund.fund_name and nav_info.get("fund_name"):
                fund.fund_name = nav_info["fund_name"]
                db.commit()
        else:
            latest_nav = fund.buy_price
            change_pct = 0
            nav_date = ""

        detail = calc_fund_profit(fund, latest_nav)
        detail["change_pct"] = change_pct
        detail["nav_date"] = nav_date
        fund_details.append(detail)
        total_cost += detail["cost"]
        total_market_value += detail["market_value"]

    total_profit = total_market_value - total_cost
    total_profit_pct = (total_profit / total_cost * 100) if total_cost else 0

    return {
        "account_id": account.id,
        "account_name": account.name,
        "account_remark": account.remark or "",
        "total_cost": round(total_cost, 2),
        "total_market_value": round(total_market_value, 2),
        "total_profit": round(total_profit, 2),
        "total_profit_pct": round(total_profit_pct, 2),
        "fund_count": len(funds),
        "funds": fund_details,
    }


def calc_global_summary(db: Session) -> dict:
    """
    全局汇总：所有账户合计市值、合计盈亏、综合收益率
    """
    accounts = db.query(Account).all()
    nav_cache = {}

    account_summaries = []
    global_cost = 0
    global_market_value = 0

    for acc in accounts:
        summary = calc_account_summary(db, acc.id, nav_cache)
        if summary:
            account_summaries.append(summary)
            global_cost += summary["total_cost"]
            global_market_value += summary["total_market_value"]

    global_profit = global_market_value - global_cost
    global_profit_pct = (global_profit / global_cost * 100) if global_cost else 0
    total_funds = sum(s["fund_count"] for s in account_summaries)

    return {
        "total_accounts": len(accounts),
        "total_funds": total_funds,
        "global_cost": round(global_cost, 2),
        "global_market_value": round(global_market_value, 2),
        "global_profit": round(global_profit, 2),
        "global_profit_pct": round(global_profit_pct, 2),
        "accounts": account_summaries,
    }
