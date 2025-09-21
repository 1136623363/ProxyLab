# 多阶段构建 - 优化版本
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 生产阶段
FROM python:3.11-slim

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libffi7 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser

# 设置工作目录
WORKDIR /app

# 从builder阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码（排除不必要的文件）
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser config.py ./
COPY --chown=appuser:appuser run.py ./

# 创建必要的目录
RUN mkdir -p static data logs && \
    chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8001

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/subscription_converter.db
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health', timeout=5)" || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2", "--access-log"]