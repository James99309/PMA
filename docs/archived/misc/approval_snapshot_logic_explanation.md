# 审批系统中的快照逻辑与审批逻辑关系详解

## 1. 为什么需要快照逻辑？

### 问题背景
在动态的业务环境中，审批模板可能会经常调整：
- 新增审批步骤
- 修改审批人
- 调整步骤顺序
- 变更审批条件

**如果没有快照逻辑会发生什么？**
```
时间线：
Day 1: 用户提交报销单 BX001，使用模板 V1.0（3个步骤）
Day 5: 管理员修改模板为 V2.0（4个步骤）
Day 10: BX001 进行第2步审批时...

问题：
❌ 系统读取当前模板 V2.0（4步骤）
❌ 但审批实例记录显示已完成1步，当前第2步
❌ 新模板的第2步可能是完全不同的步骤！
❌ 审批人、步骤名称、流程逻辑全部错乱
```

### 快照逻辑的解决方案
```
Day 1: 用户提交报销单 BX001
       ↓
       系统创建审批实例，同时保存模板快照
       ↓
       template_snapshot = {
         "template_id": 30,
         "template_name": "报销单流程",
         "created_at": "2025-08-05T14:16:33",
         "steps": [
           {"step_id": 33, "step_order": 1, "step_name": "上级审批"},
           {"step_id": 34, "step_order": 2, "step_name": "财务审批"},
           {"step_id": 35, "step_order": 3, "step_name": "总经理审核"}
         ]
       }

Day 5: 管理员修改模板（不影响已有实例）
Day 10: BX001 审批时仍使用创建时的快照
        ✅ 流程保持一致性
        ✅ 审批逻辑不会混乱
```

## 2. 数据模型设计

### 审批模板表 (approval_process_template)
```sql
-- 当前活跃的模板定义
CREATE TABLE approval_process_template (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),           -- 模板名称
    object_type VARCHAR(50),     -- 适用对象类型
    is_active BOOLEAN,           -- 是否启用
    created_at TIMESTAMP
);
```

### 审批步骤表 (approval_step)
```sql
-- 模板的步骤定义
CREATE TABLE approval_step (
    id INTEGER PRIMARY KEY,
    process_id INTEGER,          -- 关联模板ID
    step_order INTEGER,          -- 步骤顺序 (1,2,3,4...)
    step_name VARCHAR(100),      -- 步骤名称
    approver_type VARCHAR(20),   -- 审批人类型
    approver_user_id INTEGER,    -- 固定审批人ID
    action_type VARCHAR(50)      -- 步骤动作类型
);
```

### 审批实例表 (approval_instance) - 关键！
```sql
-- 具体的审批流程实例
CREATE TABLE approval_instance (
    id INTEGER PRIMARY KEY,
    process_id INTEGER,          -- 原始模板ID（用于回溯）
    object_id INTEGER,           -- 业务对象ID
    object_type VARCHAR(50),     -- 业务对象类型
    current_step INTEGER,        -- 当前步骤顺序（step_order）
    status ENUM,                 -- 实例状态
    
    -- 🔥 快照字段 - 这是核心！
    template_snapshot JSON,      -- 创建时的完整模板快照
    template_version VARCHAR(50), -- 模板版本号
    
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);
```

### 审批记录表 (approval_record)
```sql
-- 每次审批操作的记录
CREATE TABLE approval_record (
    id INTEGER PRIMARY KEY,
    instance_id INTEGER,         -- 审批实例ID
    step_id INTEGER,            -- 对应的步骤ID（快照中的step_id）
    approver_id INTEGER,        -- 审批人ID
    action VARCHAR(50),         -- approve/reject
    comment TEXT,               -- 审批意见
    timestamp TIMESTAMP         -- 审批时间
);
```

## 3. 核心逻辑关系

### A. 审批实例创建时的快照逻辑

```python
def start_approval_process(template_id, object_id, object_type, user_id):
    """发起审批流程"""
    
    # 1. 获取当前模板
    template = ApprovalProcessTemplate.query.get(template_id)
    steps = ApprovalStep.query.filter_by(process_id=template_id).order_by(ApprovalStep.step_order.asc()).all()
    
    # 2. 🔥 创建模板快照
    template_snapshot = {
        "template_id": template.id,
        "template_name": template.name,
        "object_type": template.object_type,
        "created_at": datetime.now().isoformat(),
        "steps": []
    }
    
    # 3. 快照所有步骤信息
    for step in steps:
        step_data = {
            "step_id": step.id,
            "step_order": step.step_order,
            "step_name": step.step_name,
            "approver_type": step.approver_type,
            "approver_user_id": step.approver_user_id,
            "approver_username": step.approver.username if step.approver else None,
            "approver_real_name": step.approver.real_name if step.approver else None,
            "action_type": step.action_type,
            "send_email": step.send_email,
            # ... 其他字段
        }
        template_snapshot["steps"].append(step_data)
    
    # 4. 创建审批实例，保存快照
    instance = ApprovalInstance(
        process_id=template_id,
        object_id=object_id,
        object_type=object_type,
        current_step=1,  # 从第1步开始
        status=ApprovalStatus.PENDING,
        template_snapshot=template_snapshot,  # 🔥 保存快照
        template_version=f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        started_at=datetime.now(),
        created_by=user_id
    )
    
    return instance
```

### B. 审批过程中的步骤信息获取

```python
class ApprovalInstance(db.Model):
    """审批实例模型"""
    
    def get_steps(self):
        """获取审批步骤 - 优先使用快照"""
        if self.template_snapshot and 'steps' in self.template_snapshot:
            # 🔥 使用创建时的快照（推荐）
            return self.template_snapshot['steps']
        else:
            # 回退到当前模板（兼容旧数据）
            return ApprovalStep.query.filter_by(
                process_id=self.process_id
            ).order_by(ApprovalStep.step_order.asc()).all()
    
    def get_current_step_info(self):
        """获取当前步骤信息"""
        steps = self.get_steps()
        if isinstance(steps, list) and len(steps) > 0:
            # 快照数据（字典列表）
            if isinstance(steps[0], dict):
                for step in steps:
                    # 🔥 关键：current_step存储的是step_order
                    if step.get('step_order') == self.current_step:
                        return step
            # 模型对象列表（兼容模式）
            else:
                for step in steps:
                    if step.step_order == self.current_step:
                        return step
        return None
```

### C. 审批权限检查逻辑

```python
def can_user_approve(instance_id, user_id):
    """检查用户是否可以审批当前步骤"""
    
    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    # 🔥 关键：使用快照中的步骤信息
    current_step = instance.get_current_step_info()
    if not current_step:
        return False
    
    # 🔥 基于快照数据确定实际审批人
    actual_approver = get_step_actual_approver(current_step, instance)
    return actual_approver and actual_approver.id == user_id
```

### D. 审批流程推进逻辑

```python
def process_approval(instance_id, action, comment=None, user_id=None):
    """处理审批操作"""
    
    instance = ApprovalInstance.query.get(instance_id)
    
    # 1. 🔥 获取当前步骤信息（基于快照）
    current_step = instance.get_current_step_info()
    
    # 2. 权限检查
    actual_approver = get_step_actual_approver(current_step, instance)
    if not actual_approver or actual_approver.id != user_id:
        return False
    
    # 3. 创建审批记录
    record = ApprovalRecord(
        instance_id=instance.id,
        step_id=current_step.get('step_id'),  # 🔥 使用快照中的step_id
        approver_id=user_id,
        action=action.value,
        comment=comment,
        timestamp=datetime.now()
    )
    
    # 4. 推进流程
    if action == ApprovalAction.APPROVE:
        # 🔥 获取下一步骤（基于快照）
        next_step = _get_next_step_from_snapshot(instance, current_step)
        if next_step:
            instance.current_step = next_step['step_order']  # 🔥 更新到下一步
        else:
            # 流程完成
            instance.status = ApprovalStatus.APPROVED
            instance.ended_at = datetime.now()
    
    return True
```

## 4. 关键字段说明

### current_step 字段的含义
```python
# current_step 存储的是 step_order（步骤顺序），不是 step_id
instance.current_step = 1  # 表示当前在第1步
instance.current_step = 2  # 表示当前在第2步
instance.current_step = 3  # 表示当前在第3步

# 匹配逻辑：
def get_current_step_info(self):
    for step in self.template_snapshot['steps']:
        if step['step_order'] == self.current_step:  # 🔥 用step_order匹配
            return step
```

### step_id vs step_order 的区别
```json
{
  "steps": [
    {
      "step_id": 33,        // 数据库中的唯一ID（可能会变）
      "step_order": 1,      // 在流程中的顺序位置（稳定）
      "step_name": "上级审批"
    },
    {
      "step_id": 34,        // 数据库中的唯一ID
      "step_order": 2,      // 在流程中的顺序位置
      "step_name": "财务审批"
    }
  ]
}
```

## 5. 工作流显示逻辑

### get_workflow_steps 函数
```python
def get_workflow_steps(approval_instance):
    """获取工作流步骤显示信息"""
    
    # 🔥 使用快照数据，不是当前模板
    template_steps = approval_instance.get_steps()
    current_step_order = approval_instance.current_step
    
    for step in template_steps:
        step_order = step.get('step_order')
        
        # 🔥 基于step_order判断状态
        is_completed = step_order < current_step_order  # 已完成
        is_current = step_order == current_step_order   # 当前步骤
        
        # 显示逻辑：
        if is_completed:
            display = "绿色打勾 ✅"
        elif is_current:
            display = "橘色当前状态 🔄"
        else:
            display = "灰色待审批 ⏳"
```

## 6. 常见问题和解决方案

### 问题1：步骤信息不匹配
```python
# ❌ 错误：使用当前模板
def wrong_approach(instance):
    current_step = ApprovalStep.query.filter_by(
        process_id=instance.process_id,
        step_order=instance.current_step
    ).first()
    # 可能获取到修改后的步骤信息！

# ✅ 正确：使用快照
def correct_approach(instance):
    current_step = instance.get_current_step_info()
    # 获取创建时的步骤信息，保证一致性
```

### 问题2：权限判断错误
```python
# ❌ 错误：基于当前模板判断权限
def wrong_permission_check(instance, user_id):
    template_step = get_current_template_step(instance)  # 可能已变化
    return template_step.approver_user_id == user_id

# ✅ 正确：基于快照判断权限
def correct_permission_check(instance, user_id):
    snapshot_step = instance.get_current_step_info()    # 创建时的信息
    actual_approver = get_step_actual_approver(snapshot_step, instance)
    return actual_approver and actual_approver.id == user_id
```

### 问题3：审批记录关联错误
```python
# 审批记录需要正确关联到快照中的step_id
record = ApprovalRecord(
    instance_id=instance.id,
    step_id=current_step.get('step_id'),  # 🔥 使用快照中的step_id
    approver_id=user_id,
    action=action,
    timestamp=datetime.now()
)
```

## 7. 最佳实践

### 代码规范
1. **总是使用快照数据**：`instance.get_current_step_info()`
2. **避免直接查询当前模板**：不要用 `ApprovalStep.query.filter_by(...)`
3. **step_order匹配current_step**：不要用step_id匹配
4. **保持数据完整性**：审批记录要正确关联step_id

### 系统设计原则
1. **版本隔离**：每个审批实例独立于模板变更
2. **向后兼容**：支持没有快照的旧数据
3. **数据一致性**：快照数据与审批记录相关联
4. **权限准确性**：基于创建时的权限规则

## 8. 总结

快照逻辑是审批系统的核心设计模式，它解决了以下关键问题：

1. **时间一致性**：确保长期流程不会因模板变更而混乱
2. **权限稳定性**：审批权限基于创建时的规则，不会中途改变
3. **流程完整性**：整个审批过程使用一致的步骤定义
4. **数据关联性**：审批记录与步骤的正确关联

通过快照逻辑，我们实现了一个健壮、可靠的审批系统，能够在动态变化的业务环境中保持稳定的运行。