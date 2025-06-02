# 审批模板版本化解决方案

## 方案概述

实现审批模板的版本化管理，允许删除/修改步骤而不影响已创建的审批实例，新实例使用最新模板配置。

## 技术实现方案

### 方案1：模板快照机制（推荐）

#### 1.1 数据库结构调整

**新增字段到 ApprovalInstance 表：**
```sql
ALTER TABLE approval_instance ADD COLUMN template_snapshot JSON COMMENT '创建时的模板快照';
ALTER TABLE approval_instance ADD COLUMN template_version VARCHAR(50) COMMENT '模板版本号';
```

**ApprovalInstance 模型修改：**
```python
class ApprovalInstance(db.Model):
    # ... 现有字段 ...
    template_snapshot = db.Column(db.JSON, comment='创建时的模板快照')
    template_version = db.Column(db.String(50), comment='模板版本号')
    
    def get_steps(self):
        """获取审批步骤 - 优先使用快照"""
        if self.template_snapshot and 'steps' in self.template_snapshot:
            # 使用创建时的快照
            return self.template_snapshot['steps']
        else:
            # 回退到当前模板（兼容旧数据）
            return ApprovalStep.query.filter_by(
                process_id=self.process_id
            ).order_by(ApprovalStep.step_order.asc()).all()
```

#### 1.2 创建审批实例时保存快照

**修改 start_approval_process 函数：**
```python
def start_approval_process(object_type, object_id, template_id, user_id=None):
    # ... 现有逻辑 ...
    
    # 获取模板和步骤
    template = ApprovalProcessTemplate.query.get(template_id)
    steps = ApprovalStep.query.filter_by(
        process_id=template_id
    ).order_by(ApprovalStep.step_order.asc()).all()
    
    # 创建模板快照
    template_snapshot = {
        'template_id': template.id,
        'template_name': template.name,
        'object_type': template.object_type,
        'required_fields': template.required_fields,
        'created_at': datetime.utcnow().isoformat(),
        'steps': []
    }
    
    # 保存步骤快照
    for step in steps:
        step_data = {
            'id': step.id,
            'step_order': step.step_order,
            'step_name': step.step_name,
            'approver_user_id': step.approver_user_id,
            'approver_username': step.approver.username,
            'approver_real_name': step.approver.real_name,
            'send_email': step.send_email,
            'action_type': step.action_type,
            'editable_fields': step.editable_fields,
            'cc_users': step.cc_users,
            'cc_enabled': step.cc_enabled
        }
        template_snapshot['steps'].append(step_data)
    
    # 创建审批实例
    instance = ApprovalInstance(
        object_type=object_type,
        object_id=object_id,
        process_id=template_id,
        creator_id=user_id,
        status=ApprovalStatus.PENDING,
        started_at=datetime.utcnow(),
        template_snapshot=template_snapshot,
        template_version=f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # ... 其余逻辑 ...
```

#### 1.3 修改模板限制逻辑

**更新 check_template_in_use 函数：**
```python
def check_template_in_use(template_id, strict_mode=False):
    """检查审批流程模板是否正在使用
    
    Args:
        template_id: 模板ID
        strict_mode: 严格模式，True时仍然禁止修改已使用模板
        
    Returns:
        布尔值，表示模板是否有关联的审批实例
    """
    if strict_mode:
        # 严格模式：有任何关联实例就禁止修改
        return ApprovalInstance.query.filter_by(process_id=template_id).first() is not None
    else:
        # 宽松模式：只有进行中的实例才禁止修改
        return ApprovalInstance.query.filter_by(
            process_id=template_id,
            status=ApprovalStatus.PENDING
        ).first() is not None
```

#### 1.4 前端界面调整

**修改删除按钮逻辑：**
```html
<!-- 在 approval_config_macros.html 中 -->
<button type="button" class="btn btn-sm btn-danger" 
        onclick="confirmDeleteStep('{{ step.id }}')"
        {% if pending_instances_count > 0 %}disabled title="有进行中的审批流程，无法删除步骤"{% endif %}>
  <i class="fas fa-trash"></i> 删除
</button>
```

**添加版本化提示：**
```html
<div class="alert alert-info">
  <i class="fas fa-info-circle"></i>
  <strong>版本化说明：</strong>
  修改模板不会影响已创建的审批流程，新的审批流程将使用最新的模板配置。
  当前有 {{ completed_instances_count }} 个已完成实例，{{ pending_instances_count }} 个进行中实例。
</div>
```

### 方案2：模板版本表（复杂但更灵活）

#### 2.1 新增模板版本表

```sql
CREATE TABLE approval_template_version (
    id INT PRIMARY KEY AUTO_INCREMENT,
    template_id INT NOT NULL,
    version_number VARCHAR(50) NOT NULL,
    template_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (template_id) REFERENCES approval_process_template(id),
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE KEY unique_template_version (template_id, version_number)
);
```

#### 2.2 版本管理逻辑

```python
class ApprovalTemplateVersion(db.Model):
    __tablename__ = 'approval_template_version'
    
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('approval_process_template.id'))
    version_number = db.Column(db.String(50), nullable=False)
    template_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)

def create_template_version(template_id, user_id=None):
    """创建模板版本"""
    template = ApprovalProcessTemplate.query.get(template_id)
    steps = ApprovalStep.query.filter_by(process_id=template_id).all()
    
    version_data = {
        'template': template.to_dict(),
        'steps': [step.to_dict() for step in steps]
    }
    
    version = ApprovalTemplateVersion(
        template_id=template_id,
        version_number=f"v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        template_data=version_data,
        created_by=user_id
    )
    
    db.session.add(version)
    db.session.commit()
    return version
```

## 实现步骤

### 阶段1：基础架构（1-2天）
1. **数据库迁移**：添加快照字段
2. **模型更新**：修改 ApprovalInstance 模型
3. **兼容性处理**：确保现有数据正常工作

### 阶段2：核心逻辑（2-3天）
1. **快照创建**：修改 start_approval_process 函数
2. **步骤获取**：实现快照优先的步骤获取逻辑
3. **限制调整**：更新模板使用检查逻辑

### 阶段3：界面优化（1-2天）
1. **按钮状态**：调整删除按钮的禁用逻辑
2. **版本提示**：添加版本化说明和状态显示
3. **历史查看**：支持查看实例使用的模板版本

### 阶段4：测试验证（1天）
1. **功能测试**：验证新旧实例的正确性
2. **兼容性测试**：确保现有功能不受影响
3. **性能测试**：验证快照机制的性能影响

## 代码实现示例

### 修改模板详情页面逻辑

```python
@approval_config_bp.route('/process/<int:template_id>')
@login_required
@admin_required
def template_detail(template_id):
    # ... 现有逻辑 ...
    
    # 统计实例状态
    all_instances = ApprovalInstance.query.filter_by(process_id=template_id).all()
    pending_instances = [i for i in all_instances if i.status == ApprovalStatus.PENDING]
    completed_instances = [i for i in all_instances if i.status != ApprovalStatus.PENDING]
    
    # 检查是否可以修改（只有进行中的实例才禁止修改）
    can_modify = len(pending_instances) == 0
    
    return render_template(
        'approval_config/template_detail.html',
        template=template,
        steps=steps,
        users=users,
        can_modify=can_modify,
        pending_instances_count=len(pending_instances),
        completed_instances_count=len(completed_instances),
        approval_instances=approval_instances,
        get_object_field_options=get_object_field_options
    )
```

### 修改删除步骤逻辑

```python
def delete_approval_step(step_id, force=False):
    """删除审批步骤
    
    Args:
        step_id: 步骤ID
        force: 是否强制删除（忽略进行中实例检查）
    """
    step = ApprovalStep.query.get(step_id)
    if not step:
        return False
    
    template_id = step.process_id
    
    # 检查是否有进行中的审批实例
    if not force:
        pending_instances = ApprovalInstance.query.filter_by(
            process_id=template_id,
            status=ApprovalStatus.PENDING
        ).first()
        
        if pending_instances:
            current_app.logger.warning(f"无法删除步骤 {step_id}：存在进行中的审批实例")
            return False
    
    # 记录操作日志
    current_app.logger.info(f"删除审批步骤: {step.step_name} (ID: {step_id})")
    
    # 执行删除
    current_order = step.step_order
    db.session.delete(step)
    
    # 更新后续步骤的序号
    later_steps = ApprovalStep.query.filter(
        ApprovalStep.process_id == template_id,
        ApprovalStep.step_order > current_order
    ).all()
    
    for later_step in later_steps:
        later_step.step_order -= 1
    
    db.session.commit()
    return True
```

## 优势分析

### 1. 数据完整性
- ✅ 历史审批流程完全不受影响
- ✅ 审计追溯能力得到保障
- ✅ 数据一致性得到维护

### 2. 业务灵活性
- ✅ 支持模板动态调整
- ✅ 新流程使用最新配置
- ✅ 满足业务变更需求

### 3. 用户体验
- ✅ 操作更加灵活
- ✅ 减少创建新模板的需要
- ✅ 版本信息透明可见

### 4. 技术优势
- ✅ 实现相对简单
- ✅ 性能影响最小
- ✅ 向后兼容性好

## 风险评估

### 低风险
- **数据存储**：JSON快照增加少量存储空间
- **查询性能**：快照查询比关联查询更快

### 中等风险
- **数据迁移**：需要为现有实例创建快照
- **代码复杂度**：增加版本判断逻辑

### 缓解措施
1. **渐进式迁移**：分批为现有实例创建快照
2. **回退机制**：保留原有查询逻辑作为备选
3. **充分测试**：确保新旧逻辑都能正常工作

## 总结

这个版本化方案是**强烈推荐的**，它能够：

1. **解决当前问题**：允许删除/修改模板步骤
2. **保护历史数据**：已创建的实例不受影响
3. **提升用户体验**：更灵活的模板管理
4. **技术可行性高**：实现相对简单，风险可控

建议采用**方案1（模板快照机制）**，因为它实现简单、性能好、维护成本低。 