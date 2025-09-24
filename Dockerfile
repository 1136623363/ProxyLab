# 多阶段构建 - 整合前后端
FROM node:18-alpine as frontend-builder

# 构建前端
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --frozen-lockfile
COPY frontend/ .
RUN node node_modules/vite/bin/vite.js build

# Python后端构建阶段
FROM python:3.11-slim as backend-builder

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

# 生产阶段 - 纯FastAPI
FROM python:3.11-slim

# 安装必要工具
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser

# 设置工作目录
WORKDIR /app

# 从backend-builder阶段复制虚拟环境
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制后端应用代码
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser config.py ./
COPY --chown=appuser:appuser run.py ./

# 从frontend-builder阶段复制构建的前端文件
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/dist ./static/

# 创建必要的目录
RUN mkdir -p static data logs && \
    chown -R appuser:appuser /app

# 暴露端口
EXPOSE 80

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/subscription_converter.db
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "2", "--access-log"]