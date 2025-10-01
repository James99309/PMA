# SP8D云端数据库迁移执行计划

## 📊 当前状态分析

### **本地数据库状态**
- 当前迁移版本：`592b90d54921` (head)
- 迁移历史：完整的版本管理历史
- 数据库：PMA_local (PostgreSQL 14.17)
- 状态：✅ 稳定运行

### **SP8D云端数据库状态**
- 数据库：pma_db_sp8d (PostgreSQL 16.9)
- 缺失表：2个 (`company_assets`, `temp_products`)
- 缺失字段：15个（分布在3个表中）
- 独有字段：3个（`purchase_orders`表的审批相关字段）

---

## 🎯 迁移目标

**安全地将本地数据库的新功能结构同步到SP8D云端，同时完全保护SP8D现有的独有功能。**

---

## 📋 详细执行步骤

### **阶段一：准备和安全检查**

#### **1.1 环境准备**
```bash
# 1. 确保SP8D数据库连接正常
export SP8D_DATABASE_URL="postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"

# 2. 测试连接
psql $SP8D_DATABASE_URL -c "SELECT version();"
```

#### **1.2 备份确认**
```bash
# 确认SP8D最新备份存在
ls -la cloud_sp8d_backup_20250726_132020.sql
# 文件大小：3.16 MB ✅ 已完成

# 如需要，可以创建额外的迁移前备份
```

#### **1.3 迁移环境配置**
```bash
# 临时切换到SP8D数据库进行迁移
export DATABASE_URL=$SP8D_DATABASE_URL
flask db current  # 检查SP8D当前迁移状态
```

### **阶段二：生成迁移脚本**

#### **2.1 创建缺失表的迁移**
```bash
# 生成第一个迁移：添加缺失的表
flask db revision -m "add_missing_tables_company_assets_and_temp_products_to_sp8d"
```

#### **2.2 创建缺失字段的迁移**
```bash
# 生成第二个迁移：添加缺失的字段
flask db revision -m "add_missing_columns_to_existing_tables_in_sp8d"
```

### **阶段三：迁移脚本编写**

#### **3.1 第一个迁移脚本内容**
**文件：`migrations/versions/xxxxx_add_missing_tables_company_assets_and_temp_products_to_sp8d.py`**

```python
"""add_missing_tables_company_assets_and_temp_products_to_sp8d

Revision ID: [自动生成]
Revises: [当前SP8D版本]
Create Date: 2025-07-26

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '[自动生成]'
down_revision = None  # SP8D可能没有现有迁移历史
branch_labels = None
depends_on = None

def upgrade():
    # 创建 company_assets 表
    op.create_table('company_assets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('asset_type', sa.String(50), nullable=True),
        sa.Column('asset_content', sa.Text(), nullable=True),
        sa.Column('asset_filename', sa.String(255), nullable=True),
        sa.Column('asset_size', sa.Integer(), nullable=True),
        sa.Column('asset_mime_type', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('display_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True)
    )
    
    # 创建 temp_products 表
    op.create_table('temp_products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_name', sa.String(255), nullable=True),
        sa.Column('product_model', sa.String(255), nullable=True),
        sa.Column('product_desc', sa.Text(), nullable=True),
        sa.Column('brand', sa.String(100), nullable=True),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('product_mn', sa.String(100), nullable=True),
        sa.Column('market_price', sa.Float(), nullable=True),
        sa.Column('reference_price', sa.Float(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True)
    )
    
    # 添加外键约束（如果需要）
    op.create_foreign_key(None, 'company_assets', 'companies', 
                         ['company_id'], ['id'])

def downgrade():
    # 安全的回滚操作
    op.drop_table('temp_products')
    op.drop_table('company_assets')
```

#### **3.2 第二个迁移脚本内容**
**文件：`migrations/versions/xxxxx_add_missing_columns_to_existing_tables_in_sp8d.py`**

```python
"""add_missing_columns_to_existing_tables_in_sp8d

Revision ID: [自动生成]
Revises: [第一个迁移的ID]
Create Date: 2025-07-26

"""
from alembic import op
import sqlalchemy as sa

revision = '[自动生成]'
down_revision = '[第一个迁移的ID]'
branch_labels = None
depends_on = None

def upgrade():
    # 为 dictionaries 表添加缺失的14个字段
    with op.batch_alter_table('dictionaries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email_signature_filename', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('logo_type', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('address', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('email_signature_type', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('logo_size', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('fax', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('website', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('email_signature_size', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('email_signature_content', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('logo_content', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('postal_code', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('logo_filename', sa.String(255), nullable=True))
    
    # 为 settlement_orders 表添加缺失的字段
    with op.batch_alter_table('settlement_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('settlement_status', sa.String(50), nullable=True))
    
    # 注意：不对 purchase_orders 表做任何修改
    # SP8D的 approval_status, approval_completed_at, approval_submitted_at 字段将被保留

def downgrade():
    # 安全的回滚操作
    with op.batch_alter_table('settlement_orders', schema=None) as batch_op:
        batch_op.drop_column('settlement_status')
    
    with op.batch_alter_table('dictionaries', schema=None) as batch_op:
        batch_op.drop_column('logo_filename')
        batch_op.drop_column('email')
        batch_op.drop_column('postal_code')
        batch_op.drop_column('logo_content')
        batch_op.drop_column('email_signature_content')
        batch_op.drop_column('email_signature_size')
        batch_op.drop_column('website')
        batch_op.drop_column('fax')
        batch_op.drop_column('logo_size')
        batch_op.drop_column('email_signature_type')
        batch_op.drop_column('address')
        batch_op.drop_column('phone')
        batch_op.drop_column('logo_type')
        batch_op.drop_column('email_signature_filename')
```

### **阶段四：执行迁移**

#### **4.1 第一次迁移（添加表）**
```bash
# 确保连接到SP8D数据库
export DATABASE_URL=$SP8D_DATABASE_URL

# 执行第一个迁移
flask db upgrade

# 验证表创建
psql $SP8D_DATABASE_URL -c "\dt+ company_assets temp_products"
```

#### **4.2 第二次迁移（添加字段）**
```bash
# 执行第二个迁移
flask db upgrade

# 验证字段添加
psql $SP8D_DATABASE_URL -c "\d+ dictionaries"
psql $SP8D_DATABASE_URL -c "\d+ settlement_orders"
```

#### **4.3 验证迁移完整性**
```bash
# 检查迁移状态
flask db current

# 验证SP8D独有字段仍然存在
psql $SP8D_DATABASE_URL -c "\d+ purchase_orders" | grep approval
```

### **阶段五：验证和测试**

#### **5.1 数据完整性检查**
```sql
-- 检查新添加的表
SELECT COUNT(*) FROM company_assets;
SELECT COUNT(*) FROM temp_products;

-- 检查新添加的字段（应该都是NULL）
SELECT 
    COUNT(*) as total_records,
    COUNT(logo_content) as logo_content_count,
    COUNT(settlement_status) as settlement_status_count
FROM dictionaries, settlement_orders;

-- 验证SP8D独有字段完好
SELECT 
    COUNT(*) as total_records,
    COUNT(approval_status) as approval_status_count
FROM purchase_orders;
```

#### **5.2 约束检查**
```sql
-- 检查外键约束
SELECT 
    tc.constraint_name, 
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name IN ('company_assets', 'temp_products');
```

#### **5.3 功能测试**
```bash
# 连接应用测试（如果可能）
# 验证SP8D的审批功能是否正常
# 验证新添加的功能是否可用
```

---

## 🚨 安全措施和应急预案

### **风险控制**
1. **完整备份**：SP8D数据库已备份（3.16 MB）
2. **事务安全**：每个迁移在独立事务中执行
3. **增量操作**：只添加结构，不删除任何现有内容
4. **回滚准备**：每个迁移都有完整的downgrade函数

### **应急回滚**
```bash
# 如果需要回滚到迁移前状态
flask db downgrade [前一个版本ID]

# 或者完全回滚
flask db downgrade base
```

### **数据恢复**
```bash
# 极端情况下从备份恢复
psql $SP8D_DATABASE_URL < cloud_sp8d_backup_20250726_132020.sql
```

---

## ✅ 执行检查清单

### **迁移前检查**
- [ ] SP8D数据库连接正常
- [ ] 备份文件存在且完整
- [ ] 迁移脚本已审查
- [ ] 测试环境验证通过（如有）

### **迁移中监控**
- [ ] 第一个迁移执行成功
- [ ] 新表创建完成
- [ ] 第二个迁移执行成功
- [ ] 新字段添加完成

### **迁移后验证**
- [ ] 数据完整性检查通过
- [ ] SP8D独有功能正常
- [ ] 新功能可用
- [ ] 约束关系正确

---

## 🎯 预期结果

### **成功标准**
1. **✅ SP8D获得本地新功能**：
   - `company_assets` 表及相关功能
   - `temp_products` 表及相关功能
   - 字典表的公司Logo管理功能
   - 结算单状态管理功能

2. **✅ SP8D独有功能完全保留**：
   - `purchase_orders` 表的审批功能继续正常工作
   - 所有现有业务逻辑不受影响
   - 数据完整性得到保证

3. **✅ 系统稳定性**：
   - 零业务中断
   - 零数据丢失
   - 完整的版本管理历史

---

## 📞 支持联系

**如遇到问题，请立即停止操作并：**
1. 记录错误信息
2. 检查备份文件完整性
3. 准备回滚操作
4. 联系技术支持

---

*制定时间：2025-07-26*  
*执行负责人：系统管理员*  
*风险等级：🟢 LOW*