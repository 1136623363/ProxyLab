# 多阶段构建 - 整合前后端和Nginx
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

# 生产阶段 - 整合Nginx
FROM python:3.11-slim

# 安装Nginx和必要工具
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
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
RUN mkdir -p static data logs /var/log/nginx /var/lib/nginx /var/cache/nginx && \
    chown -R appuser:appuser /app

# 配置Nginx
COPY nginx.conf /etc/nginx/nginx.conf
RUN chown -R appuser:appuser /var/log/nginx /var/lib/nginx /var/cache/nginx /etc/nginx

# 配置Supervisor
RUN echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:nginx]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=nginx -g "daemon off;"' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/var/log/nginx/error.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/var/log/nginx/access.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:app]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 2 --access-log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'directory=/app' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=appuser' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/app/logs/app_error.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/app/logs/app_access.log' >> /etc/supervisor/conf.d/supervisord.conf

# 暴露端口
EXPOSE 80 8001

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/subscription_converter.db
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 启动命令
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]