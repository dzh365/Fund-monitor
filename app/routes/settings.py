"""
app/routes/settings.py - 系统设置
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app import get_db
from app.models import Setting
from config import Config

router = APIRouter()

# 默认设置项
DEFAULTS = {
    "serverchan_sendkey": "",
    "push_time": "20:00",
    "skip_weekend": "true",
    "push_enabled": "true",
}


def _get_setting(db: Session, key: str) -> str:
    s = db.query(Setting).filter(Setting.key == key).first()
    return s.value if s else DEFAULTS.get(key, "")


def _set_setting(db: Session, key: str, value: str):
    s = db.query(Setting).filter(Setting.key == key).first()
    if s:
        s.value = value
    else:
        db.add(Setting(key=key, value=value))
    db.commit()


class SettingsUpdate(BaseModel):
    serverchan_sendkey: Optional[str] = None
    push_time: Optional[str] = None
    skip_weekend: Optional[bool] = None
    push_enabled: Optional[bool] = None


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    """获取系统设置"""
    return {
        "serverchan_sendkey": _get_setting(db, "serverchan_sendkey"),
        "push_time": _get_setting(db, "push_time"),
        "skip_weekend": _get_setting(db, "skip_weekend") == "true",
        "push_enabled": _get_setting(db, "push_enabled") == "true",
    }


@router.put("/settings")
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    """更新系统设置"""
    if data.serverchan_sendkey is not None:
        _set_setting(db, "serverchan_sendkey", data.serverchan_sendkey)
    if data.push_time is not None:
        _set_setting(db, "push_time", data.push_time)
    if data.skip_weekend is not None:
        _set_setting(db, "skip_weekend", "true" if data.skip_weekend else "false")
    if data.push_enabled is not None:
        _set_setting(db, "push_enabled", "true" if data.push_enabled else "false")

    return {"message": "设置已保存"}


@router.post("/settings/test-push")
def test_push(db: Session = Depends(get_db)):
    """测试 Server酱 推送"""
    from app.services.push_service import send_report
    sendkey = _get_setting(db, "serverchan_sendkey")
    if not sendkey:
        return {"success": False, "message": "请先配置 Server酱 SendKey"}

    result = send_report(
        sendkey,
        "🔔 基金监控系统 - 推送测试",
        "✅ 如果你收到这条消息，说明 Server酱 推送配置成功！\n\n"
        f"_发送时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
    )
    return result
