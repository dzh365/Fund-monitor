"""
app/routes/push.py - 推送日志 + 手动触发
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import get_db
from app.models import PushLog, Setting
from app.services.calculator import calc_global_summary
from app.services.push_service import build_report, send_report

router = APIRouter()


@router.get("/push/logs")
def push_logs(page: int = 1, size: int = 20, db: Session = Depends(get_db)):
    """推送日志列表"""
    total = db.query(PushLog).count()
    logs = (
        db.query(PushLog)
        .order_by(PushLog.push_time.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [
            {
                "id": log.id,
                "push_time": log.push_time.strftime("%Y-%m-%d %H:%M:%S") if log.push_time else "",
                "status": log.status,
                "content": log.content or "",
                "error_msg": log.error_msg or "",
            }
            for log in logs
        ],
    }


@router.post("/push/trigger")
def trigger_push(db: Session = Depends(get_db)):
    """手动触发一次推送"""
    # 读取 sendkey
    setting = db.query(Setting).filter(Setting.key == "serverchan_sendkey").first()
    sendkey = setting.value if setting else ""

    summary = calc_global_summary(db)
    if summary["total_funds"] == 0:
        return {"success": False, "message": "无持仓基金，无需推送"}

    title, body = build_report(summary)
    result = send_report(sendkey, title, body)
    return result
