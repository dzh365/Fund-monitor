# 📈 基金净值在线监控与盈亏推送系统

个人基金投资的全栈看板。支持多资金账户管理（支付宝、天天基金、招商银行等），自动获取每日收盘净值，实时计算持仓盈亏，通过 Server酱推送每日盈亏报告。

主要功能：

- 多资金账户：按平台分别建账，独立管理持仓
- 自动净值：调用天天基金公开 API，自动拉取最新净值和日涨跌幅
- 盈亏计算：成本、市值、盈亏金额、收益率，账户与全局两级汇总
- 数据图表：ECharts 饼图（持仓占比）、柱图（盈亏对比）、折线图（资产趋势）
- 微信推送：Server酱 SCT API，每个交易日自动推送分账户盈亏报告
- 定时任务：APScheduler 调度，默认工作日 20:00 执行，周末跳过
- 主题切换：浅色 / 深色 / 跟随系统，一键切换

技术栈：Python 3.10+ · FastAPI · SQLAlchemy (SQLite) · Bootstrap 5 · ECharts · APScheduler · httpx

---

## 部署

### 直接部署

```bash
# 克隆项目
git clone <repo-url> fund-monitor
cd fund-monitor

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置
cp .env.example .env
# 编辑 .env，填写 SERVERCHAN_SENDKEY（可选）

# 启动
python main.py
```

浏览器打开 `http://localhost:16888`

### Docker 部署

```bash
cd fund-monitor

# 配置
cp .env.example .env
# 编辑 .env，填写 SERVERCHAN_SENDKEY（可选）

# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f
```

浏览器打开 `http://<你的主机IP>:16888`

数据库文件在 `./data/fund_monitor.db`，通过 volume 挂载，重建容器不丢数据。容器内置健康检查，`restart: unless-stopped` 确保主机重启后自动恢复。

---

## 声明

本项目由 [Mimo Claw](https://aistudio.xiaomimimo.com/#/?forcePage=claw) 生成。
