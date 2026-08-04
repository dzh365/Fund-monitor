"""
app/__init__.py - FastAPI 应用工厂
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import Config

# 数据库引擎
engine = create_engine(
    Config.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 模板与静态文件
templates = Jinja2Templates(directory="app/templates")


def create_app() -> FastAPI:
    app = FastAPI(title="基金净值监控系统", version="1.0.0")

    # 挂载静态文件
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # 注册路由
    from app.routes.dashboard import router as dashboard_router
    from app.routes.account import router as account_router
    from app.routes.fund import router as fund_router
    from app.routes.push import router as push_router
    from app.routes.settings import router as settings_router

    app.include_router(dashboard_router)
    app.include_router(account_router, prefix="/api")
    app.include_router(fund_router, prefix="/api")
    app.include_router(push_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")

    # 启动事件：建表 + 启动定时任务
    @app.on_event("startup")
    def on_startup():
        from app.models import Account, Fund, FundNavHistory, PushLog, Setting
        Base.metadata.create_all(bind=engine)
        from app.services.scheduler import start_scheduler
        start_scheduler()

    return app


def get_db():
    """数据库会话依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
