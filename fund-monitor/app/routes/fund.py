"""
app/routes/fund.py - 基金 CRUD + 查询
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app import get_db
from app.models import Fund, Account, FundNavHistory
from app.services.fund_api import search_fund, validate_fund_code
from app.services.calculator import calc_fund_profit

router = APIRouter()


class FundCreate(BaseModel):
    fund_code: str
    buy_price: float
    shares: float
    buy_date: Optional[str] = ""


class FundUpdate(BaseModel):
    buy_price: Optional[float] = None
    shares: Optional[float] = None
    buy_date: Optional[str] = None


# ─── 账户下基金列表 ─────────────────────────────────────

@router.get("/accounts/{account_id}/funds")
def list_funds(account_id: int, db: Session = Depends(get_db)):
    """获取某账户下的基金列表（含最新净值和盈亏）"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "账户不存在")

    funds = db.query(Fund).filter(Fund.account_id == account_id).all()
    result = []
    for fund in funds:
        # 查最新净值快照
        latest = (
            db.query(FundNavHistory)
            .filter(FundNavHistory.fund_code == fund.fund_code)
            .order_by(FundNavHistory.fetched_at.desc())
            .first()
        )
        latest_nav = latest.nav if latest else fund.buy_price
        nav_date = latest.nav_date if latest else ""

        detail = calc_fund_profit(fund, latest_nav)
        detail["nav_date"] = nav_date
        result.append(detail)

    return result


@router.post("/accounts/{account_id}/funds")
def add_fund(account_id: int, data: FundCreate, db: Session = Depends(get_db)):
    """向账户添加基金"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "账户不存在")

    if not validate_fund_code(data.fund_code):
        raise HTTPException(400, "基金代码格式错误，应为6位数字")

    if data.buy_price <= 0 or data.shares <= 0:
        raise HTTPException(400, "买入净值和持有份额必须大于0")

    # 查询基金名称
    fund_name = ""
    try:
        info = search_fund(data.fund_code)
        fund_name = info.get("fund_name", "")
    except Exception:
        pass  # 查不到名称不影响添加

    fund = Fund(
        account_id=account_id,
        fund_code=data.fund_code,
        fund_name=fund_name,
        buy_price=data.buy_price,
        shares=data.shares,
        buy_date=data.buy_date or "",
    )
    db.add(fund)
    db.commit()
    db.refresh(fund)

    return {
        "id": fund.id,
        "fund_code": fund.fund_code,
        "fund_name": fund.fund_name,
        "message": "添加成功",
    }


@router.put("/funds/{fund_id}")
def update_fund(fund_id: int, data: FundUpdate, db: Session = Depends(get_db)):
    """编辑基金持仓信息"""
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(404, "基金记录不存在")

    if data.buy_price is not None:
        if data.buy_price <= 0:
            raise HTTPException(400, "买入净值必须大于0")
        fund.buy_price = data.buy_price
    if data.shares is not None:
        if data.shares <= 0:
            raise HTTPException(400, "持有份额必须大于0")
        fund.shares = data.shares
    if data.buy_date is not None:
        fund.buy_date = data.buy_date

    db.commit()
    return {"message": "更新成功"}


@router.delete("/funds/{fund_id}")
def delete_fund(fund_id: int, db: Session = Depends(get_db)):
    """删除基金"""
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(404, "基金记录不存在")

    db.delete(fund)
    db.commit()
    return {"message": "删除成功"}


# ─── 基金搜索 ───────────────────────────────────────────

@router.get("/fund/search")
def fund_search(code: str, db: Session = Depends(get_db)):
    """根据基金代码查询基金信息"""
    if not validate_fund_code(code):
        raise HTTPException(400, "基金代码格式错误，应为6位数字")

    try:
        info = search_fund(code)
        return info
    except Exception as e:
        raise HTTPException(400, f"查询失败: {e}")
