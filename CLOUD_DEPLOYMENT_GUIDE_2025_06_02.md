# PMA系统云端部署指南 - 2025年6月2日

## 部署概述

本次部署包含了PMA系统的重大权限系统修复和多项功能增强，主要解决了权限管理中的关键问题，并增加了审批流程、项目评分等新功能。

**🔧 数据库事务修复 (2025-06-02 19:30)**：
- ✅ 修复了云端部署后的数据库事务被中止问题
- ✅ 解决了 `current transaction is aborted, commands ignored until end of transaction block` 错误
- ✅ 在所有查询失败时添加 `db.session.rollback()` 事务回滚处理
- ✅ 确保后续查询不受前一个失败查询影响，提升系统稳定性

**🔧 SQLAlchemy兼容性修复 (2025-06-02 19:00)**：
- ✅ 修复了云端部署后的SQLAlchemy版本兼容性问题
- ✅ 解决了 `sqlalchemy.exc.StatementError` 查询参数错误
- ✅ 增强了所有关键查询的容错处理和后备机制
- ✅ 确保系统在不同SQLAlchemy版本环境下的稳定运行

**🔧 紧急修复 (2025-06-02 18:30)**：
- ✅ 修复了部署错误：环境变量PORT解析问题
- ✅ 解决了 `ValueError: invalid literal for int() with base 10: '$PORT'` 错误
- ✅ 增强了环境变量解析的容错性和稳定性

## 部署内容

### 数据库事务修复 (提交版本: 8c96afe)

**问题背景**：
云端部署后出现数据库事务被中止错误，导致后续查询失败：
```
psycopg2.errors.InFailedSqlTransaction: current transaction is aborted, commands ignored until end of transaction block
```

**核心修复**：
- ✅ 修复 `app/views/main.py` 首页查询的数据库事务回滚问题
- ✅ 修复 `app/views/product_analysis.py` 产品分析查询的事务问题  
- ✅ 修复 `app/views/user.py` 用户列表查询的事务问题
- ✅ 修复 `app/routes/product_management.py` 产品库存查询的事务问题

**技术细节**：
```python
# 修复前（事务会被中止）
try:
    results = query.order_by(Model.updated_at.desc()).limit(5).all()
except Exception as e:
    logger.warning(f"查询失败: {str(e)}")
    results = []

# 修复后（事务正确回滚）
try:
    results = query.order_by(Model.updated_at.desc()).limit(5).all()
except Exception as e:
    logger.warning(f"查询失败: {str(e)}")
    try:
        # 回滚失败的事务
        db.session.rollback()
        results = query.order_by(Model.id.desc()).limit(5).all()
    except Exception as e2:
        logger.error(f"查询完全失败: {str(e2)}")
        # 回滚失败的事务
        db.session.rollback()
        results = []
```

**影响模块**：
- 首页项目/报价/客户数据显示
- 产品分析页面数据查询
- 用户列表页面显示
- 产品库存管理页面

### SQLAlchemy兼容性修复 (提交版本: 8e33b85)

**问题背景**：
云端部署后出现SQLAlchemy版本兼容性问题，查询语句 `Project.updated_at.desc().limit(5)` 在云端环境报错：
```
sqlalchemy.exc.StatementError: (Background on this error at: https://sqlalche.me/e/20/f405)
```

**核心修复**：
- ✅ 修复 `app/views/main.py` 首页项目查询的兼容性问题
- ✅ 修复 `app/views/product_analysis.py` 产品分析查询的兼容性问题  
- ✅ 修复 `app/views/user.py` 用户列表查询的兼容性问题
- ✅ 修复 `app/routes/product_management.py` 产品库存查询的兼容性问题

**技术细节**：
所有查询都增加了异常处理，失败时使用 `id` 排序作为后备方案：
```python
try:
    results = query.order_by(Model.updated_at.desc()).limit(5).all()
except Exception as e:
    logger.warning(f"使用updated_at排序失败: {str(e)}, 尝试使用id排序")
    results = query.order_by(Model.id.desc()).limit(5).all()
```

**影响模块**：
- 首页项目/报价/客户数据显示
- 产品分析页面数据查询
- 用户列表页面显示
- 产品库存管理页面

### 环境变量解析修复 (提交版本: 2ce3b94)

**核心修复**：
- ✅ 修复 `config.py` 中的 `PORT` 环境变量解析错误
- ✅ 修复 `run.py` 中的端口解析逻辑  
- ✅ 修复 `MAIL_PORT` 环境变量解析
- ✅ 添加对无效环境变量值（如 `$PORT`）的处理
- ✅ 确保在环境变量无效时使用默认端口值

**技术细节**：
```python
# 修复前（会报错）
PORT = int(os.environ.get('PORT', 10000))

# 修复后（安全解析）
try:
    port_env = os.environ.get('PORT', '10000')
    if port_env.startswith('$') or not port_env.isdigit():
        PORT = 10000
    else:
        PORT = int(port_env)
except (ValueError, TypeError):
    PORT = 10000  # 默认端口
```

### 权限系统修复 (迁移版本: 5055ec5e2171)

**核心修复**：
- ✅ 权限合并逻辑修复：个人权限只能增强角色权限，不能减少
- ✅ 权限保存逻辑优化：避免为所有模块创建个人权限记录
- ✅ 用户角色变更处理：检测角色变更，自动清理个人权限
- ✅ 权限检查方法统一：使用OR逻辑合并角色权限和个人权限

**技术细节**：
```python
# 权限合并公式
最终权限 = 角色权限 OR 个人权限

# 权限检查逻辑
if personal_perm is not None:
    return role_perm or personal_perm
else:
    return role_perm
```

**权限设计原则**：
- 个人权限只能增强角色权限，不能减少
- 只存储真正需要的个人权限增强设置
- 角色变更时自动清理个人权限

## 部署流程

### 1. 预部署检查

运行预部署检查脚本：
```bash
python3 cloud_deployment_verification.py
```

**检查项目**：
- ✅ 环境变量解析修复验证
- ✅ SQLAlchemy兼容性验证  
- ✅ 数据库连接验证
- ✅ 权限系统修复验证
- ✅ 代码完整性验证

### 2. 代码部署

1. **拉取最新代码**：
   ```bash
   git pull origin main
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **环境变量检查**：
   - 确保 `PORT` 环境变量设置正确
   - 确保 `DATABASE_URL` 配置正确
   - 确保其他必要环境变量已设置

### 3. 数据库迁移

1. **运行数据库迁移**：
   ```bash
   flask db upgrade
   ```

2. **验证数据完整性**：
   ```bash
   python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); print('Database connection OK')"
   ```

### 4. 应用启动测试

1. **本地测试启动**：
   ```bash
   python3 run.py --port 8080
   ```

2. **功能验证**：
   - 首页数据加载
   - 用户登录功能
   - 权限系统功能
   - 产品分析功能

### 5. 生产环境部署

1. **重启应用服务**
2. **监控应用日志**
3. **验证核心功能**

## 验证清单

### 功能验证
- [ ] 首页项目/报价/客户数据正常显示
- [ ] 用户登录和权限检查正常
- [ ] 产品分析页面数据查询正常
- [ ] 用户列表页面显示正常
- [ ] 产品库存管理功能正常

### 性能验证
- [ ] 页面加载时间正常（< 3秒）
- [ ] 数据库查询性能正常
- [ ] 内存使用在合理范围

### 错误监控
- [ ] 应用日志无严重错误
- [ ] 数据库连接稳定
- [ ] 没有事务中止错误

## 回滚计划

如果部署出现问题，按以下步骤回滚：

1. **代码回滚**：
   ```bash
   git reset --hard <previous_commit_hash>
   ```

2. **数据库回滚**：
   ```bash
   flask db downgrade
   ```

3. **重启服务**

## 监控和维护

### 日志监控
- 监控应用错误日志
- 关注数据库连接日志
- 观察权限相关错误

### 性能监控
- 数据库查询性能
- 内存使用情况
- 响应时间指标

### 定期维护
- 定期备份数据库
- 监控磁盘空间使用
- 更新安全补丁

## 联系信息

如有部署问题，请联系：
- 技术负责人：NIJIE
- 邮箱：james111@evertac.net

---

**部署日期**：2025年6月2日  
**文档版本**：v3.0  
**最后更新**：2025-06-02 19:30

## 新增功能

1. **审批流程增强**
   - 审批模板版本化管理
   - 审批流程锁定机制
   - 审批中心UI优化

2. **项目评分系统**
   - 项目评分记录管理
   - 评分配置系统
   - 评分数据分析

3. **版本管理系统**
   - 代码版本跟踪
   - 变更历史记录
   - 升级管理功能

## 技术文档

### 权限系统架构
- **设计原则**: 个人权限只能增强角色权限，不能减少
- **权限计算**: 最终权限 = 角色权限 OR 个人权限
- **存储策略**: 只存储真正需要的个人权限增强

### 关键代码位置
- **权限检查**: `app/models/user.py` → `has_permission()`
- **权限管理**: `app/views/user.py` → `manage_permissions()`
- **模板上下文**: `app/__init__.py` → `inject_permissions()`

### 数据库表结构
- **users**: 用户基本信息和角色
- **permissions**: 个人权限增强设置
- **role_permissions**: 角色基础权限配置

## 联系信息

- **部署负责人**: 倪捷
- **技术支持**: 开发团队
- **紧急联系**: [紧急联系方式]

## 版本信息

- **PMA版本**: v1.0.1
- **部署日期**: 2025年6月2日
- **Git提交**: dfebe97
- **迁移版本**: 5055ec5e2171
- **部署环境**: 云端生产环境

---

**重要提醒**: 权限系统是安全核心功能，任何问题请立即联系技术团队进行处理。 