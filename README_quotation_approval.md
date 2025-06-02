# 报价审核功能说明

## 功能概述

为PMA项目管理系统的报价模块增加了审核功能，支持根据不同项目阶段进行相应的审核操作，并在前端显示审核状态徽章。

## 主要功能

### 1. 审核状态管理
- 支持多种审核状态：发现审核、植入审核、招标前审核、招标中审核、中标审核、批价审核、签约审核
- 每个审核状态对应不同的项目阶段
- 不允许在已获得审核的阶段重复审核

### 2. 审核徽章显示
- 在报价单列表中，报价单编号后显示审核徽章
- 在报价单详情页面，多个位置显示审核徽章
- 徽章采用不同颜色和图标区分不同审核状态

### 3. 审核权限控制
- 只有管理员和拥有 `quotation_approval` 权限的用户可以执行审核
- 系统自动检查用户权限和项目阶段状态

## 技术实现

### 数据库变更
- 在 `quotations` 表添加了三个字段：
  - `approval_status`: 当前审核状态
  - `approved_stages`: 已通过审核的阶段列表（JSON数组）
  - `approval_history`: 审核历史记录（JSON数组）

### 新增模型功能
- `QuotationApprovalStatus` 类：定义审核状态常量和阶段映射
- `approval_badge_html` 属性：生成审核徽章HTML

### API端点
- `POST /approval/quotation/<id>/approve`: 执行审核操作
- `GET /approval/quotation/<id>/approval-status`: 获取审核状态

### 前端界面
- 报价单列表页面：编号后显示徽章
- 报价单详情页面：提供审核操作界面和历史记录
- 审核模态框：支持通过/拒绝操作并添加意见

## 使用说明

### 1. 执行审核
1. 打开报价单详情页面
2. 在"审批和审核操作"区域查看当前项目阶段
3. 点击"通过审核"或"拒绝审核"按钮
4. 在弹出的模态框中添加审核意见（可选）
5. 确认执行审核操作

### 2. 查看审核状态
- 审核徽章会自动显示在报价单编号旁边
- 不同审核状态采用不同颜色和图标
- 审核历史记录显示在详情页面底部

### 3. 权限配置
在用户角色权限设置中添加 `quotation_approval` 模块的创建权限。

## 审核状态对照表

| 项目阶段 | 审核状态 | 徽章颜色 | 图标 |
|---------|---------|---------|-----|
| discover | discover_approved | 蓝色 | 搜索 |
| embed | embed_approved | 绿色 | 加号圆圈 |
| pre_tender | pre_tender_approved | 橙色 | 文件 |
| tendering | tendering_approved | 粉色 | 法槌 |
| awarded | awarded_approved | 紫色 | 奖杯 |
| quoted | quoted_approved | 青色 | 美元符号 |
| signed | signed_approved | 蓝色 | 勾选圆圈 |
| 拒绝 | rejected | 红色 | 叉号圆圈 |

## 注意事项

1. 只能在项目设置了当前阶段的情况下进行审核
2. 每个阶段只能审核一次，不允许重复审核
3. 审核操作会记录在审核历史中，包括操作人、时间和意见
4. 系统会自动检查用户权限，无权限用户不会看到审核按钮

## 文件变更清单

### 新增文件
- `migrations/add_quotation_approval_fields.py` - 数据库迁移脚本

### 修改文件
- `app/models/quotation.py` - 添加审核相关字段和方法
- `app/models/approval.py` - 添加报价审核动作类型
- `app/permissions.py` - 添加报价审核权限
- `app/views/approval.py` - 添加审核API端点
- `app/helpers/approval_helpers.py` - 修改审批处理逻辑
- `app/templates/quotation/list.html` - 显示审核徽章
- `app/templates/quotation/detail.html` - 添加审核操作界面
- `app/templates/macros/ui_helpers.html` - 添加徽章渲染宏

## 部署步骤

1. 备份数据库
2. 运行迁移脚本：`python migrations/add_quotation_approval_fields.py`
3. 重启应用服务
4. 配置用户权限（如需要）

## 测试建议

1. 创建测试报价单，设置不同项目阶段
2. 使用不同权限的账户测试审核功能
3. 验证徽章显示和审核历史记录
4. 测试重复审核的限制功能 