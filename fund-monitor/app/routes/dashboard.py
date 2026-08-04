"""
app/routes/dashboard.py - 仪表盘路由
首页 + API
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import get_db, templates
from app.models import Account, Fund, FundNavHistory
from app.services.calculator import calc_global_summary

router = APIRouter()


# ─── 页面 ───────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def dashboard_page(request: Request):
    """首页仪表盘"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ─── API ────────────────────────────────────────────────

@router.get("/api/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    """全局统计数据"""
    summary = calc_global_summary(db)
    return {
        "total_accounts": summary["total_accounts"],
        "total_funds": summary["total_funds"],
        "global_cost": summary["global_cost"],
        "global_market_value": summary["global_market_value"],
        "global_profit": summary["global_profit"],
        "global_profit_pct": summary["global_profit_pct"],
    }


@router.get("/api/dashboard/account-stats")
def account_stats(db: Session = Depends(get_db)):
    """各账户统计数据"""
    summary = calc_global_summary(db)
    return summary["accounts"]


@router.get("/api/dashboard/trend")
def asset_trend(days: int = 30, db: Session = Depends(get_db)):
    """
    资产趋势数据：取每天最后一次净值快照，
    按当日持仓市值汇总，返回近 N 天数据
    """
    cutoff = datetime.now() - timedelta(days=days)
    histories = (
        db.query(FundNavHistory)
        .filter(FundNavHistory.fetched_at >= cutoff)
        .order_by(FundNavHistory.fetched_at.asc())
        .all()
    )
    funds = db.query(Fund).all()
    share_map = {f.fund_code: f.shares for f in funds}

    # 按日期聚合
    daily: dict[str, float] = {}
    for h in histories:
        date_key = h.nav_date or h.fetched_at.strftime("%Y-%m-%d")
        mv = h.nav * share_map.get(h.fund_code, 0)
        daily[date_key] = daily.get(date_key, 0) + mv

    dates = sorted(daily.keys())
    return {
        "dates": dates,
        "values": [round(daily[d], 2) for d in dates],
    }
