# 使用GitHub Actions进行CI/CD部署

## 当前问题
Jenkins账户被锁定，无法使用Jenkins进行CI/CD。我们可以使用GitHub Actions作为替代方案。

## 解决方案

### 1. 配置GitHub Secrets

在GitHub仓库中配置以下Secrets：
- `DOCKERHUB_USERNAME`: 你的Docker Hub用户名 (1136623363)
- `DOCKERHUB_TOKEN`: 你的Docker Hub访问令牌

### 2. 配置服务器部署

#### 方案A: 使用GitHub Actions部署到服务器

创建服务器部署脚本：

```yaml
# 在 .github/workflows/ci-cd.yml 中添加部署步骤
- name: Deploy to server
  uses: appleboy/ssh-action@v0.1.5
  with:
    host: ${{ secrets.SERVER_HOST }}
    username: ${{ secrets.SERVER_USERNAME }}
    key: ${{ secrets.SERVER_SSH_KEY }}
    script: |
      cd /path/to/ProxyLab
      docker-compose -f docker-compose.prod.yml down
      docker-compose -f docker-compose.prod.yml pull
      docker-compose -f docker-compose.prod.yml up -d
```

#### 方案B: 使用Webhook部署

1. 在服务器上创建webhook接收器
2. GitHub Actions构建完成后触发webhook
3. 服务器自动拉取镜像并重启服务

### 3. 手动部署方案

如果自动化部署有问题，可以使用手动部署：

```bash
# 1. 在服务器上克隆项目
git clone https://github.com/yourusername/ProxyLab.git
cd ProxyLab

# 2. 配置环境变量
cp env.production .env
# 编辑 .env 文件

# 3. 部署
docker-compose -f docker-compose.prod.yml up -d
```

### 4. 监控部署状态

```bash
# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 更新服务
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 立即行动

1. **配置GitHub Secrets**：
   - 进入仓库设置 → Secrets and variables → Actions
   - 添加 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN`

2. **推送代码**：
   ```bash
   git add .
   git commit -m "Fix CI/CD pipeline"
   git push origin main
   ```

3. **检查GitHub Actions**：
   - 进入仓库的Actions标签页
   - 查看构建状态

## 长期解决方案

1. **解决Jenkins账户问题**：
   - 联系Jenkins支持
   - 升级付费计划
   - 或迁移到其他CI/CD平台

2. **考虑其他CI/CD平台**：
   - GitLab CI
   - Azure DevOps
   - CircleCI
   - Travis CI

现在您可以先使用GitHub Actions进行CI/CD，等Jenkins问题解决后再切换回来。
