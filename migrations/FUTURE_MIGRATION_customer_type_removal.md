# 未来数据库迁移计划：移除 customer_type 字段

## 📋 迁移概要

**迁移目标**: 从 `project_customer_associations` 表中移除已废弃的 `customer_type` 字段

**创建日期**: 2025-10-15

**优先级**: 低 (非紧急，可在下次主要版本更新时执行)

**影响范围**:
- 数据库表: `project_customer_associations`
- 受影响记录: 约1200条关联记录
- 相关代码: 已完成废弃标记和代码修改

---

## 🎯 废弃原因

### 1. **字段冗余**
- `customer_type` 字段重复存储了 `companies.company_type` 的信息
- 数据存在两个地方，违反数据库规范化原则

### 2. **数据不准确**
根据2025-10-15的数据分析:
- 总关联记录: 1136
- 正确的 customer_type: 1011 (89.0%)
- **错误的 customer_type: 120 (10.6%)**
- 无公司类型: 5 (0.4%)

### 3. **前端未使用**
- 前端代码 (`app/templates/project/detail.html:1851`) 显示的是 `association.company_type`
- `association.customer_type` 字段完全被忽略
- 用户看到的始终是公司的实际类型，不是关联表中存储的类型

### 4. **硬编码问题**
- 前端添加客户时曾硬编码为 `'end_user'` (已在2025-10-15修复为 `null`)
- 导致所有手动添加的关联都被错误标记为"直接用户"

---

## ✅ 已完成的准备工作

### 代码层面废弃 (2025-10-15)

#### 1. **前端修改** (`app/templates/project/detail.html:1789`)
```javascript
// 修改前:
customer_type: 'end_user'  // 默认客户类型

// 修改后:
customer_type: null  // DEPRECATED: 该字段已废弃，前端使用 company.company_type
```

#### 2. **后端API修改** (`app/views/project.py:3391-3409`)
```python
# customer_type 改为可选参数，不再是必需参数
customer_type = data.get('customer_type', None)  # DEPRECATED: 该字段已废弃，允许为空
if not all([project_id, company_id]):  # customer_type 不再检查
    return jsonify({'success': False, 'message': '缺少必要参数'}), 400

# 允许 None 值
valid_types = ['end_user', 'design_issues', 'contractor', 'system_integrator', 'dealer', None]
```

#### 3. **模型更新** (`app/models/project_customer_association.py:16-20`)
```python
# DEPRECATED: customer_type 字段已废弃，前端显示使用 company.company_type
# 该字段冗余存储且经常不准确，计划在未来迁移时删除
# 目前保留以向后兼容，但新记录可以设置为 NULL
customer_type = db.Column(db.String(50), nullable=True)  # DEPRECATED
```

### 数据清理 (2025-10-15)

#### 1. **重复关联删除**
- 删除了41条重复的关联记录 (同一项目中同一公司ID重复)
- 保留策略: 每组保留最早创建的记录
- 详细记录: `scripts/temp/fix_duplicates_result.json`

#### 2. **保留的数据问题** (暂不处理)
- 120条不准确的 `customer_type` 值: 保留原样，因为前端不使用
- 5条 `customer_type` 为 NULL 的记录: 正常，符合新规范
- 92个项目有重复公司名称 (不同ID): 需人工审核，与本次迁移无关

---

## 🔧 迁移步骤

### 执行时机
- **推荐**: 下一个主要版本更新 (如 v3.0.0)
- **前提**: 确认所有代码已不再使用 `customer_type` 字段

### 迁移脚本模板

```python
"""移除 project_customer_associations.customer_type 字段

Revision ID: remove_customer_type_YYYYMMDD
Revises: <previous_revision>
Create Date: YYYY-MM-DD HH:MM:SS

说明:
- customer_type 字段已在代码中废弃 (2025-10-15)
- 前端使用 company.company_type 显示客户类型
- 该字段冗余且数据不准确，安全删除
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_customer_type_YYYYMMDD'
down_revision = '<previous_revision>'
branch_labels = None
depends_on = None

def upgrade():
    # 1. 先移除依赖该字段的唯一约束
    op.drop_constraint(
        'unique_project_company_type',
        'project_customer_associations',
        type_='unique'
    )

    # 2. 创建新的唯一约束 (不包含 customer_type)
    op.create_unique_constraint(
        'unique_project_company',
        'project_customer_associations',
        ['project_id', 'company_id']
    )

    # 3. 删除 customer_type 列
    op.drop_column('project_customer_associations', 'customer_type')

def downgrade():
    # 1. 恢复 customer_type 列
    op.add_column(
        'project_customer_associations',
        sa.Column('customer_type', sa.String(50), nullable=True)
    )

    # 2. 移除新的唯一约束
    op.drop_constraint(
        'unique_project_company',
        'project_customer_associations',
        type_='unique'
    )

    # 3. 恢复旧的唯一约束 (包含 customer_type)
    op.create_unique_constraint(
        'unique_project_company_type',
        'project_customer_associations',
        ['project_id', 'company_id', 'customer_type']
    )
```

### 执行前检查清单

- [ ] 确认所有环境 (本地、测试、生产) 的代码已更新到包含废弃标记的版本
- [ ] 全局搜索代码，确认没有地方引用 `association.customer_type`
- [ ] 备份生产数据库 (使用 `backup_cloud_pma_db.py`)
- [ ] 在测试环境执行迁移并验证
- [ ] 检查 API 响应，确认 `customer_type` 字段不再返回

### 执行命令

```bash
# 1. 创建迁移脚本
python3 standard_migration_upgrade.py

# 2. 执行测试环境迁移
FLASK_ENV=testing alembic upgrade head

# 3. 验证测试环境功能正常

# 4. 执行生产环境迁移
FLASK_ENV=production alembic upgrade head

# 5. 清理旧备份 (可选)
```

---

## ⚠️ 风险评估

### 低风险 ✅
- **代码已准备**: 字段已标记为 DEPRECATED，新代码不使用
- **前端无影响**: 前端显示 `company.company_type`，不依赖该字段
- **向后兼容**: 字段改为 nullable，旧代码仍可运行
- **可回滚**: 迁移脚本包含 downgrade 方法

### 需要注意 ⚠️
- **唯一约束变化**: 旧约束 `(project_id, company_id, customer_type)` → 新约束 `(project_id, company_id)`
  - **影响**: 删除字段后，同一项目不能重复关联同一公司 (无论类型)
  - **评估**: 这是期望行为，与当前前端逻辑一致
- **API 响应变化**: 后端 API 可能仍返回 `customer_type` 字段
  - **建议**: 迁移前先从 API 响应中移除该字段

### 相关代码需同步更新

#### 1. **API 响应** (`app/views/project.py:3315-3325`)
```python
# 当前代码 (需修改):
associations_data.append({
    'id': assoc.id,
    'company_id': assoc.company_id,
    'company_name': company.company_name,
    'customer_type': assoc.customer_type,  # ❌ 迁移前应移除
    'customer_type_label': assoc.customer_type_label,  # ❌ 迁移前应移除
    'company_type': company.company_type,  # ✅ 保留
    # ...
})

# 建议改为:
associations_data.append({
    'id': assoc.id,
    'company_id': assoc.company_id,
    'company_name': company.company_name,
    'company_type': company.company_type,  # ✅ 只返回公司实际类型
    # ...
})
```

#### 2. **模型属性** (`app/models/project_customer_association.py:39-49`)
```python
# 当前代码 (建议删除整个属性):
@property
def customer_type_label(self):
    """获取客户类型的中文标签"""
    type_labels = {
        'end_user': '直接用户',
        'design_issues': '设计院及顾问',
        'contractor': '总承包单位',
        'system_integrator': '系统集成商',
        'dealer': '经销商'
    }
    return type_labels.get(self.customer_type, self.customer_type)
```

#### 3. **模型方法** (`app/models/project_customer_association.py:64-93`)
```python
# add_association 方法需移除 customer_type 参数
@classmethod
def add_association(cls, project_id, company_id, created_by=None):  # 移除 customer_type
    """添加项目-客户关联"""
    # 检查是否已存在相同的关联 (只检查 project_id + company_id)
    existing = cls.query.filter_by(
        project_id=project_id,
        company_id=company_id
    ).first()

    if existing:
        return False, "该客户已经关联到项目中"

    # 创建新关联 (不传 customer_type)
    association = cls(
        project_id=project_id,
        company_id=company_id,
        created_by=created_by
    )

    db.session.add(association)
    return True, association
```

---

## 📊 迁移后效果

### 数据库层面
- ✅ 移除冗余字段，减少存储空间
- ✅ 消除数据不一致风险
- ✅ 简化唯一约束逻辑
- ✅ 表结构更清晰

### 代码层面
- ✅ 移除 DEPRECATED 标记和相关注释
- ✅ 删除 `customer_type_label` 属性
- ✅ 简化 API 响应结构
- ✅ 清理类型映射字典

### 用户体验
- ✅ 无影响 (前端已使用 company.company_type)
- ✅ 数据更准确 (直接从公司表读取)
- ✅ 避免混淆 (只有一个"客户类型"来源)

---

## 📝 相关文档

- **废弃代码提交**: git log 搜索 "DEPRECATED: customer_type"
- **重复清理记录**: `scripts/temp/fix_duplicates_result.json`
- **检查脚本**: `scripts/temp/check_special_settlements.py`
- **分析报告**: 本会话的conversation summary

---

## ✅ 执行确认

迁移完成后，请在此记录：

- **执行日期**: ___________
- **执行人**: ___________
- **迁移脚本版本**: ___________
- **备份文件路径**: ___________
- **验证结果**: [ ] 通过 / [ ] 失败
- **回滚**: [ ] 不需要 / [ ] 已回滚
- **备注**: ___________

---

**文档版本**: 1.0
**最后更新**: 2025-10-15
**维护人**: 系统管理员
