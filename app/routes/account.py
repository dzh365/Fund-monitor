"""
app/routes/account.py - 资金账户 CRUD
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app import get_db
from app.models import Account

router = APIRouter()


class AccountCreate(BaseModel):
    name: str
    remark: Optional[str] = ""


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    remark: Optional[str] = None


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db)):
    """获取所有资金账户"""
    accounts = db.query(Account).order_by(Account.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "remark": a.remark or "",
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "",
        }
        for a in accounts
    ]


@router.post("/accounts")
def create_account(data: AccountCreate, db: Session = Depends(get_db)):
    """添加资金账户"""
    existing = db.query(Account).filter(Account.name == data.name).first()
    if existing:
        raise HTTPException(400, f"账户「{data.name}」已存在")

    account = Account(name=data.name, remark=data.remark or "")
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"id": account.id, "name": account.name, "message": "创建成功"}


@router.put("/accounts/{account_id}")
def update_account(account_id: int, data: AccountUpdate, db: Session = Depends(get_db)):
    """编辑资金账户"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "账户不存在")

    if data.name is not None:
        dup = db.query(Account).filter(Account.name == data.name, Account.id != account_id).first()
        if dup:
            raise HTTPException(400, f"账户名「{data.name}」已被使用")
        account.name = data.name
    if data.remark is not None:
        account.remark = data.remark

    db.commit()
    return {"message": "更新成功"}


@router.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """删除资金账户（级联删除关联基金）"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(404, "账户不存在")

    db.delete(account)
    db.commit()
    return {"message": f"账户「{account.name}」及其下所有基金已删除"}
