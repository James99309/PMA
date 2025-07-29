# 多数据库迁移安全管理指南

## 🚨 问题分析

当前状况：
- **SP8D数据库**: 版本 `sync_local_to_cloud_20250728`，已完成迁移
- **OVS数据库**: alembic_version表为空，需要执行 `ovs_sync_to_latest_20250729` 迁移
- **风险**: 两个迁移文件在同一目录，可能发生混乱

## 🔒 安全策略

### 方案1: 环境检查迁移（推荐）
在迁移文件中添加数据库环境检查，确保只在正确的数据库执行。

### 方案2: 分离迁移文件
为不同数据库创建独立的迁移路径。

### 方案3: 手动迁移验证
在执行前人工验证当前数据库状态。

## 🛠️ 实施方案1: 环境检查迁移

修改OVS迁移文件，添加数据库识别机制：

```python
def upgrade():
    # 1. 检查当前数据库是否为OVS
    connection = op.get_bind()
    
    # 通过数据库名或特征表来识别
    try:
        result = connection.execute(sa.text("SELECT current_database()"))
        db_name = result.fetchone()[0]
        
        if 'ovs' not in db_name.lower():
            print(f"❌ 错误: 当前数据库 '{db_name}' 不是OVS数据库")
            print("此迁移仅适用于OVS数据库")
            return
            
        print(f"✅ 确认: 当前数据库 '{db_name}' 是OVS数据库")
    except Exception as e:
        print(f"⚠️ 无法确定数据库名称: {e}")
        
        # 备用检查: 通过表数量和特征来判断
        try:
            result = connection.execute(sa.text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"))
            table_count = result.fetchone()[0]
            
            if table_count != 56:  # OVS应该有56个表
                print(f"❌ 错误: 当前数据库表数量 {table_count}，不符合OVS数据库特征(56个表)")
                print("请确认您正在正确的数据库上执行迁移")
                return
                
            print(f"✅ 确认: 表数量 {table_count} 符合OVS数据库特征")
        except Exception as e2:
            print(f"❌ 数据库验证失败: {e2}")
            return
    
    # 2. 检查alembic版本状态
    try:
        result = connection.execute(sa.text("SELECT version_num FROM alembic_version"))
        current_version = result.fetchone()
        
        if current_version and current_version[0]:
            print(f"❌ 错误: 数据库已有迁移版本 '{current_version[0]}'")
            print("此迁移仅适用于未初始化的OVS数据库")
            return
            
    except Exception:
        # alembic_version表为空或不存在，这是期望的OVS状态
        print("✅ 确认: OVS数据库处于未初始化状态")
    
    # 3. 继续执行迁移...
    print("🚀 开始OVS数据库迁移...")
```

## 🎯 实施步骤

### 第1步: 修改OVS迁移文件
为OVS迁移文件添加安全检查机制。

### 第2步: 修改SP8D迁移文件
为SP8D迁移文件添加相应的数据库检查。

### 第3步: 执行前验证
在执行迁移前，手动验证当前连接的数据库。

### 第4步: 建立标准流程
制定多数据库迁移的标准操作程序。

## 📋 验证清单

在执行 `flask db upgrade` 前，请确认：

- [ ] 当前连接的数据库确实是OVS数据库
- [ ] OVS数据库的alembic_version表为空
- [ ] OVS数据库表数量为56个
- [ ] 已有完整的数据库备份
- [ ] 迁移文件包含数据库验证逻辑

## 🚨 应急预案

如果执行错误：

1. **立即停止**: 如果发现执行了错误的迁移，立即停止
2. **检查状态**: 查看 alembic_version 表的当前状态
3. **备份恢复**: 必要时使用备份恢复数据库
4. **重置版本**: 手动修正 alembic_version 表

## 🔧 手动验证命令

```bash
# 连接OVS数据库前，先确认连接字符串
echo $DATABASE_URL

# 验证当前数据库
psql $DATABASE_URL -c "SELECT current_database(), COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"

# 检查alembic版本
psql $DATABASE_URL -c "SELECT * FROM alembic_version;"
```