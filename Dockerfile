FROM python:3.12-slim

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY . .

# 数据目录（挂载卷）
VOLUME /app/data

# 默认环境变量
ENV HOST=0.0.0.0 \
    PORT=16888 \
    DATABASE_URL=sqlite:///./data/fund_monitor.db

EXPOSE 16888

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:16888/api/dashboard/stats || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "16888"]
