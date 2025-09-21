# 部署指南

## 生产环境部署

### 1. 服务器要求

**最低配置:**
- CPU: 1 核心
- 内存: 1GB RAM
- 存储: 10GB 可用空间
- 网络: 稳定的互联网连接

**推荐配置:**
- CPU: 2+ 核心
- 内存: 2GB+ RAM
- 存储: 20GB+ SSD
- 网络: 100Mbps+ 带宽

### 2. 系统准备

#### Ubuntu/Debian
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y curl wget git unzip

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### CentOS/RHEL
```bash
# 更新系统
sudo yum update -y

# 安装必要工具
sudo yum install -y curl wget git unzip

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl enable docker
sudo systemctl start docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. 项目部署

#### 方法一: Docker Compose (推荐)

1. **克隆项目**
```bash
git clone <repository-url>
cd subscription-converter
```

2. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

3. **修改配置**
```env
# 生产环境配置
SECRET_KEY=your-very-secure-secret-key-here
DATABASE_URL=postgresql://user:password@db:5432/subscription_converter
DEBUG=False
CORS_ORIGINS=["https://yourdomain.com"]
```

4. **启动服务**
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 方法二: 手动部署

1. **安装 Python 3.11+**
```bash
# Ubuntu/Debian
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# CentOS/RHEL
sudo yum install -y python311 python311-pip python311-devel
```

2. **安装 Node.js 16+**
```bash
# 使用 NodeSource 仓库
curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt-get install -y nodejs
```

3. **部署后端**
```bash
# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DATABASE_URL="postgresql://user:password@localhost:5432/subscription_converter"
export SECRET_KEY="your-secret-key"

# 启动服务
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

4. **部署前端**
```bash
cd frontend
npm install
npm run build

# 使用 Nginx 服务静态文件
sudo cp -r dist/* /var/www/html/
```

### 4. 数据库配置

#### PostgreSQL (推荐)

1. **安装 PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt install -y postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install -y postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

2. **创建数据库**
```bash
sudo -u postgres psql
CREATE DATABASE subscription_converter;
CREATE USER converter_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE subscription_converter TO converter_user;
\q
```

3. **更新配置**
```env
DATABASE_URL=postgresql://converter_user:your_password@localhost:5432/subscription_converter
```

#### SQLite (开发/测试)

```env
DATABASE_URL=sqlite:///./data/subscription_converter.db
```

### 5. Nginx 配置

1. **安装 Nginx**
```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS/RHEL
sudo yum install -y nginx
```

2. **创建配置文件**
```bash
sudo nano /etc/nginx/sites-available/subscription-converter
```

3. **配置内容**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL 证书配置
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 前端静态文件
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # 缓存设置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
```

4. **启用配置**
```bash
sudo ln -s /etc/nginx/sites-available/subscription-converter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL 证书配置

#### 使用 Let's Encrypt (免费)

1. **安装 Certbot**
```bash
# Ubuntu/Debian
sudo apt install -y certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install -y certbot python3-certbot-nginx
```

2. **获取证书**
```bash
sudo certbot --nginx -d yourdomain.com
```

3. **自动续期**
```bash
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

### 7. 系统服务配置

#### 创建 systemd 服务

1. **后端服务**
```bash
sudo nano /etc/systemd/system/subscription-converter.service
```

```ini
[Unit]
Description=Subscription Converter API
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/subscription-converter
Environment=PATH=/path/to/subscription-converter/venv/bin
ExecStart=/path/to/subscription-converter/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

2. **启用服务**
```bash
sudo systemctl daemon-reload
sudo systemctl enable subscription-converter
sudo systemctl start subscription-converter
```

### 8. 监控和日志

#### 日志配置

1. **应用日志**
```bash
# 创建日志目录
sudo mkdir -p /var/log/subscription-converter
sudo chown www-data:www-data /var/log/subscription-converter

# 配置日志轮转
sudo nano /etc/logrotate.d/subscription-converter
```

```
/var/log/subscription-converter/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload subscription-converter
    endscript
}
```

2. **Nginx 日志**
```bash
# 配置访问日志
sudo nano /etc/nginx/nginx.conf
```

```nginx
http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
}
```

#### 监控设置

1. **健康检查脚本**
```bash
#!/bin/bash
# /usr/local/bin/health-check.sh

API_URL="http://127.0.0.1:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

2. **定时检查**
```bash
# 添加到 crontab
*/5 * * * * /usr/local/bin/health-check.sh
```

### 9. 备份策略

#### 数据库备份

1. **PostgreSQL 备份脚本**
```bash
#!/bin/bash
# /usr/local/bin/backup-db.sh

BACKUP_DIR="/var/backups/subscription-converter"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="subscription_converter"

mkdir -p $BACKUP_DIR

# 创建备份
pg_dump $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# 压缩备份
gzip $BACKUP_DIR/db_backup_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
```

2. **文件备份**
```bash
#!/bin/bash
# /usr/local/bin/backup-files.sh

BACKUP_DIR="/var/backups/subscription-converter"
APP_DIR="/path/to/subscription-converter"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据目录
tar -czf $BACKUP_DIR/data_backup_$DATE.tar.gz -C $APP_DIR data/

# 删除7天前的备份
find $BACKUP_DIR -name "data_backup_*.tar.gz" -mtime +7 -delete
```

### 10. 安全配置

#### 防火墙设置

```bash
# Ubuntu/Debian (UFW)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS/RHEL (firewalld)
sudo systemctl enable firewalld
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

#### 系统安全

1. **更新系统**
```bash
# 定期更新
sudo apt update && sudo apt upgrade -y
```

2. **配置 SSH**
```bash
sudo nano /etc/ssh/sshd_config
```

```
# 禁用 root 登录
PermitRootLogin no

# 使用密钥认证
PasswordAuthentication no
PubkeyAuthentication yes

# 限制用户
AllowUsers yourusername
```

3. **安装 fail2ban**
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 11. 性能优化

#### 数据库优化

1. **PostgreSQL 配置**
```bash
sudo nano /etc/postgresql/13/main/postgresql.conf
```

```
# 内存设置
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# 连接设置
max_connections = 100

# 日志设置
log_statement = 'mod'
log_min_duration_statement = 1000
```

2. **重启服务**
```bash
sudo systemctl restart postgresql
```

#### 应用优化

1. **Gunicorn 配置**
```bash
# 创建配置文件
nano gunicorn.conf.py
```

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

2. **启动命令**
```bash
gunicorn -c gunicorn.conf.py app.main:app
```

### 12. 故障排除

#### 常见问题

1. **服务无法启动**
```bash
# 检查日志
sudo journalctl -u subscription-converter -f

# 检查端口占用
sudo netstat -tlnp | grep :8000
```

2. **数据库连接失败**
```bash
# 检查数据库状态
sudo systemctl status postgresql

# 测试连接
psql -h localhost -U converter_user -d subscription_converter
```

3. **Nginx 配置错误**
```bash
# 测试配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log
```

#### 性能问题

1. **高 CPU 使用率**
```bash
# 查看进程
top -p $(pgrep -f gunicorn)

# 调整 worker 数量
```

2. **内存不足**
```bash
# 查看内存使用
free -h

# 调整数据库缓存
```

3. **磁盘空间不足**
```bash
# 查看磁盘使用
df -h

# 清理日志
sudo journalctl --vacuum-time=7d
```

---

**注意**: 请根据实际环境调整配置参数，确保系统安全和性能。
