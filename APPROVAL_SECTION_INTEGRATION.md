# 审批区域集成总结

## 概述
将审批中心的审批详情页面功能合并到各个业务模块的详情页面中，在详情页面底部显示审批区域，包含审批基本信息和审批流程图，不包含进度摘要。

## 实现方案

### 1. 创建通用审批区域宏
- **文件**: `app/templates/macros/approval_macros.html`
- **宏名称**: `render_approval_section`
- **功能**: 
  - 显示审批基本信息（审批编号、流程名称、发起人、状态等）
  - 显示当前步骤信息（如果审批进行中）
  - 显示审批流程图（时间线形式）
  - 提供审批操作按钮（如果当前用户可以审批）
  - 显示发起审批按钮（如果没有审批实例）

### 2. 更新模板导入
- **项目详情页面**: `app/templates/project/detail.html`
  - 添加 `render_approval_section` 宏导入
  - 替换原有审批流程区域为新宏调用
- **报价单详情页面**: `app/templates/quotation/detail.html`
  - 添加 `render_approval_section` 宏导入
  - 替换原有审批和审核操作区域为新宏调用

### 3. 添加辅助函数
- **文件**: `app/helpers/approval_helpers.py`
- **新增函数**:
  - `get_workflow_steps(approval_instance)`: 获取审批流程步骤信息
  - `render_approval_code(instance_id)`: 渲染审批编号

### 4. 更新上下文处理器
- **文件**: `app/context_processors.py`
- **更新内容**: 
  - 添加新函数到导入列表
  - 在 `inject_approval_functions` 中返回新函数
  - 确保模板可以访问所有必要的审批相关函数

## 功能特性

### 审批区域显示内容
1. **审批基本信息卡片**:
   - 审批编号（APV-XXXX格式）
   - 流程名称
   - 发起人
   - 发起时间
   - 当前状态
   - 完成时间（如果已完成）

2. **当前步骤信息卡片**（审批进行中时）:
   - 步骤名称
   - 审批人
   - 审批操作按钮（通过/拒绝）

3. **流程状态卡片**（审批完成时）:
   - 最终状态图标
   - 完成时间

4. **审批流程图**:
   - 时间线形式显示所有步骤
   - 区分已完成、当前、未开始步骤
   - 显示审批时间和意见
   - 显示最终结果

### 交互功能
- **审批操作**: 当前审批人可直接在详情页面进行审批
- **模态框审批**: 提供审批意见输入
- **AJAX提交**: 无需页面刷新完成审批操作

## 技术实现

### 宏参数
```jinja2
{{ render_approval_section(object_type, object_id, approval_instance, current_user) }}
```
- `object_type`: 业务对象类型（'project', 'quotation'等）
- `object_id`: 业务对象ID
- `approval_instance`: 审批实例对象（可选）
- `current_user`: 当前用户对象

### 样式和布局
- 使用Bootstrap卡片组件
- 响应式布局（左右分栏）
- 时间线样式显示流程图
- 状态颜色区分（成功/警告/危险）

### JavaScript功能
- 审批模态框控制
- AJAX审批提交
- 页面刷新机制

## 使用方法

### 在新模块中集成审批区域
1. 在模板中导入宏：
```jinja2
{% from 'macros/approval_macros.html' import render_approval_section with context %}
```

2. 在详情页面底部添加审批区域：
```jinja2
<!-- 审批流程区域 -->
{% set approval_instance = get_object_approval_instance('module_name', object.id) if get_object_approval_instance is defined %}
{{ render_approval_section('module_name', object.id, approval_instance, current_user) }}
```

3. 确保视图函数提供必要的上下文变量

## 优势

1. **统一体验**: 所有模块的审批功能保持一致
2. **减少跳转**: 用户无需跳转到审批中心即可查看和操作审批
3. **代码复用**: 通过宏实现代码复用，便于维护
4. **扩展性强**: 新模块可轻松集成审批功能
5. **功能完整**: 包含查看、操作、历史记录等完整功能

## 已集成模块

- ✅ 项目管理模块 (`app/templates/project/detail.html`)
- ✅ 报价单模块 (`app/templates/quotation/detail.html`)

## 后续扩展

可以按照相同方式为其他业务模块（如客户管理、产品管理等）集成审批区域功能。 