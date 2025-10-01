# PMA系统本地数据库配置说明

## 概述
本文档说明如何配置和使用本地PostgreSQL数据库运行PMA系统，而不是云端数据库。

## 前提条件
1. 已安装PostgreSQL服务器
2. PostgreSQL服务正在运行
3. 用户`nijie`有创建数据库的权限

## 配置步骤

### 1. 创建和初始化本地数据库
```bash
python setup_local_db.py
```

这个脚本会：
- 创建`pma_local`数据库（如果不存在）
- 测试数据库连接
- 初始化所有数据表结构

### 2. 启动本地版本应用

**方法一：使用原来的run.py（推荐）**
```bash
python run.py --local --port 8080
```

**方法二：使用专用的本地启动脚本**
```bash
python run_local.py --port 8080
```

默认端口：5000（如果被占用请使用8080）
访问地址：http://localhost:8080

## 数据库配置详情

### 本地数据库连接信息
- **主机**: localhost
- **端口**: 5432
- **数据库**: pma_local
- **用户**: nijie
- **SSL**: 禁用（本地连接）

### 环境变量设置
本地版本会自动设置以下环境变量：
```
FLASK_ENV=local
DATABASE_URL=postgresql://nijie@localhost:5432/pma_local
```

## 文件说明

### 新增文件
1. `run_local.py` - 本地数据库启动脚本
2. `setup_local_db.py` - 数据库初始化脚本
3. `LOCAL_DATABASE_SETUP.md` - 本说明文档

### 配置文件
- `config.py` - 包含`LocalConfig`类用于本地数据库配置

## 与云端版本的区别

| 项目 | 云端版本 | 本地版本 |
|------|----------|----------|
| 启动脚本 | `python run.py` | `python run.py --local` |
| 数据库 | Render PostgreSQL | 本地PostgreSQL |
| 端口 | 10000 | 8080（推荐） |
| 调试模式 | 关闭 | 开启 |
| SSL | 启用 | 禁用 |
| 环境 | production | local |

## 故障排除

### 数据库连接失败
如果遇到数据库连接问题，请检查：
1. PostgreSQL服务是否启动
2. 用户`nijie`是否存在
3. 用户是否有访问权限
4. 数据库`pma_local`是否存在

### 端口冲突
如果5000端口被占用（macOS的AirPlay接收器），使用`--port`参数指定其他端口：
```bash
python run.py --local --port 8080
```

或者在系统偏好设置中关闭AirPlay接收器：
系统偏好设置 -> 通用 -> AirDrop与接力 -> AirPlay接收器

### 权限问题
确保PostgreSQL用户`nijie`有以下权限：
- 连接到数据库服务器
- 创建数据库
- 创建表和索引

## 数据迁移

### 从云端导入数据
如需从云端数据库导入数据到本地，可以使用PostgreSQL的pg_dump和pg_restore工具。

### 备份本地数据
```bash
pg_dump -h localhost -U nijie pma_local > pma_local_backup.sql
```

### 恢复本地数据
```bash
psql -h localhost -U nijie pma_local < pma_local_backup.sql
```

## 开发建议
1. 使用本地数据库进行开发和测试
2. 定期备份本地数据
3. 在提交代码前确保云端版本也能正常运行
4. 使用版本控制管理数据库结构变更 