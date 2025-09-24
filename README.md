# ProxyLab - 订阅转换器

一个功能强大的订阅链接转换和管理系统，支持多种代理协议和输出格式。

## ✨ 特性

- 🔄 **多协议支持**: V2Ray, Trojan, Shadowsocks, VLESS, Hysteria2
- 📱 **多格式输出**: Clash, V2RayN, 原始格式等
- 🎯 **智能解析**: 自动识别和解析订阅链接
- 📊 **实时监控**: 节点状态检测和性能监控
- 🔐 **用户管理**: 多用户支持和权限控制
- 🐳 **单镜像部署**: 整合Nginx和FastAPI，一键部署

## 🚀 快速开始

### Docker部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/1136623363/ProxyLab.git
cd ProxyLab

# 2. 配置环境变量
cp env.example .env
# 编辑 .env 文件，设置必要的环境变量

# 3. 启动服务
docker-compose up -d

# 4. 访问应用
# 应用界面: http://localhost:8899
# API文档: http://localhost:8899/docs
# 健康检查: http://localhost:8899/health
```

### 从Docker Hub部署

```bash
# 拉取并运行镜像
docker run -d \
  --name proxylab \
  -p 8899:80 \
  -e SECRET_KEY="your-secret-key" \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  1136623363/proxylab:latest
```

### 手动安装

```bash
# 后端
pip install -r requirements.txt
export SECRET_KEY="your-secret-key"
python run.py

# 前端
cd frontend
npm install
npm run dev
```

## 📖 使用说明

### 基本功能

1. **添加订阅链接** - 在管理界面添加订阅链接，系统自动解析节点
2. **生成订阅** - 选择节点和输出格式，生成订阅链接
3. **节点监控** - 查看节点状态、延迟和使用统计

### API使用

```bash
# 登录获取token
curl -X POST "http://localhost:8001/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 获取订阅内容
curl -X GET "http://localhost:8001/api/output/subscription?format=clash" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | `your-secret-key-change-this-in-production` | JWT密钥 |
| `DATABASE_URL` | `sqlite:///./data/subscription_converter.db` | 数据库连接 |
| `DEBUG` | `false` | 调试模式 |
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8001` | 服务端口 |

### 数据库配置

- **SQLite（默认）**: `sqlite:///./data/subscription_converter.db`
- **PostgreSQL（生产推荐）**: `postgresql://username:password@localhost:5432/subscription_converter`

## 📊 监控和维护

```bash
# 健康检查
curl http://localhost:8899/health

# 查看日志
docker logs -f proxylab

# 数据备份
cp data/subscription_converter.db backup_$(date +%Y%m%d).db
```

## 🔒 安全建议

1. **修改默认密钥**: `export SECRET_KEY="$(openssl rand -hex 32)"`
2. **使用HTTPS**: 配置SSL证书
3. **数据库安全**: 使用强密码，定期备份
4. **网络安全**: 配置防火墙，限制CORS源

## 🛠️ 开发指南

### 项目结构

```
ProxyLab/
├── app/                    # 后端应用
│   ├── routers/           # API路由
│   ├── models/            # 数据模型
│   ├── parsers/           # 协议解析器
│   └── output/            # 输出生成器
├── frontend/              # 前端应用
├── docker-compose.yml     # Docker配置
└── Dockerfile            # 单镜像构建
```

### 开发环境

```bash
# 后端开发
cd app && pip install -r requirements.txt && python run.py

# 前端开发
cd frontend && npm install && npm run dev
```

## 🔧 CI/CD

项目使用GitHub Actions自动构建和部署：

- **自动构建**: 推送代码到main分支自动构建Docker镜像
- **自动推送**: 构建完成后自动推送到Docker Hub
- **单镜像部署**: 前端和后端整合到一个镜像中

### 配置GitHub Actions

在GitHub仓库中配置Secrets：
- `DOCKERHUB_USERNAME`: 1136623363
- `DOCKERHUB_TOKEN`: 您的Docker Hub访问令牌

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

---

⭐ 如果这个项目对您有帮助，请给它一个星标！