# PMA 项目通用按钮设计系统完整指南

## 🎯 按钮系统概览

PMA项目采用统一的按钮设计系统，基于Bootstrap框架扩展，提供完整的颜色主题、尺寸规格、图标规范和交互动画。

---

## 📦 核心组件定义

### **主要按钮宏：render_button**

**文件位置**: `app/templates/macros/ui_helpers.html:227`

```jinja2
{% macro render_button(
    text,                    # 按钮文本（必需）
    href=None,               # 链接地址（type="a"时使用）
    color="primary",         # 颜色主题
    size="md",               # 尺寸大小
    icon=None,               # FontAwesome图标类名
    rounded="pill",          # 圆角样式
    extra_class="",          # 附加CSS类
    type="a",                # 按钮类型（a/button/submit）
    attrs=None,              # 附加HTML属性
    onclick=None             # JavaScript点击事件
) %}
```

### **辅助按钮组件**

1. **确认取消按钮组**: `render_confirm_cancel()`
2. **浮动操作按钮**: `render_floating_action_button_group()`

---

## 🎨 颜色主题系统

### **颜色定义表**

| 颜色名称 | 十六进制值 | 用途说明 | 使用场景 |
|---------|-----------|---------|---------|
| `primary` | `#0C7CD0` | 主要操作 | 保存、提交、确认、主要功能入口 |
| `auxiliary` | `#F2F2F2` | 辅助操作 | 添加产品、次要功能、工具按钮 |
| `secondary` | Bootstrap灰 | 次要操作 | 取消、返回、导航、中性操作 |
| `success` | `#198754` | 成功操作 | 导出、执行成功、完成状态 |
| `danger` | `#dc3545` | 危险操作 | 删除、拒绝、危险警告 |
| `warning` | Bootstrap黄 | 警告操作 | 编辑、修改、需注意操作 |
| `info` | Bootstrap蓝 | 信息操作 | 查看、详情、信息展示 |

### **特殊颜色处理**

#### **auxiliary按钮悬浮效果**
```css
.btn-auxiliary {
    background-color: #F2F2F2 !important;
    color: black !important;
    border: 1px solid #ccc !important;
    transition: background-color 0.3s, color 0.3s, border-color 0.3s;
}

.btn-auxiliary:hover {
    background-color: black !important;
    color: white !important;
    border-color: black !important;
}
```

**设计理念**: 灰白→黑色的反转效果，提供独特的视觉反馈

---

## 📏 尺寸规格系统

### **尺寸定义表**

| 尺寸名称 | CSS类组合 | 字体大小 | 内边距 | 使用场景 |
|---------|-----------|---------|--------|---------|
| `xs` | `text-xs py-1 px-2` | 0.75rem | 4px 8px | 表格内操作、紧凑布局 |
| `sm` | `text-xs py-1 px-2` | 0.75rem | 4px 8px | 卡片操作、列表项按钮 |
| `md` | `text-xs py-1 px-3` | 0.75rem | 4px 12px | **默认尺寸**，最常用 |
| `lg` | `text-sm py-2 px-4` | 0.875rem | 8px 16px | 主要CTA按钮、表单提交 |

### **响应式适配**
- **桌面端**: 保持原始尺寸
- **移动端**: 自动调整，推荐使用`sm`尺寸
- **有图标时**: 移动端自动隐藏文字，仅显示图标

---

## 🎯 图标设计规范

### **图标与功能对应表**

#### **基础操作类**
| 功能类型 | 推荐图标 | 备选图标 | 颜色建议 |
|---------|---------|---------|---------|
| 保存/提交 | `fas fa-save` | `fas fa-check` | primary |
| 取消/返回 | `fas fa-arrow-left` | `fas fa-times` | secondary |
| 编辑/修改 | `fas fa-edit` | `fas fa-pencil-alt` | warning |
| 删除 | `fas fa-trash` | `fas fa-trash-alt` | danger |
| 添加/新增 | `fas fa-plus` | `fas fa-plus-circle` | auxiliary |

#### **数据操作类**
| 功能类型 | 推荐图标 | 备选图标 | 颜色建议 |
|---------|---------|---------|---------|
| 导出Excel | `fas fa-file-excel` | `fas fa-download` | success |
| 导出PDF | `fas fa-file-pdf` | `fas fa-download` | success |
| 搜索 | `fas fa-search` | `fas fa-filter` | info |
| 刷新 | `fas fa-redo` | `fas fa-sync` | info |
| 查看详情 | `fas fa-eye` | `fas fa-info-circle` | info |

#### **业务功能类**
| 功能类型 | 推荐图标 | 备选图标 | 颜色建议 |
|---------|---------|---------|---------|
| 授权/权限 | `fas fa-key` | `fas fa-user-shield` | warning |
| 审批通过 | `fas fa-check-circle` | `fas fa-thumbs-up` | success |
| 审批拒绝 | `fas fa-times-circle` | `fas fa-thumbs-down` | danger |
| 邮件发送 | `fas fa-envelope` | `fas fa-paper-plane` | info |
| 列表管理 | `fas fa-list` | `fas fa-table` | secondary |

### **图标使用原则**

1. **必需图标**: 删除、编辑、返回等高频危险操作
2. **推荐图标**: 保存、添加、导出等常用功能  
3. **可选图标**: 查看、列表等低风险操作
4. **禁止图标**: 取消、确认等可能引起歧义的操作

---

## ⚡ 动画交互系统

### **标准悬浮动画**

```css
/* 除auxiliary外所有按钮的悬浮效果 */
.btn:not(.btn-auxiliary):not(.user-avatar-capsule):not(.navbar-toggler):hover {
    transform: translateY(-2px);      /* 向上浮动2px */
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);  /* 增强阴影 */
    transition: all 0.2s ease;       /* 平滑过渡 */
}

/* 点击时的回弹效果 */
.btn:not(.btn-auxiliary):not(.user-avatar-capsule):not(.navbar-toggler):active {
    transform: translateY(0);        /* 恢复原位 */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);  /* 减弱阴影 */
    transition: all 0.1s ease;       /* 快速回弹 */
}
```

### **动画设计理念**
- **微交互**: 2px向上浮动，提供轻微的层次感
- **视觉反馈**: 阴影变化增强深度感知
- **性能优化**: 仅使用transform和box-shadow，避免重排重绘

---

## 📱 响应式设计规范

### **移动端适配策略**

#### **文字隐藏机制**
```jinja2
{# 有图标时移动端隐藏文字 #}
{%- if icon %}
    <i class="{{ icon }}"></i>
    <span class="d-none d-md-inline">{{ display_text }}</span>
{%- else %}
    {{ display_text }}
{%- endif %}
```

#### **浮动操作按钮**
```jinja2
{{ render_floating_action_button_group([
    {'text': '新增产品', 'href': '/new', 'icon': 'fas fa-plus'},
    {'text': '批量导入', 'href': '/import', 'icon': 'fas fa-upload'}
]) }}
```

- **显示规则**: 仅在移动端显示 (`d-md-none`)
- **位置**: 固定在右下角
- **交互**: 点击主按钮展开子菜单

### **断点适配表**

| 屏幕尺寸 | 按钮行为 | 图标显示 | 文字显示 |
|---------|---------|---------|---------|
| ≥768px (md+) | 标准样式 | 完整显示 | 完整显示 |
| <768px (sm-) | 紧凑样式 | 仅图标 | 隐藏文字 |

---

## 🔧 智能化功能

### **文本自动间距调整**

针对中文两字按钮的视觉优化：

```jinja2
{%- set display_text = text %}
{%- if text|length == 2 and not icon %}
  {%- if text == "导出" %}
    {%- set display_text = "导 出" %}
  {%- elif text == "编辑" %}
    {%- set display_text = "编 辑" %}
  {%- elif text == "删除" %}
    {%- set display_text = "删 除" %}
  {%- elif text == "保存" %}
    {%- set display_text = "保 存" %}
  {%- elif text == "取消" %}
    {%- set display_text = "取 消" %}
  {%- elif text == "搜索" %}
    {%- set display_text = "搜 索" %}
  {%- elif text == "重置" %}
    {%- set display_text = "重 置" %}
  {%- elif text == "新增" %}
    {%- set display_text = "新 增" %}
  {%- elif text == "修改" %}
    {%- set display_text = "修 改" %}
  {%- elif text == "确认" %}
    {%- set display_text = "确 认" %}
  {%- elif text == "授权" %}
    {%- set display_text = "授 权" %}
  {%- endif %}
{%- endif %}
```

**设计目的**: 改善中文按钮的视觉平衡和可读性

---

## 💼 实际使用示例

### **基础用法示例**

```html
<!-- 1. 主要操作按钮 -->
{{ render_button('保存设置', type='submit', color='primary') }}

<!-- 2. 带图标的链接按钮 -->
{{ render_button('返回列表', href=url_for('product.list'), 
                 color='secondary', icon='fas fa-arrow-left') }}

<!-- 3. 危险操作按钮 -->
{{ render_button('删除产品', type='button', color='danger', 
                 icon='fas fa-trash-alt', onclick='confirmDelete()') }}

<!-- 4. 辅助功能按钮 -->
{{ render_button('添加产品', href='#', color='auxiliary', 
                 attrs='data-bs-toggle="modal" data-bs-target="#addModal"') }}
```

### **高级用法示例**

```html
<!-- 小尺寸表格操作按钮 -->
<td class="text-end">
    {{ render_button('编辑', href=url_for('edit', id=item.id), 
                     color='warning', size='sm', icon='fas fa-edit', 
                     extra_class='me-1') }}
    {{ render_button('删除', type='button', color='danger', 
                     size='sm', icon='fas fa-trash-alt', 
                     onclick='deleteItem(' ~ item.id ~ ')') }}
</td>

<!-- 导出功能按钮组 -->
<div class="btn-group" role="group">
    {{ render_button('Excel', onclick='exportExcel()', 
                     color='success', icon='fas fa-file-excel', size='sm') }}
    {{ render_button('PDF', onclick='exportPDF()', 
                     color='success', icon='fas fa-file-pdf', size='sm') }}
</div>

<!-- 确认取消按钮组 -->
<div class="modal-footer">
    {{ render_confirm_cancel(
        confirm_text='确认删除', 
        cancel_text='取消', 
        confirm_color='danger',
        cancel_color='secondary',
        confirm_type='submit',
        size='md'
    ) }}
</div>
```

### **移动端浮动按钮**

```html
<!-- 页面主要操作的移动端浮动按钮 -->
{{ render_floating_action_button_group([
    {
        'text': '新增产品', 
        'href': url_for('product.new'), 
        'icon': 'fas fa-plus',
        'color': 'primary'
    },
    {
        'text': '批量导入', 
        'href': url_for('product.import'), 
        'icon': 'fas fa-upload',
        'color': 'auxiliary'
    },
    {
        'text': '导出数据', 
        'onclick': 'exportData()', 
        'icon': 'fas fa-download',
        'color': 'success'
    }
]) }}
```

---

## 🎯 设计最佳实践

### **按钮层级规范**

1. **主要操作 (Primary)**
   - 每个页面/表单最多1个
   - 用于最重要的操作（保存、提交）
   - 位置：右侧或底部最显眼位置

2. **次要操作 (Secondary)**
   - 数量不限，但要控制
   - 用于导航、取消等中性操作
   - 位置：主要操作左侧或上方

3. **辅助操作 (Auxiliary)**
   - 用于工具功能、添加操作
   - 独特的悬浮变黑效果
   - 位置：页面右上角或功能区域

4. **危险操作 (Danger)**
   - 必须添加确认机制
   - 建议放在独立位置
   - 图标必需，增强警示效果

### **图标使用最佳实践**

1. **必需场景**：删除、编辑、返回、危险操作
2. **推荐场景**：保存、添加、导出、搜索
3. **避免场景**：确认、取消、普通文本链接
4. **移动端优先**：所有功能性按钮建议添加图标

### **性能优化建议**

1. **CSS动画**：仅使用transform和opacity，避免引起重排
2. **图标加载**：使用FontAwesome CDN或本地化部署
3. **事件处理**：onclick优于内联JavaScript
4. **可访问性**：保持语义化HTML结构

### **国际化支持**

1. **文本处理**：自动文字间距仅对中文生效
2. **RTL支持**：图标位置自动调整
3. **文化适配**：颜色含义考虑不同文化背景

---

## 📋 快速参考手册

### **常用按钮组合**

```html
<!-- 表单提交区域 -->
<div class="d-flex justify-content-end gap-2">
    {{ render_button('取消', href=url_for('back'), color='secondary') }}
    {{ render_button('保存', type='submit', color='primary') }}
</div>

<!-- 列表操作区域 -->
<div class="d-flex gap-2 mb-3">
    {{ render_button('新增', href=url_for('new'), color='auxiliary', icon='fas fa-plus') }}
    {{ render_button('导出', onclick='exportData()', color='success', icon='fas fa-file-excel') }}
</div>

<!-- 表格行操作 -->
<div class="btn-group btn-group-sm">
    {{ render_button('查看', href=url_for('view', id=item.id), 
                     color='info', size='sm', icon='fas fa-eye') }}
    {{ render_button('编辑', href=url_for('edit', id=item.id), 
                     color='warning', size='sm', icon='fas fa-edit') }}
    {{ render_button('删除', onclick='deleteItem(' ~ item.id ~ ')', 
                     color='danger', size='sm', icon='fas fa-trash') }}
</div>
```

### **错误用法对比**

| ❌ 错误用法 | ✅ 正确用法 | 说明 |
|------------|------------|------|
| `color='red'` | `color='danger'` | 使用标准颜色名称 |
| `size='small'` | `size='sm'` | 使用标准尺寸名称 |
| `icon='fa-plus'` | `icon='fas fa-plus'` | 包含完整FontAwesome类名 |
| 删除按钮无图标 | 删除按钮必需图标 | 危险操作必须视觉标识 |
| 每页多个primary | 每页最多1个primary | 保持视觉层级 |

---

## 🔄 版本更新日志

- **v1.0** (2025-07-25): 初始版本，完整的按钮设计系统
- **功能特性**: 颜色主题、尺寸系统、图标规范、动画效果
- **响应式**: 移动端适配、浮动按钮、智能文字隐藏
- **国际化**: 中文字符间距优化、多语言支持

---

此设计系统确保了PMA项目中所有按钮的一致性和可用性，提供了完整的设计规范和实现指南。开发时请严格遵循此规范，确保用户体验的统一性。