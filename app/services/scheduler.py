"""
app/services/scheduler.py - 定时任务调度
使用 APScheduler 每日自动获取净值并推送报告
"""

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from config import Config
from app import SessionLocal
from app.models import Fund, FundNavHistory
from app.services.calculator import calc_global_summary
from app.services.push_service import build_report, send_report
from app.services.fund_api import search_fund

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def daily_report_job():
    """
    每日定时任务流程：
    1. 获取所有基金最新净值
    2. 计算盈亏
    3. 记录净值快照
    4. 推送报告
    """
    now = datetime.now()
    weekday = now.weekday()

    # 周末跳过
    if Config.SKIP_WEEKEND and weekday >= 5:
        logger.info(f"今天是{'周六' if weekday == 5 else '周日'}，跳过推送")
        return

    logger.info("=" * 50)
    logger.info("开始执行每日净值获取与推送任务")

    db = SessionLocal()
    try:
        # 1) 获取所有基金代码
        funds = db.query(Fund).all()
        if not funds:
            logger.info("无持仓基金，跳过")
            return

        # 2) 获取净值并记录快照
        nav_cache = {}
        for fund in funds:
            code = fund.fund_code
            try:
                info = search_fund(code)
                nav_cache[code] = info

                # 保存净值快照
                snapshot = FundNavHistory(
                    fund_code=code,
                    nav=info["nav"],
                    nav_date=info["nav_date"],
                )
                db.add(snapshot)

                # 更新基金名称
                if not fund.fund_name and info.get("fund_name"):
                    fund.fund_name = info["fund_name"]

                logger.info(f"  {info.get('fund_name', code)}: 净值={info['nav']:.4f}")

            except Exception as e:
                logger.error(f"  获取基金 {code} 失败: {e}")

        db.commit()

        # 3) 计算盈亏
        summary = calc_global_summary(db)

        # 4) 推送
        title, body = build_report(summary)
        result = send_report(Config.SERVERCHAN_SENDKEY, title, body)

        if result["success"]:
            logger.info("✅ 每日报告推送成功")
        else:
            logger.warning(f"⚠️ 推送失败: {result['message']}")

        logger.info(f"推送标题: {title}")

    except Exception as e:
        logger.error(f"每日任务异常: {e}", exc_info=True)
    finally:
        db.close()


def start_scheduler():
    """启动定时调度器"""
    time_str = Config.PUSH_TIME
    hour, minute = time_str.split(":")

    trigger = CronTrigger(
        day_of_week="mon-fri" if Config.SKIP_WEEKEND else "*",
        hour=int(hour),
        minute=int(minute),
    )

    scheduler.add_job(
        daily_report_job,
        trigger=trigger,
        id="daily_fund_report",
        name="每日基金报告",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"⏰ 定时任务已启动: 每{'工作日' if Config.SKIP_WEEKEND else '天'} "
                f"{time_str} 执行")
