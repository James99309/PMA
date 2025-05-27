# PMA系统云端部署指南

## 当前部署状态

### 数据库配置
- **云端数据库**: Render PostgreSQL
- **数据库URL**: `postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d`
- **本地数据库**: PostgreSQL (nijie@localhost:5432/pma_local)

### 代码仓库
- **GitHub仓库**: `git@github.com:James99309/PMA.git`
- **当前分支**: main
- **最新提交**: 产品分析模块部署 (22523c8)

## 部署步骤

### 1. 检查本地更改
```bash
# 检查Git状态
git status

# 查看未提交的更改
git diff
```

### 2. 提交并推送代码
```bash
# 添加所有更改
git add .

# 提交更改
git commit -m "描述性提交信息"

# 推送到远程仓库
git push origin main
```

### 3. 云端服务器部署
```bash
# SSH连接到云端服务器
ssh user@your-server.com

# 进入项目目录
cd /path/to/pma

# 拉取最新代码
git pull origin main

# 激活虚拟环境（如果使用）
source venv/bin/activate

# 安装/更新依赖
pip install -r requirements.txt

# 应用数据库迁移（如果有）
flask db upgrade

# 重启应用服务
supervisorctl restart pma
# 或者
systemctl restart pma
# 或者
pm2 restart pma
```

### 4. 验证部署
```bash
# 检查服务状态
supervisorctl status pma

# 查看应用日志
tail -f /var/log/pma/app.log

# 测试应用访问
curl -I http://your-domain.com
```

## 数据库迁移检查

### 检查迁移状态
```bash
# 查看当前迁移版本
flask db current

# 查看迁移历史
flask db history

# 查看待应用的迁移
flask db show
```

### 应用迁移
```bash
# 应用所有待处理的迁移
flask db upgrade

# 应用到特定版本
flask db upgrade <revision_id>
```

## 环境变量配置

### 必需的环境变量
```bash
# 数据库连接
DATABASE_URL=postgresql://user:password@host:port/database

# 应用密钥
SECRET_KEY=your-secret-key

# JWT密钥
JWT_SECRET_KEY=your-jwt-secret

# 邮件配置
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# 管理员邮箱
ADMIN_EMAIL=admin@company.com

# 应用域名
APP_DOMAIN=https://your-domain.com

# 端口配置
FLASK_PORT=8082
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查DATABASE_URL格式
   - 确认数据库服务器可访问
   - 验证用户名密码正确

2. **迁移失败**
   - 检查数据库权限
   - 查看迁移文件语法
   - 手动回滚到上一版本

3. **应用启动失败**
   - 检查依赖是否完整安装
   - 查看错误日志
   - 验证配置文件正确性

### 日志查看
```bash
# 应用日志
tail -f logs/app.log

# 系统日志
journalctl -u pma -f

# Supervisor日志
tail -f /var/log/supervisor/pma.log
```

## 备份策略

### 数据库备份
```bash
# 创建数据库备份
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
psql $DATABASE_URL < backup_file.sql
```

### 代码备份
```bash
# 创建代码快照
git tag -a v$(date +%Y.%m.%d) -m "部署快照 $(date)"
git push origin --tags
```

## 监控和维护

### 性能监控
- 监控数据库连接数
- 检查内存使用情况
- 监控响应时间

### 定期维护
- 清理日志文件
- 更新依赖包
- 数据库优化

## 联系信息
- **开发者**: James Ni
- **邮箱**: james98980566@gmail.com
- **GitHub**: James99309 