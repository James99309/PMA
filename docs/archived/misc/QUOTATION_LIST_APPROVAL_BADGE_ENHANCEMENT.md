# 报价单列表审核徽章功能增强

## 功能概述

在报价单列表页面的报价编号字段后面添加审核确认徽章，只有通过审核的报价单才会显示审核徽章，提供直观的审核状态指示。

## 主要变更

### 1. 表格列宽调整

**报价编号列宽度扩展**：
```html
<!-- 修改前 -->
<th class="px-3 py-3" style="min-width: 130px;">

<!-- 修改后 -->
<th class="px-3 py-3" style="min-width: 180px;">
```

**原因**：为了容纳报价编号和审核徽章，避免内容换行，将最小宽度从130px增加到180px。

### 2. 审核徽章显示逻辑

**桌面端表格视图**：
```html
<td class="px-3">
    <div class="d-flex align-items-center">
        <a href="{{ url_for('quotation.view_quotation', id=quotation.id) }}">
            {{ render_quotation_number(quotation.quotation_number) }}
        </a>
        {% set approval_instance = get_object_approval_instance('quotation', quotation.id) if get_object_approval_instance is defined %}
        {% if approval_instance and approval_instance.status == ApprovalStatus.APPROVED %}
        <span class="approval-badge-small ms-2" title="已通过审核">
            <i class="fas fa-check-circle"></i>
        </span>
        {% endif %}
    </div>
</td>
```

**移动端卡片视图**：
```html
<div class="d-flex align-items-center">
    <span class="badge bg-info">{{ render_quotation_number(quotation.quotation_number) }}</span>
    {% set approval_instance = get_object_approval_instance('quotation', quotation.id) if get_object_approval_instance is defined %}
    {% if approval_instance and approval_instance.status == ApprovalStatus.APPROVED %}
    <span class="approval-badge-small ms-2" title="已通过审核">
        <i class="fas fa-check-circle"></i>
    </span>
    {% endif %}
</div>
```

### 3. 审核状态判断逻辑

**审核实例获取**：
- 使用`get_object_approval_instance('quotation', quotation.id)`获取报价单的审批实例
- 检查审批实例是否存在且状态为`ApprovalStatus.APPROVED`
- 只有审核通过的报价单才显示审核徽章

**显示条件**：
```jinja2
{% if approval_instance and approval_instance.status == ApprovalStatus.APPROVED %}
```

### 4. 审核徽章样式设计

**基础样式**：
```css
.approval-badge-small {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background-color: #28a745;
    color: #fff;
    font-size: 10px;
    line-height: 1;
    vertical-align: middle;
}

.approval-badge-small i {
    font-size: 10px;
}
```

**移动端适配**：
```css
@media (max-width: 991.98px) {
    .approval-badge-small {
        width: 16px;
        height: 16px;
        font-size: 9px;
    }
    
    .approval-badge-small i {
        font-size: 9px;
    }
}
```

## 设计特点

### 1. 尺寸协调

- **桌面端**：18px × 18px，与报价编号胶囊徽章大小协调
- **移动端**：16px × 16px，适配小屏幕显示
- **图标大小**：10px（桌面）/ 9px（移动），确保清晰可见

### 2. 视觉设计

- **颜色**：绿色背景（#28a745），表示通过状态
- **图标**：Font Awesome的`fa-check-circle`，直观表示审核通过
- **形状**：圆形设计，与系统其他徽章保持一致
- **位置**：报价编号右侧，使用`ms-2`类添加适当间距

### 3. 交互体验

- **提示信息**：鼠标悬停显示"已通过审核"
- **响应式**：在不同屏幕尺寸下自动调整大小
- **对齐方式**：使用flexbox确保垂直居中对齐

## 功能特性

### 1. 条件显示

- **显示条件**：只有审核状态为`APPROVED`的报价单才显示徽章
- **隐藏条件**：未审核、审核中、审核拒绝的报价单不显示徽章
- **动态更新**：审核状态变化后，列表页面刷新即可看到徽章变化

### 2. 多端适配

- **桌面端**：表格视图中的徽章显示
- **移动端**：卡片视图中的徽章显示
- **响应式**：不同屏幕尺寸下的样式适配

### 3. 性能优化

- **模板级别**：在模板中直接判断，避免额外的数据库查询
- **缓存友好**：使用现有的审批实例数据，不增加查询负担
- **轻量级**：CSS和HTML代码简洁，不影响页面加载速度

## 技术实现

### 1. 模板函数依赖

- `get_object_approval_instance()`: 获取审批实例
- `ApprovalStatus`: 审批状态枚举
- `render_quotation_number()`: 渲染报价编号

### 2. 样式依赖

- Font Awesome图标库：`fa-check-circle`
- Bootstrap间距类：`ms-2`
- 自定义CSS类：`.approval-badge-small`

### 3. 兼容性考虑

- 向后兼容：如果审批功能未启用，徽章不会显示
- 错误处理：如果`get_object_approval_instance`未定义，使用条件判断避免错误
- 数据安全：检查审批实例存在性，避免空值错误

## 用户体验改进

### 1. 信息可视化

- **快速识别**：用户可以一眼看出哪些报价单已通过审核
- **状态明确**：绿色勾号清晰表示审核通过状态
- **信息密度**：在不增加列宽的情况下提供更多信息

### 2. 操作效率

- **筛选便利**：用户可以快速找到已审核的报价单
- **状态跟踪**：便于跟踪报价单的审核进度
- **决策支持**：帮助用户做出基于审核状态的业务决策

### 3. 界面一致性

- **设计统一**：与系统其他徽章样式保持一致
- **交互一致**：悬停提示与其他元素行为一致
- **布局协调**：与现有表格布局完美融合

## 测试建议

### 1. 功能测试

- [ ] 审核通过的报价单显示绿色勾号徽章
- [ ] 未审核的报价单不显示徽章
- [ ] 审核中的报价单不显示徽章
- [ ] 审核拒绝的报价单不显示徽章
- [ ] 徽章悬停显示正确的提示信息

### 2. 界面测试

- [ ] 桌面端表格视图徽章显示正常
- [ ] 移动端卡片视图徽章显示正常
- [ ] 不同屏幕尺寸下徽章大小适配正确
- [ ] 徽章与报价编号对齐良好
- [ ] 列宽调整后内容不换行

### 3. 兼容性测试

- [ ] Chrome浏览器显示正常
- [ ] Firefox浏览器显示正常
- [ ] Safari浏览器显示正常
- [ ] 移动端浏览器显示正常

### 4. 性能测试

- [ ] 页面加载速度无明显影响
- [ ] 大量数据时徽章渲染性能良好
- [ ] 内存使用无异常增长

## 后续优化建议

### 1. 功能扩展

- 考虑添加审核中状态的徽章（如黄色时钟图标）
- 支持点击徽章查看审核详情
- 添加审核状态的筛选功能

### 2. 样式优化

- 支持主题色彩自定义
- 添加动画效果（如淡入淡出）
- 优化高分辨率屏幕显示

### 3. 交互改进

- 添加审核状态的快速操作菜单
- 支持批量查看审核状态
- 集成审核流程的快捷入口

---

**实施时间**：2024-12-19  
**实施人员**：系统维护团队  
**影响范围**：报价单列表页面  
**优先级**：中等  
**状态**：已完成开发，待测试 