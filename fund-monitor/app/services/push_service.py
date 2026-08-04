"""
app/services/push_service.py - Server酱推送服务
"""

import logging
from datetime import datetime

import httpx

from config import Config
from app.models import PushLog
from app import SessionLocal

logger = logging.getLogger(__name__)

SERVERCHAN_API = "https://sctapi.ftqq.com/{sendkey}.send"


def build_report(summary: dict) -> tuple[str, str]:
    """
    根据全局汇总数据构建推送报告

    参数:
        summary: calc_global_summary() 的返回值

    返回:
        (标题, Markdown正文)
    """
    global_profit = summary["global_profit"]
    sign = "+" if global_profit >= 0 else ""
    date_str = datetime.now().strftime("%Y-%m-%d")
    title = f"基金日报 | {date_str} | 总盈亏：{sign}¥{global_profit:,.2f}"

    lines = []
    lines.append(f"📅 **{date_str}**\n")

    for acc in summary.get("accounts", []):
        acc_profit = acc["total_profit"]
        acc_pct = acc["total_profit_pct"]
        acc_sign = "+" if acc_profit >= 0 else ""
        acc_emoji = "📈" if acc_profit >= 0 else "📉"

        lines.append(f"---")
        acc_color = "🔴" if acc_profit >= 0 else "🟢"
        lines.append(
            f"**{acc_emoji} 【{acc['account_name']}】** "
            f"持仓市值 ¥{acc['total_market_value']:,.2f} | "
            f"盈亏 {acc_color} {acc_sign}¥{acc_profit:,.2f}（{acc_sign}{acc_pct:.2f}%）"
        )
        lines.append("")

        for fund in acc.get("funds", []):
            fp = fund["profit"]
            fp_sign = "+" if fp >= 0 else ""
            color = "🔴" if fp >= 0 else "🟢"
            lines.append(
                f"· {fund['fund_name']} | "
                f"净值 {fund['latest_nav']:.4f} | "
                f"{color} {fp_sign}¥{fp:,.2f}（{fp_sign}{fund['profit_pct']:.2f}%）"
            )
        lines.append("")

    lines.append("---")
    g_sign = "+" if global_profit >= 0 else ""
    g_emoji = "📈" if global_profit >= 0 else "📉"
    g_color = "🔴" if global_profit >= 0 else "🟢"
    lines.append(
        f"{g_emoji} **合计：市值 ¥{summary['global_market_value']:,.2f} | "
        f"总盈亏 {g_color} {g_sign}¥{global_profit:,.2f}（{g_sign}{summary['global_profit_pct']:.2f}%）**"
    )

    body = "\n".join(lines)
    return title, body


def send_report(sendkey: str, title: str, body: str) -> dict:
    """
    调用 Server酱 API 推送消息

    返回:
        {"success": bool, "message": str}
    """
    if not sendkey or sendkey.startswith("your-sendkey"):
        msg = "Server酱 SendKey 未配置"
        logger.warning(msg)
        _log_push("failed", title, msg)
        return {"success": False, "message": msg}

    url = SERVERCHAN_API.format(sendkey=sendkey)
    payload = {"title": title, "desp": body}

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.post(url, data=payload)
            resp.raise_for_status()
            data = resp.json()

        code = data.get("code", -1)
        message = data.get("message", "未知")

        if code == 0:
            logger.info(f"推送成功: {message}")
            _log_push("success", title, "")
            return {"success": True, "message": message}
        else:
            logger.error(f"推送失败: {message}")
            _log_push("failed", title, message)
            return {"success": False, "message": message}

    except Exception as e:
        msg = str(e)
        logger.error(f"推送异常: {msg}")
        _log_push("failed", title, msg)
        return {"success": False, "message": msg}


def _log_push(status: str, content: str, error_msg: str = "") -> None:
    """记录推送日志"""
    db = SessionLocal()
    try:
        log = PushLog(
            status=status,
            content=content[:500],
            error_msg=error_msg[:1000],
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"记录推送日志失败: {e}")
        db.rollback()
    finally:
        db.close()
