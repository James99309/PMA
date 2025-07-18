# PMA本地启动指南

## 🚀 快速启动

### 日常开发（推荐）
```bash
./start.sh
```

### 超简单启动（调试用）
```bash
./start_simple.sh
```

### 完整安全启动（首次使用）
```bash
./start_local_safe.sh
```

## ✅ 启动成功标志

看到以下信息表示启动成功：
```
🔒 云端数据库访问已被禁用 - 仅允许本地数据库连接
🔧 配置为使用本地数据库
💾 数据库: 本地PostgreSQL
📍 访问地址: http://localhost:端口号
```

## 🔧 常见问题

### 端口被占用
脚本会自动查找可用端口：5001-5008, 8001-8003

### 进程冲突
脚本会自动关闭现有Python进程

### 数据库连接失败
```bash
brew services start postgresql
createdb pma_local
```

## 🛡️ 安全保证

- ✅ 100%本地数据库连接
- ✅ 云端数据库访问已禁用
- ✅ 自动安全检查
- ✅ 环境隔离保护

## 📞 快速帮助

1. **启动失败**: 使用 `./start_simple.sh`
2. **端口冲突**: 脚本自动处理
3. **数据库问题**: 检查PostgreSQL服务
4. **权限问题**: `chmod +x *.sh` 