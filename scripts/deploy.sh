#!/bin/bash

# 部署脚本
set -e

# 配置
DOCKERHUB_USERNAME=${DOCKERHUB_USERNAME:-yourusername}
IMAGE_NAME="proxylab"
ENVIRONMENT=${1:-staging}

echo "🚀 开始部署到 $ENVIRONMENT 环境..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 登录Docker Hub
echo "🔐 登录Docker Hub..."
echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USERNAME --password-stdin

# 拉取最新镜像
echo "📥 拉取最新镜像..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker pull $DOCKERHUB_USERNAME/$IMAGE_NAME:latest
    docker pull $DOCKERHUB_USERNAME/$IMAGE_NAME-frontend:latest
else
    docker pull $DOCKERHUB_USERNAME/$IMAGE_NAME:develop
    docker pull $DOCKERHUB_USERNAME/$IMAGE_NAME-frontend:develop
fi

# 停止现有服务
echo "🛑 停止现有服务..."
docker-compose -f docker-compose.$ENVIRONMENT.yml down

# 启动新服务
echo "▶️ 启动新服务..."
docker-compose -f docker-compose.$ENVIRONMENT.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 健康检查
echo "🏥 执行健康检查..."
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ 部署成功！"
    echo "🌐 前端地址: http://localhost:3000"
    echo "🔧 后端地址: http://localhost:8001"
    echo "📚 API文档: http://localhost:8001/docs"
else
    echo "❌ 健康检查失败，请检查日志"
    docker-compose -f docker-compose.$ENVIRONMENT.yml logs
    exit 1
fi

# 清理旧镜像
echo "🧹 清理旧镜像..."
docker image prune -f

echo "🎉 部署完成！"
