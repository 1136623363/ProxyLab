# GitHub Actions 配置指南

## 步骤1：配置GitHub Secrets

### 1.1 进入仓库设置
1. 打开您的GitHub仓库：https://github.com/yourusername/ProxyLab
2. 点击 **Settings** 标签页
3. 在左侧菜单中找到 **Secrets and variables** → **Actions**

### 1.2 添加必要的Secrets
点击 **New repository secret** 添加以下secrets：

#### DOCKERHUB_USERNAME
- **Name**: `DOCKERHUB_USERNAME`
- **Value**: `1136623363`

#### DOCKERHUB_TOKEN
- **Name**: `DOCKERHUB_TOKEN`
- **Value**: 您的Docker Hub访问令牌

### 1.3 获取Docker Hub访问令牌
1. 登录 https://hub.docker.com
2. 点击右上角头像 → **Account Settings**
3. 点击 **Security** 标签页
4. 点击 **New Access Token**
5. 输入描述（如：GitHub Actions）
6. 选择权限：**Read, Write, Delete**
7. 点击 **Generate**
8. 复制生成的令牌（只显示一次）

## 步骤2：推送代码触发构建

### 2.1 提交当前更改
```bash
git add .
git commit -m "Configure GitHub Actions CI/CD"
git push origin main
```

### 2.2 检查构建状态
1. 进入仓库的 **Actions** 标签页
2. 查看最新的workflow运行状态
3. 点击具体的运行查看详细日志

## 步骤3：验证构建结果

### 3.1 检查Docker Hub
1. 登录 https://hub.docker.com
2. 查看您的仓库：`1136623363/proxylab`
3. 确认镜像已成功推送

### 3.2 测试镜像
```bash
# 拉取并测试后端镜像
docker pull 1136623363/proxylab:latest
docker run -p 8001:8001 1136623363/proxylab:latest

# 拉取并测试前端镜像
docker pull 1136623363/proxylab-frontend:latest
docker run -p 3000:80 1136623363/proxylab-frontend:latest
```

## 步骤4：部署到生产环境

### 4.1 使用Docker Compose部署
```bash
# 在服务器上
git clone https://github.com/yourusername/ProxyLab.git
cd ProxyLab

# 配置环境变量
cp env.production .env
# 编辑 .env 文件，设置生产环境变量

# 部署
docker-compose -f docker-compose.prod.yml up -d
```

### 4.2 使用部署脚本
```bash
# 设置环境变量
export DOCKERHUB_USERNAME=1136623363
export DOCKERHUB_TOKEN=your_token

# 执行部署
./scripts/deploy.sh production
```

## 故障排除

### 常见问题

1. **构建失败 - 权限问题**
   - 检查Docker Hub用户名和令牌是否正确
   - 确认令牌有推送权限

2. **构建失败 - 依赖问题**
   - 检查requirements.txt中的依赖
   - 查看构建日志中的具体错误

3. **推送失败 - 网络问题**
   - 检查网络连接
   - 尝试重新运行workflow

### 查看日志
1. 进入GitHub Actions页面
2. 点击失败的workflow
3. 点击具体的步骤查看详细日志
4. 根据错误信息进行修复

## 自动化流程

配置完成后，每次推送代码到main分支都会：
1. ✅ 自动运行测试
2. ✅ 自动构建Docker镜像
3. ✅ 自动推送到Docker Hub
4. ✅ 可以配置自动部署到服务器

## 下一步

1. **配置Secrets**：按照步骤1配置GitHub Secrets
2. **推送代码**：按照步骤2推送代码触发构建
3. **验证结果**：按照步骤3验证构建是否成功
4. **部署应用**：按照步骤4部署到生产环境

现在您就有了一个完整的CI/CD流程！
