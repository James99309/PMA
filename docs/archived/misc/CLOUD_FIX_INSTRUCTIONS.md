# 云端数据库约束冲突修复指南

## 🚨 当前问题
云端升级时遇到约束 `uq_scoring_config` 已存在的错误，导致升级失败。

## 🔧 修复方案

### 方案1：使用修复脚本（推荐）
在Render Terminal中执行以下命令：

```bash
# 进入项目目录
cd ~/project/src

# 直接运行约束冲突修复脚本
python fix_constraint_conflict.py
```

### 方案2：重新运行升级脚本
修复脚本已集成到升级脚本中：

```bash
cd ~/project/src
./upgrade_cloud_database.sh
```

### 方案3：手动修复（如果脚本不可用）
```bash
# 连接到数据库并手动处理
psql $DATABASE_URL

-- 检查当前约束
\d+ project_scoring_config

-- 如果 uq_scoring_config 已存在，跳过创建
-- 否则创建约束
ALTER TABLE project_scoring_config ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name);

-- 退出数据库
\q

# 运行Flask迁移
flask db upgrade
```

## ✅ 验证修复结果

修复完成后，检查以下内容：

1. **检查迁移版本**：
   ```bash
   flask db current
   ```
   应该显示：`c1308c08d0c9`

2. **检查约束状态**：
   ```bash
   psql $DATABASE_URL -c "\d+ project_scoring_config"
   ```

3. **启动应用测试**：
   ```bash
   python run.py
   ```

## 🎯 修复原理

**问题原因**：
- 云端数据库中 `uq_scoring_config` 约束已经存在
- 但迁移脚本仍尝试创建该约束
- 导致 "relation already exists" 错误

**修复逻辑**：
1. 检查约束是否已存在
2. 如果存在，跳过创建
3. 如果不存在，安全创建
4. 执行剩余的迁移操作

## 📞 如果仍有问题

如果上述方法都不起作用，请：

1. 复制完整的错误日志
2. 运行 `psql $DATABASE_URL -c "\d+ project_scoring_config"` 查看当前表结构
3. 联系技术支持并提供以上信息

---

**创建时间**: 2025年6月4日  
**适用环境**: Render云端部署  
**预计修复时间**: 2-5分钟 