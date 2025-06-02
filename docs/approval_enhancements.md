# 审批流程增强功能

## 概述

本次更新为审批流程系统添加了三个重要的增强功能：

1. **对象锁定机制** - 发起审批后自动锁定对象编辑
2. **步骤字段编辑权限** - 在特定审批步骤允许编辑指定字段
3. **邮件抄送功能** - 审批过程中自动发送邮件给指定用户

## 功能详情

### 1. 对象锁定机制

#### 功能描述
- 当发起审批流程时，系统可以自动锁定被审批对象的所有编辑功能
- 直到审批流程结束（通过或拒绝）才解锁对象
- 支持自定义锁定原因说明

#### 配置选项
- `lock_object_on_start`: 是否在发起审批后锁定对象（默认：True）
- `lock_reason`: 锁定原因说明（默认："审批流程进行中，暂时锁定编辑"）

#### 支持的对象类型
- 项目（Project）
- 报价单（Quotation）
- 客户（Customer）

### 2. 步骤字段编辑权限

#### 功能描述
- 在审批流程的特定步骤中，允许审批人编辑指定的字段
- 即使对象被锁定，审批人仍可编辑被授权的字段
- 支持为每个审批步骤配置不同的可编辑字段列表

#### 配置选项
- `editable_fields`: 在当前步骤可编辑的字段列表（JSON数组）

#### 权限检查
- 系统提供 `check_field_editable()` 函数检查字段编辑权限
- 考虑当前用户、审批状态、步骤权限等因素

### 3. 邮件抄送功能

#### 功能描述
- 在审批步骤完成时，自动发送邮件通知给指定的抄送用户
- 支持为每个审批步骤配置不同的抄送用户列表
- 邮件内容包含审批结果、意见和业务对象信息

#### 配置选项
- `cc_enabled`: 是否启用邮件抄送（默认：False）
- `cc_users`: 邮件抄送用户ID列表（JSON数组）

#### 邮件内容
- 审批对象信息
- 审批结果（同意/拒绝）
- 审批意见
- 审批人信息
- 审批时间

## 数据库变更

### 审批流程模板表 (approval_process_template)
```sql
-- 新增字段
ALTER TABLE approval_process_template 
ADD COLUMN lock_object_on_start BOOLEAN DEFAULT TRUE;

ALTER TABLE approval_process_template 
ADD COLUMN lock_reason VARCHAR(200) DEFAULT '审批流程进行中，暂时锁定编辑';
```

### 审批步骤表 (approval_step)
```sql
-- 新增字段
ALTER TABLE approval_step 
ADD COLUMN editable_fields JSON DEFAULT '[]';

ALTER TABLE approval_step 
ADD COLUMN cc_users JSON DEFAULT '[]';

ALTER TABLE approval_step 
ADD COLUMN cc_enabled BOOLEAN DEFAULT FALSE;
```

## API 变更

### 创建审批模板
```python
create_approval_template(
    name="项目审批流程",
    object_type="project",
    creator_id=1,
    required_fields=["project_name", "project_description"],
    lock_object_on_start=True,  # 新增
    lock_reason="审批中，禁止编辑"  # 新增
)
```

### 添加审批步骤
```python
add_approval_step(
    template_id=1,
    step_name="项目经理审批",
    approver_id=2,
    send_email=True,
    editable_fields=["project_budget", "project_timeline"],  # 新增
    cc_users=[3, 4],  # 新增
    cc_enabled=True  # 新增
)
```

### 字段编辑权限检查
```python
can_edit = check_field_editable(
    object_type="project",
    object_id=123,
    field_name="project_budget",
    user_id=2
)
```

## 前端界面变更

### 审批模板配置页面
- 添加了"对象锁定配置"区域
- 包含锁定开关和锁定原因输入框

### 审批步骤配置页面
- 添加了"可编辑字段"选择区域
- 添加了"邮件抄送"配置区域
- 支持多选字段和用户

### 审批步骤列表显示
- 显示可编辑字段标签
- 显示邮件抄送用户信息
- 显示动作类型（包括邮件抄送）

## 使用示例

### 配置项目审批流程

1. **创建审批模板**
   - 模板名称：项目立项审批
   - 业务对象：项目
   - 必填字段：项目名称、项目描述
   - 对象锁定：启用
   - 锁定原因：项目审批中，暂时锁定编辑

2. **添加审批步骤**
   
   **步骤1：部门经理审批**
   - 审批人：部门经理
   - 可编辑字段：项目预算、项目时间线
   - 邮件抄送：项目组成员
   
   **步骤2：总经理审批**
   - 审批人：总经理
   - 可编辑字段：项目优先级
   - 邮件抄送：财务部门

### 审批流程执行

1. **发起审批**
   - 项目被自动锁定，无法编辑
   - 通知第一步审批人

2. **部门经理审批**
   - 可以编辑项目预算和时间线
   - 审批完成后发送邮件给项目组成员

3. **总经理审批**
   - 可以编辑项目优先级
   - 审批完成后发送邮件给财务部门
   - 审批通过后项目自动解锁

## 技术实现

### 核心函数

- `start_approval_process()`: 发起审批时处理对象锁定
- `process_approval()`: 处理审批时检查字段权限和发送抄送邮件
- `_lock_approval_object()`: 锁定业务对象
- `_unlock_approval_object()`: 解锁业务对象
- `_send_approval_cc_email()`: 发送审批抄送邮件
- `check_field_editable()`: 检查字段编辑权限

### 邮件模板

系统使用现有的邮件发送机制，邮件内容包含：
- 审批对象基本信息
- 审批结果和意见
- 审批人和时间信息
- 相关链接

## 兼容性

- 所有新字段都有默认值，不影响现有数据
- 现有审批流程继续正常工作
- 新功能为可选配置，默认行为保持不变

## 测试验证

所有功能已通过完整测试：
- ✅ 对象锁定和解锁机制
- ✅ 字段编辑权限检查
- ✅ 邮件抄送功能
- ✅ 数据库字段存储
- ✅ API接口调用
- ✅ 前端界面配置

## 后续优化

1. 支持更细粒度的字段权限控制
2. 添加审批流程模板复制功能
3. 支持条件分支审批流程
4. 增加审批统计和报表功能 