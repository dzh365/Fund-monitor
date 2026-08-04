#!/usr/bin/env python3
"""
main.py - 基金净值监控系统入口
启动 FastAPI 服务
"""

import uvicorn
from fastapi import Request
from fastapi.responses import HTMLResponse
from config import Config
from app import create_app, templates

app = create_app()


# ── HTML 页面路由 ──────────────────────────────────────
@app.get("/accounts", response_class=HTMLResponse)
def accounts_page(request: Request):
    return templates.TemplateResponse("accounts.html", {"request": request})


@app.get("/accounts/{account_id}", response_class=HTMLResponse)
def account_detail_page(request: Request, account_id: int):
    return templates.TemplateResponse("account_detail.html", {"request": request, "account_id": account_id})


@app.get("/push-logs", response_class=HTMLResponse)
def push_logs_page(request: Request):
    return templates.TemplateResponse("push_logs.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True,
    )
