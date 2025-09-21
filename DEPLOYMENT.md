# 部署指南

## 快速开始

### 使用Docker Compose（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd ProxyLab
```

2. **配置环境变量**
```bash
cp env.example .env
# 编辑 .env 文件，设置必要的环境变量
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问应用**
- 前端: http://localhost:3000
- 后端API: http://localhost:8001
- API文档: http://localhost:8001/docs

### 手动部署

#### 后端部署

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
export SECRET_KEY="your-super-secret-key"
export DATABASE_URL="sqlite:///./data/subscription_converter.db"
export DEBUG=false
```

3. **初始化数据库**
```bash
python -c "from app.database import init_database; init_database()"
```

4. **启动服务**
```bash
python run.py
```

#### 前端部署

1. **安装依赖**
```bash
cd frontend
npm install
```

2. **构建生产版本**
```bash
npm run build
```

3. **启动服务**
```bash
npm run serve
```

## 生产环境部署

### 使用Docker

1. **构建镜像**
```bash
docker build -t subscription-converter .
```

2. **运行容器**
```bash
docker run -d \
  --name subscription-converter \
  -p 8001:8001 \
  -e SECRET_KEY="your-super-secret-key" \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  subscription-converter
```

### 使用Docker Compose

1. **生产环境配置**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    image: subscription-converter:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=subscription_converter
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

2. **启动生产环境**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 环境变量配置

### 必需配置

- `SECRET_KEY`: JWT密钥，生产环境必须修改
- `DATABASE_URL`: 数据库连接字符串
- `DEBUG`: 调试模式，生产环境设为false

### 可选配置

- `HOST`: 服务监听地址（默认: 0.0.0.0）
- `PORT`: 服务端口（默认: 8001）
- `LOG_LEVEL`: 日志级别（默认: info）
- `CORS_ORIGINS`: CORS允许的源，逗号分隔
- `NODE_CHECK_TIMEOUT`: 节点检测超时时间（秒）
- `CACHE_TTL`: 缓存生存时间（秒）

## 数据库配置

### SQLite（开发环境）
```bash
DATABASE_URL=sqlite:///./data/subscription_converter.db
```

### PostgreSQL（生产环境推荐）
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/subscription_converter
```

### MySQL
```bash
DATABASE_URL=mysql://username:password@localhost:3306/subscription_converter
```

## 反向代理配置

### Nginx配置示例

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 监控和日志

### 日志文件位置
- 应用日志: `logs/app.log`
- Nginx访问日志: `/var/log/nginx/access.log`
- Nginx错误日志: `/var/log/nginx/error.log`

### 健康检查
```bash
curl http://localhost:8001/health
```

### 监控指标
- 内存使用: 通过Docker stats查看
- 数据库连接: 通过应用日志监控
- 响应时间: 通过Nginx日志分析

## 安全建议

1. **修改默认密钥**
   - 生成强随机密钥
   - 定期轮换密钥

2. **数据库安全**
   - 使用强密码
   - 限制数据库访问IP
   - 定期备份数据

3. **网络安全**
   - 使用HTTPS
   - 配置防火墙
   - 限制CORS源

4. **系统安全**
   - 定期更新依赖
   - 监控异常访问
   - 使用非root用户运行

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
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log

# 查看访问统计
grep "GET /api" logs/app.log | wc -l
```

## 性能优化

1. **数据库优化**
   - 添加适当索引
   - 定期清理旧数据
   - 使用连接池

2. **缓存优化**
   - 启用Redis缓存
   - 设置合理的TTL
   - 监控缓存命中率

3. **应用优化**
   - 使用多进程部署
   - 启用Gzip压缩
   - 优化静态资源

## 备份和恢复

### 数据备份
```bash
# SQLite备份
cp data/subscription_converter.db backup_$(date +%Y%m%d).db

# PostgreSQL备份
pg_dump -h localhost -U user subscription_converter > backup_$(date +%Y%m%d).sql
```

### 恢复数据
```bash
# SQLite恢复
cp backup_20231201.db data/subscription_converter.db

# PostgreSQL恢复
psql -h localhost -U user subscription_converter < backup_20231201.sql
```
