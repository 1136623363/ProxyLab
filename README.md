# ProxyLab - 订阅转换器

一个功能强大的订阅链接转换和管理系统，支持多种代理协议和输出格式。

## ✨ 特性

- 🔄 **多协议支持**: V2Ray, Trojan, Shadowsocks, VLESS, Hysteria2
- 📱 **多格式输出**: Clash, V2RayN, 原始格式等
- 🎯 **智能解析**: 自动识别和解析订阅链接
- 📊 **实时监控**: 节点状态检测和性能监控
- 🔐 **用户管理**: 多用户支持和权限控制
- 📈 **统计分析**: 使用统计和性能分析
- 🌐 **Web界面**: 现代化的Vue.js前端界面
- 🐳 **容器化**: 完整的Docker支持

## 🚀 快速开始

### 使用Docker Compose（推荐）

1. **克隆项目**
```bash
git clone https://github.com/yourusername/ProxyLab.git
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
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8001
- API文档: http://localhost:8001/docs

### 手动安装

#### 后端安装

1. **安装Python依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
export SECRET_KEY="your-super-secret-key"
export DATABASE_URL="sqlite:///./data/subscription_converter.db"
```

3. **初始化数据库**
```bash
python -c "from app.database import init_database; init_database()"
```

4. **启动服务**
```bash
python run.py
```

#### 前端安装

1. **安装Node.js依赖**
```bash
cd frontend
npm install
```

2. **启动开发服务器**
```bash
npm run dev
```

## 📖 使用说明

### 基本功能

1. **添加订阅链接**
   - 登录管理界面
   - 在"订阅管理"中添加订阅链接
   - 系统会自动解析节点信息

2. **生成订阅**
   - 选择需要的节点
   - 选择输出格式（Clash、V2RayN等）
   - 生成订阅链接

3. **节点监控**
   - 查看节点状态和延迟
   - 监控节点可用性
   - 查看使用统计

### API使用

#### 认证
```bash
# 登录获取token
curl -X POST "http://localhost:8001/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

#### 获取订阅
```bash
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
| `LOG_LEVEL` | `info` | 日志级别 |

### 数据库配置

#### SQLite（默认）
```bash
DATABASE_URL=sqlite:///./data/subscription_converter.db
```

#### PostgreSQL（生产环境推荐）
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/subscription_converter
```

## 🐳 Docker部署

### 单容器部署
```bash
docker run -d \
  --name proxylab \
  -p 8001:8001 \
  -e SECRET_KEY="your-secret-key" \
  -v ./data:/app/data \
  proxylab:latest
```

### Docker Compose部署
```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 监控和维护

### 健康检查
```bash
curl http://localhost:8001/health
```

### 日志查看
```bash
# 应用日志
docker logs proxylab

# 实时日志
docker logs -f proxylab
```

### 数据备份
```bash
# SQLite备份
cp data/subscription_converter.db backup_$(date +%Y%m%d).db

# PostgreSQL备份
pg_dump -h localhost -U user subscription_converter > backup.sql
```

## 🔒 安全建议

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

## 🛠️ 开发指南

### 项目结构
```
ProxyLab/
├── app/                    # 后端应用
│   ├── routers/           # API路由
│   ├── models/            # 数据模型
│   ├── parsers/           # 协议解析器
│   ├── output/            # 输出生成器
│   └── monitoring/        # 监控模块
├── frontend/              # 前端应用
│   ├── src/              # 源代码
│   └── public/           # 静态资源
├── docs/                 # 文档
├── docker-compose.yml    # Docker Compose配置
└── Dockerfile           # Docker配置
```

### 开发环境设置
```bash
# 后端开发
cd app
pip install -r requirements.txt
python run.py

# 前端开发
cd frontend
npm install
npm run dev
```

### 代码规范
- Python: 遵循PEP 8
- JavaScript: 使用ESLint
- 提交信息: 使用约定式提交

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Element Plus](https://element-plus.org/) - Vue 3组件库
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL工具包

## 📞 支持

如果您遇到问题或有建议，请：

1. 查看 [文档](docs/)
2. 搜索 [Issues](https://github.com/yourusername/ProxyLab/issues)
3. 创建新的 Issue
4. 联系维护者

---

⭐ 如果这个项目对您有帮助，请给它一个星标！
