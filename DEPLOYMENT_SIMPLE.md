# 简化部署指南

## 快速开始

### 1. 使用Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/yourusername/ProxyLab.git
cd ProxyLab

# 配置环境变量
cp env.example .env
# 编辑 .env 文件，设置必要的环境变量

# 启动服务
docker-compose up -d
```

### 2. 访问应用

- 前端界面: http://localhost:3000
- 后端API: http://localhost:8001
- API文档: http://localhost:8001/docs

## 生产环境部署

### 使用Docker Compose

```bash
# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### 使用部署脚本

```bash
# 设置环境变量
export DOCKERHUB_USERNAME=yourusername
export DOCKERHUB_TOKEN=your_token

# 执行部署
./scripts/deploy.sh production
```

## 环境变量配置

### 必需配置

- `SECRET_KEY`: JWT密钥，生产环境必须修改
- `DATABASE_URL`: 数据库连接字符串
- `DOCKERHUB_USERNAME`: Docker Hub用户名

### 可选配置

- `DEBUG`: 调试模式（默认: false）
- `HOST`: 服务监听地址（默认: 0.0.0.0）
- `PORT`: 服务端口（默认: 8001）
- `LOG_LEVEL`: 日志级别（默认: info）

## 持续部署

### GitHub Actions

1. 配置GitHub Secrets：
   - `DOCKERHUB_USERNAME`: Docker Hub用户名
   - `DOCKERHUB_TOKEN`: Docker Hub访问令牌

2. 推送代码到main分支即可自动构建和部署

### Jenkins

1. 配置Jenkins凭据：
   - 添加Docker Hub凭据（ID: `dockerhub-credentials`）

2. 创建Pipeline任务：
   - 选择Pipeline script from SCM
   - 配置Git仓库URL

## 监控和维护

### 查看服务状态

```bash
docker-compose ps
docker-compose logs -f
```

### 更新服务

```bash
docker-compose pull
docker-compose up -d
```

### 备份数据

```bash
# 数据库备份
docker-compose exec postgres pg_dump -U proxylab subscription_converter > backup.sql

# 恢复数据
docker-compose exec -T postgres psql -U proxylab subscription_converter < backup.sql
```

## 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用
   - 查看日志文件
   - 验证环境变量配置

2. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 确认网络连通性

3. **前端无法访问后端**
   - 检查CORS配置
   - 验证代理设置
   - 查看浏览器控制台错误

### 日志分析

```bash
# 查看应用日志
docker-compose logs app

# 查看错误日志
docker-compose logs app | grep ERROR

# 查看访问统计
docker-compose logs app | grep "GET /api" | wc -l
```

## 安全建议

1. **修改默认密钥**
   ```bash
   export SECRET_KEY="$(openssl rand -hex 32)"
   ```

2. **使用HTTPS**
   - 配置SSL证书
   - 启用HTTPS重定向

3. **数据库安全**
   - 使用强密码
   - 限制访问IP
   - 定期备份

4. **网络安全**
   - 配置防火墙
   - 限制CORS源
   - 使用反向代理
