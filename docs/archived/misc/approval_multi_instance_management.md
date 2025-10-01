# 审批系统多实例管理机制详解

## 🎯 核心原则

**一个业务对象（报销单）在同一时间只能有一个活跃的审批实例**

## 📊 实例状态生命周期

```
创建审批实例
    ↓
PENDING (审批中)
    ↓
三种结束状态：
├─ APPROVED (审批通过)
├─ REJECTED (审批拒绝)  
└─ RECALLED (流程召回)
```

## 🔄 多实例产生场景

### 场景1：正常流程完成后重新发起
```
BX001 → 实例1 (APPROVED) → 修改报销单 → 实例2 (PENDING)
```

### 场景2：拒绝后重新发起
```
BX001 → 实例1 (REJECTED) → 修改报销单 → 实例2 (PENDING)
```

### 场景3：召回后重新发起 ⭐ 主要场景
```
BX001 → 实例1 (PENDING) → 召回 → 实例1 (RECALLED) → 重新发起 → 实例2 (PENDING)
```

## 🔍 实际数据分析

### BX2025080412 的完整时间线：
```
实例121: 19:50:36 创建 → 20:10:48 召回 (RECALLED)
实例124: 20:16:43 创建 → 20:16:49 召回 (RECALLED) 
实例125: 20:23:23 创建 → 20:23:31 召回 (RECALLED)
实例126: 20:23:38 创建 → 20:32:10 通过 (APPROVED)
```

**分析**：用户在短时间内多次召回并重新发起，最终第4次审批通过。

## 🛠️ 多实例控制机制

### 1. 创建新实例时的检查逻辑

```python
def start_approval_process(object_type, object_id, template_id, user_id=None):
    # 🔍 检查是否存在活跃实例
    existing = get_object_approval_instance(object_type, object_id, include_rejected=False)
    
    # ❌ 如果存在PENDING或APPROVED状态的实例，禁止创建新实例
    if existing and existing.status not in [ApprovalStatus.RECALLED, ApprovalStatus.REJECTED]:
        return None  # 创建失败
    
    # ✅ 如果存在RECALLED或REJECTED状态的实例，允许创建新实例
    if existing and existing.status in [ApprovalStatus.RECALLED, ApprovalStatus.REJECTED]:
        # 旧实例保持原状态，创建新实例
        pass
    
    # 创建新的审批实例...
```

### 2. 获取当前活跃实例的逻辑

```python
def get_object_approval_instance(object_type, object_id, include_rejected=False):
    query = ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id
    )
    
    if not include_rejected:
        # 🔍 只返回活跃状态的实例（PENDING、APPROVED）
        query = query.filter(
            ApprovalInstance.status.in_([
                ApprovalStatus.PENDING,
                ApprovalStatus.APPROVED
            ])
        )
    
    # 按创建时间倒序，返回最新的实例
    return query.order_by(ApprovalInstance.started_at.desc()).first()
```

## 🚨 关键判断规则

### 活跃状态 vs 非活跃状态

**活跃状态** (阻止创建新实例):
- `PENDING` - 审批进行中
- `APPROVED` - 已通过（通常不需要重新审批）

**非活跃状态** (允许创建新实例):
- `RECALLED` - 已召回，流程终止
- `REJECTED` - 已拒绝，流程终止

### 实例优先级

**当存在多个实例时，系统如何选择？**

```python
# 1. 默认获取：只考虑活跃状态，按时间倒序
instance = get_object_approval_instance('expense', expense_id)  # 最新的PENDING或APPROVED

# 2. 完整获取：包含所有状态，按时间倒序  
all_instances = get_object_approval_instance('expense', expense_id, include_rejected=True)
```

## 🔧 召回机制详解

### 两种召回函数

#### 1. `recall_approval()` - 标准召回
```python
def recall_approval(object_type, object_id, user_id, reason=None):
    # ❌ 错误：设置为REJECTED状态
    approval_instance.status = ApprovalStatus.REJECTED
    
    # 添加召回记录
    recall_record = ApprovalRecord(action='recall', ...)
```

#### 2. `recall_approval_process()` - 新版召回  
```python
def recall_approval_process(object_type, object_id, user_id=None):
    # ✅ 正确：设置为RECALLED状态
    instance.status = ApprovalStatus.RECALLED
    
    # 更新业务对象状态为草稿
    expense.status = 'draft'
```

### 召回权限控制

```python
def can_recall_approval(object_type, object_id, user_id):
    instance = get_object_approval_instance(object_type, object_id)
    
    # 只有PENDING状态的实例可以召回
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    # 只有创建者可以召回
    if instance.created_by != user_id:
        return False
        
    return True
```

## 📋 业务对象状态联动

### 报销单状态与审批实例状态的关系

| 审批实例状态 | 报销单状态 | 是否锁定 | 说明 |
|------------|-----------|----------|------|
| PENDING    | pending   | ✅ 锁定   | 审批中，不可编辑 |
| APPROVED   | approved  | ❌ 解锁   | 审批通过，可进入支付流程 |
| REJECTED   | draft     | ❌ 解锁   | 审批拒绝，可重新编辑 |
| RECALLED   | draft     | ❌ 解锁   | 流程召回，可重新编辑 |

## 🎯 最佳实践

### 1. 实例查询原则
```python
# ✅ 获取当前活跃实例（用于审批操作）
active_instance = get_object_approval_instance('expense', expense_id)

# ✅ 获取完整历史（用于历史查看）
all_instances = ApprovalInstance.query.filter_by(
    object_type='expense', 
    object_id=expense_id
).order_by(ApprovalInstance.started_at.desc()).all()
```

### 2. 状态检查原则
```python
# ✅ 检查是否可以发起新审批
def can_start_new_approval(object_type, object_id):
    existing = get_object_approval_instance(object_type, object_id)
    return existing is None or existing.status in [ApprovalStatus.RECALLED, ApprovalStatus.REJECTED]

# ✅ 检查是否可以执行操作
def can_operate_approval(object_type, object_id):
    instance = get_object_approval_instance(object_type, object_id)
    return instance and instance.status == ApprovalStatus.PENDING
```

### 3. 历史记录管理
```python
# ✅ 保留所有历史实例，通过状态区分
# 不删除旧实例，保持完整的审批历史
```

## 🔍 常见问题解答

### Q1: 召回后的旧实例还有用吗？
**A**: 有用！用于：
- 审批历史追踪
- 操作日志记录  
- 数据审计
- 问题排查

### Q2: 如何确定当前应该使用哪个实例？
**A**: 使用 `get_object_approval_instance()` 获取最新的活跃实例，系统会自动排除RECALLED和REJECTED状态的实例。

### Q3: 为什么不直接删除旧实例？
**A**: 
- 保持数据完整性
- 审计追踪需要
- 问题排查需要
- 合规要求

### Q4: 多个PENDING实例会冲突吗？
**A**: 不会。系统设计保证同一时间只能有一个PENDING实例。创建新实例前会检查并阻止冲突。

## 📊 总结

1. **单一活跃原则**: 一个业务对象同时只有一个活跃审批实例
2. **状态驱动**: 通过实例状态控制流程行为
3. **历史保留**: 所有实例都保留，用于审计和追踪
4. **权限控制**: 严格的召回和重新发起权限控制
5. **状态联动**: 审批状态与业务对象状态保持同步

这种设计确保了审批流程的完整性、可追溯性和数据一致性。