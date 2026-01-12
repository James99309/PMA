# Tailwind 组件规范

本文档包含所有 Tailwind CSS 组件的使用规范。这些组件适用于 `tw_*.html` 风格的页面。

> **注意**: Bootstrap 风格的组件规范请参阅 [CLAUDE-COMPONENTS.md](./CLAUDE-COMPONENTS.md)

---

## 目录

1. [详情页布局组件](#-tailwind-详情页布局组件)
2. [工作记录组件](#-tailwind-工作记录组件)
3. [行动记录列表组件](#-tailwind-行动记录列表组件)
4. [行动记录回复组件](#-tailwind-行动记录回复组件)
5. [按钮组件](#-tailwind-按钮组件)
6. [确认模态框组件](#-tailwind-确认模态框组件)
7. [表单模态框组件](#-tailwind-表单模态框组件)
8. [行动记录模态框组件](#-tailwind-行动记录模态框组件)
9. [用户徽章组件](#-tailwind-用户徽章组件)
10. [信息卡片组件](#-tailwind-信息卡片组件)
11. [卡片外壳组件](#-tailwind-卡片外壳组件)
12. [表格卡片组件](#-tailwind-表格卡片组件)
13. [项目列表卡片组件](#-tailwind-项目列表卡片组件)
14. [审批流程组件](#-tailwind-审批流程组件)
15. [标签页组件](#-tailwind-标签页组件)
16. [Mention 编辑器组件](#-tailwind-mention-编辑器组件)
17. [详情页卡片高度同步工具](#-详情页卡片高度同步工具)
18. [签字板组件](#️-tailwind-签字板组件)

---

## 🎨 模态框设计规范

### **设计原则**
所有 Tailwind 模态框遵循统一的简洁设计：

```
┌─────────────────────────────────┐
│  标题                          │  ← 无X按钮，无分割线
│                                 │
│  内容区域                       │
│                                 │
│              [取消]  [确认]     │  ← 无分割线
└─────────────────────────────────┘
```

### **关闭方式**
- **底部按钮**：取消/关闭按钮（主要关闭方式）
- **点击遮罩**：点击模态框外部区域关闭
- **ESC 键**：按 ESC 键关闭

### **默认参数**
| 组件 | 参数 | 默认值 |
|-----|------|--------|
| `tw_modal` | `show_close` | `false` |
| `tw_modal` | `header_border` | `false` |
| `tw_modal_header` | `show_close` | `false` |
| `tw_modal_header` | `border` | `false` |
| `tw_modal_footer` | `border` | `false` |

### **使用示例**
```jinja2
{% call tw_modal('myModal', title='标题', close_action='closeModal()') %}
    <div class="p-6">
        <!-- 内容区域 -->
    </div>
    <footer class="flex items-center justify-end px-6 py-4">
        <button type="button" onclick="closeModal()">{{ _('取消') }}</button>
        <button type="button" onclick="handleSubmit()">{{ _('确认') }}</button>
    </footer>
{% endcall %}
```

### **特殊情况**
如需显示 X 按钮或分割线，可通过参数启用：
```jinja2
{{ tw_modal('modal', title='标题', show_close=true, header_border=true) }}
{{ tw_modal_footer(cancel_text='取消', border=true) }}
```

---

## 📐 Tailwind 详情页布局组件

### **组件概述**
统一的详情页布局组件，支持固定顶部标题区域、可滚动内容区域和 sticky 吸顶侧边栏。

**文件位置**: `app/templates/components/tw_detail_layout.html`

**功能特性**:
- 固定顶部：面包屑导航、页面标题、状态徽章、操作按钮
- 可滚动内容区域
- 可选的 sticky 吸顶侧边栏（如行动记录）
- 深色模式支持
- 响应式布局

### **布局结构**
```
┌─────────────────────────────────────────────────────────────────┐
│ 固定顶部区域（不滚动）                                            │
│ [面包屑导航]                                                      │
│ [页面标题]                              [状态徽章] [操作按钮]       │
├─────────────────────────────────────────────────────────────────┤
│ 可滚动内容区域                                                    │
│ ┌─────────────────────────────┬─────────────────────────────┐   │
│ │ 左侧主内容（随页面滚动）      │ 右侧边栏（sticky吸顶）       │   │
│ │                             │ 滚动到顶部后固定不动          │   │
│ │ [卡片1]                     │                             │   │
│ │ [卡片2]                     │ [行动记录等]                 │   │
│ │ [卡片3]                     │                             │   │
│ └─────────────────────────────┴─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### **使用方式**

#### **1. 有侧边栏的详情页（如项目详情）**
```jinja2
{% from 'components/tw_detail_layout.html' import tw_detail_layout %}

{% call(slot) tw_detail_layout(has_sidebar=true) %}
    {% if slot == 'breadcrumb' %}
        <a class="hover:underline" href="{{ url_for('project.list_projects') }}">{{ _('项目管理') }}</a>
        <span>/</span>
        <span class="text-slate-800 dark:text-slate-200">{{ project.project_name }}</span>
    {% elif slot == 'title' %}
        <h2 class="text-3xl font-bold text-slate-900 dark:text-white">{{ project.project_name }}</h2>
    {% elif slot == 'badges' %}
        {{ render_tw_active_badge(project.is_active) }}
    {% elif slot == 'actions' %}
        {{ tw_btn_outline(_('编辑'), onclick='openEditModal()', icon='edit', size='sm') }}
        {{ tw_btn_outline(_('删除'), onclick='confirmDelete()', icon='delete', size='sm', color='danger') }}
    {% elif slot == 'main' %}
        <!-- 左侧主内容卡片 -->
        <div class="bg-white dark:bg-slate-900 rounded-lg shadow-sm border p-6">
            项目信息卡片
        </div>
        <div class="bg-white dark:bg-slate-900 rounded-lg shadow-sm border p-6">
            联系人卡片
        </div>
    {% elif slot == 'sidebar' %}
        <!-- 右侧边栏：行动记录等 -->
        <div class="bg-white dark:bg-slate-900 rounded-lg shadow-sm border p-6 flex flex-col" style="max-height: calc(100vh - 120px)">
            <h2 class="text-lg font-semibold mb-6">{{ _('行动记录') }}</h2>
            <div class="flex-1 overflow-y-auto">
                <!-- 行动记录列表 -->
            </div>
        </div>
    {% endif %}
{% endcall %}
```

#### **2. 无侧边栏的详情页（如报销单详情）**
```jinja2
{% from 'components/tw_detail_layout.html' import tw_detail_layout %}

{% call(slot) tw_detail_layout(has_sidebar=false) %}
    {% if slot == 'breadcrumb' %}
        <a class="hover:underline" href="{{ url_for('expense.list_expenses') }}">{{ _('报销管理') }}</a>
        <span>/</span>
        <span class="text-slate-800 dark:text-slate-200">{{ expense.expense_number }}</span>
    {% elif slot == 'title' %}
        <h2 class="text-3xl font-bold text-slate-900 dark:text-white">{{ expense.expense_number }}</h2>
    {% elif slot == 'badges' %}
        {{ render_tw_expense_status_badge(expense.status) }}
    {% elif slot == 'actions' %}
        {{ tw_btn_outline(_('编辑'), onclick='openEditModal()', icon='edit', size='sm') }}
    {% elif slot == 'content' %}
        <!-- 无侧边栏时使用 content 槽 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="bg-white dark:bg-slate-900 rounded-lg shadow-sm border p-6">
                基本信息
            </div>
            <div class="bg-white dark:bg-slate-900 rounded-lg shadow-sm border p-6">
                报销明细
            </div>
        </div>
    {% endif %}
{% endcall %}
```

### **参数说明**

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `has_sidebar` | boolean | `false` | 是否有右侧边栏 |
| `sidebar_cols` | number | `1` | 侧边栏占用列数（总共3列） |
| `main_cols` | number | `2` | 主内容占用列数 |
| `sidebar_sticky_top` | string | `'4'` | 侧边栏吸顶距离顶部的位置（Tailwind单位） |
| `sidebar_max_height` | string | `'calc(100vh - 120px)'` | 侧边栏最大高度 |

### **插槽说明**

| 插槽名 | 说明 | 使用场景 |
|-------|------|---------|
| `breadcrumb` | 面包屑导航内容 | 所有详情页 |
| `title` | 页面标题（通常是 h2 标签） | 所有详情页 |
| `badges` | 状态徽章区域 | 显示状态、锁定等徽章 |
| `actions` | 操作按钮区域 | 编辑、删除、导出等按钮 |
| `content` | 主内容区（无侧边栏时） | `has_sidebar=false` 时使用 |
| `main` | 左侧主内容（有侧边栏时） | `has_sidebar=true` 时使用 |
| `sidebar` | 右侧边栏内容 | `has_sidebar=true` 时使用 |

### **已使用页面**
- `app/templates/project/tw_project_detail.html` - 项目详情页

### **注意事项**
- 组件使用 Tailwind CSS，仅适用于 Tailwind 页面
- 侧边栏使用 CSS `sticky` 定位，滚动到顶部后固定
- 侧边栏内部内容如需滚动，需要自行设置 `overflow-y-auto` 和固定高度
- 确保页面外层容器有 `h-screen overflow-hidden` 以支持固定顶部效果

---

## 📊 Tailwind 工作记录组件

### **组件概述**
可复用的 Tailwind CSS 工作记录表格组件，用于显示工作行动记录。

**文件位置**: `app/templates/components/tw_work_records.html`

**功能特性**:
- 固定高度滚动
- 无限滚动加载更多
- 账户筛选（可选）
- 深色模式支持
- 国际化支持

### **使用方式**

#### 1. 导入组件
```jinja2
{% from 'components/tw_work_records.html' import render_tw_work_records, render_tw_work_records_script %}
```

#### 2. 渲染 HTML 结构
```jinja2
{{ render_tw_work_records(
    container_id='workRecords',
    show_account_filter=true,
    max_height='400px',
    title=_('工作记录')
) }}
```

#### 3. 引入 JavaScript（页面底部）
```jinja2
{{ render_tw_work_records_script(
    container_id='workRecords',
    api_url='/api/recent_work_records',
    user_role=current_user.role,
    show_account_filter=true
) }}
```

### **参数说明**

#### render_tw_work_records()

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `container_id` | string | 'records' | 容器ID前缀 |
| `show_account_filter` | bool | false | 是否显示账户筛选 |
| `max_height` | string | '400px' | 最大高度 |
| `title` | string | None | 组件标题 |

#### render_tw_work_records_script()

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `container_id` | string | 'records' | 容器ID前缀（需与HTML一致） |
| `api_url` | string | '/api/recent_work_records' | API地址 |
| `user_role` | string | '' | 用户角色 |
| `show_account_filter` | bool | false | 是否启用账户筛选 |

### **API 数据格式要求**

```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "date": "2025-12-06",
            "time": "14:30",
            "owner_initials": "张三",
            "customer_id": 1,
            "customer_name": "客户名称",
            "contact_name": "联系人",
            "project_id": 1,
            "project_name": "项目名称",
            "communication": "行动记录内容",
            "has_reply": true,
            "reply_count": 2
        }
    ],
    "total": 100,
    "loaded_count": 20,
    "has_more": true
}
```

### **JavaScript API**

组件暴露公共方法供外部调用：

```javascript
// 重新加载数据
window.workRecordsComponent.reload();

// 加载更多
window.workRecordsComponent.loadMore();

// 查看回复
window.workRecordsComponent.viewReplies(actionId);

// 添加回复
window.workRecordsComponent.addReply(actionId);
```

### **使用示例**

**首页使用**（完整示例）:
```jinja2
{% from 'components/tw_work_records.html' import render_tw_work_records, render_tw_work_records_script %}

<!-- 在页面内容区域 -->
{{ render_tw_work_records(
    container_id='workRecords',
    show_account_filter=true,
    max_height='400px',
    title=_('工作记录')
) }}

<!-- 在页面底部 </body> 之前 -->
{{ render_tw_work_records_script(
    container_id='workRecords',
    api_url='/api/recent_work_records',
    user_role=current_user.role,
    show_account_filter=true
) }}
```

### **注意事项**
- 组件使用 Tailwind CSS，仅适用于 Tailwind 页面
- `container_id` 在 HTML 和 Script 宏中必须一致
- 管理员/总监角色才会显示账户筛选下拉框
- 表头在滚动时保持固定（sticky）

---

## 📝 Tailwind 行动记录列表组件

### **组件概述**
通用的 Tailwind CSS 行动记录列表展示组件，支持多种场景和完整功能。

**文件位置**: `app/templates/components/tw_action_list.html`

**功能特性**:
- 两种布局模式：卡片布局（card）和表格布局（table）
- 回复功能：展开/折叠面板、聊天气泡样式回复
- 快速添加：内联表单快速添加行动记录
- 分页支持：上一页/下一页导航
- 删除功能：权限控制的删除按钮
- 相对时间：自动转换为"刚刚"、"几分钟前"等
- 深色模式和国际化支持

### **使用方式**

#### 1. 导入组件
```jinja2
{% from 'components/tw_action_list.html' import tw_action_list_card, render_tw_action_list_script with context %}
```

#### 2. 基础使用（卡片布局）
适用于项目详情页、联系人详情页等侧边栏场景。

```jinja2
{{ tw_action_list_card(
    actions=project_actions,
    add_button={'onclick': 'openAddActionModal()'},
    max_items=10,
    show_contact=true,
    show_company=true,
    view_all_url='#'
) }}
```

#### 3. 带删除功能
适用于联系人详情页。

```jinja2
{{ tw_action_list_card(
    actions=actions,
    add_button={'href': url_for('customer.add_action')},
    max_items=20,
    show_contact=false,
    show_company=false,
    show_project=true,
    show_delete=true,
    delete_callback='deleteAction',
    time_format='date',
    min_height='400px'
) }}
```

#### 4. 完整功能（表格布局 + 回复 + 快速添加 + 分页）
适用于客户详情页。

```jinja2
{{ tw_action_list_card(
    actions=viewable_actions,
    add_button={'onclick': 'openAddActionModal()'},
    layout='table',
    enable_replies=true,
    container_id='customerReplies',
    api_prefix='/customer',
    enable_quick_add=true,
    quick_add_contacts=contacts,
    quick_add_company_id=company.id,
    enable_pagination=true,
    pagination=pagination,
    page_url=url_for('customer.view_company', company_id=company.id),
    has_create_permission=has_permission('customer', 'create')
) }}

<!-- 页面底部引入脚本 -->
{{ render_tw_action_list_script(
    container_id='customerReplies',
    api_prefix='/customer',
    enable_replies=true,
    enable_quick_add=true,
    quick_add_company_id=company.id
) }}
```

### **参数说明**

#### tw_action_list_card()

**基础参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `actions` | list | 必填 | 行动记录列表 |
| `title` | string | '行动记录' | 卡片标题 |
| `add_button` | dict | none | 添加按钮配置 `{onclick: '...'} 或 {href: '...'}` |
| `max_items` | int | 10 | 最大显示条数（仅卡片布局生效） |
| `view_all_url` | string | none | 查看全部链接 |
| `min_height` | string | '600px' | 最小高度 |
| `time_format` | string | 'relative' | 时间格式：'relative'（相对时间）或 'date'（日期） |
| `container_class` | string | '' | 额外的CSS类 |

**显示控制参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `layout` | string | 'card' | 布局模式：'card'（卡片）或 'table'（表格） |
| `show_contact` | bool | true | 显示联系人名称 |
| `show_company` | bool | true | 显示企业名称 |
| `show_project` | bool | false | 显示关联项目链接 |
| `show_delete` | bool | false | 显示删除按钮 |
| `delete_callback` | string | 'deleteAction' | 删除回调函数名 |

**回复功能参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_replies` | bool | false | 启用回复功能 |
| `container_id` | string | 'actionReplies' | 回复容器ID前缀 |
| `api_prefix` | string | '/customer' | API路径前缀 |

**快速添加参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_quick_add` | bool | false | 启用快速添加 |
| `quick_add_contacts` | list | [] | 联系人列表 |
| `quick_add_company_id` | int | none | 公司ID |
| `has_create_permission` | bool | false | 创建权限 |

**分页参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_pagination` | bool | false | 启用分页 |
| `pagination` | object | none | 分页对象（需含 pages, has_prev, has_next 等属性） |
| `page_url` | string | '' | 分页链接基础URL |

#### render_tw_action_list_script()

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `container_id` | string | 'actionReplies' | 容器ID前缀（需与组件一致） |
| `api_prefix` | string | '/customer' | API路径前缀 |
| `enable_replies` | bool | false | 启用回复功能 |
| `enable_quick_add` | bool | false | 启用快速添加 |
| `quick_add_company_id` | int | none | 公司ID |

### **API 接口要求**

启用回复功能时需要后端提供以下接口：

```
GET  {api_prefix}/action/{actionId}/replies     # 获取回复列表
POST {api_prefix}/action/{actionId}/reply       # 提交回复
POST {api_prefix}/action/reply/{replyId}/delete # 删除回复
```

启用快速添加时需要：

```
POST {api_prefix}/api/quick-add-action          # 快速添加行动记录
Body: { company_id, contact_id, communication }
```

### **JavaScript API**

启用回复功能后，组件暴露以下方法：

```javascript
// 折叠面板
window.{containerId}Actions.collapsePanel(actionId);

// 加载回复
window.{containerId}Actions.loadReplies(actionId);

// 提交回复
window.{containerId}Actions.submitReply(actionId);

// 删除回复
window.{containerId}Actions.deleteReply(actionId, replyId);
```

### **页面使用情况**

| 页面 | 文件 | 布局 | 功能 |
|-----|------|-----|------|
| 客户详情页 | `tw_view.html` | table | 回复 + 快速添加 + 分页 |
| 联系人详情页 | `tw_contact_view.html` | card | 基础列表 + 删除 |
| 项目详情页 | `tw_project_detail.html` | card | 基础列表 |

### **全局变量要求**

使用回复功能时，需在页面中设置：

```html
<script>
    window.currentUserId = {{ current_user.id }};
    window.i18nTexts = {
        justNow: '{{ _("刚刚") }}',
        minutesAgo: '{{ _("分钟前") }}',
        hoursAgo: '{{ _("小时前") }}',
        daysAgo: '{{ _("天前") }}',
        monthsAgo: '{{ _("个月前") }}',
        yearsAgo: '{{ _("年前") }}',
        delete: '{{ _("删除") }}',
        confirmDeleteReply: '{{ _("确定要删除这条回复吗？") }}',
        selectContact: '{{ _("请选择联系人") }}',
        enterContent: '{{ _("请输入行动记录内容") }}'
    };
</script>
```

### **样式规范**

#### 添加按钮样式
**统一使用文字链接样式**（两种布局模式保持一致）：

```html
<!-- onclick 方式 -->
<button type="button" onclick="..." class="text-primary text-sm font-medium hover:underline">{{ _('添加记录') }}</button>

<!-- href 方式 -->
<a href="..." class="text-primary text-sm font-medium hover:underline">{{ _('添加记录') }}</a>
```

**样式说明**：
- `text-primary` - 主题色文字
- `text-sm` - 小号字体
- `font-medium` - 中等字重
- `hover:underline` - 悬停下划线

**禁止**：不使用 `tw_btn_outline` 等按钮组件，保持简洁的文字链接风格。

### **注意事项**
- 组件使用 Tailwind CSS，仅适用于 Tailwind 页面
- 卡片布局（card）适合侧边栏，表格布局（table）适合主内容区
- 启用回复功能时必须同时调用 `render_tw_action_list_script` 宏
- `container_id` 在组件和脚本宏中必须保持一致
- 回复功能的删除确认需要页面存在 `replyDeleteConfirmModal` 模态框

---

## 💬 Tailwind 行动记录回复组件

### **组件概述**
可复用的 Tailwind CSS 行动记录回复组件，用于项目和客户详情页的回复功能。

> **注意**: 此组件已被集成到 `tw_action_list.html` 组件中。如果使用 `tw_action_list_card` 并启用 `enable_replies=true`，则无需单独使用此组件。

**文件位置**: `app/templates/components/tw_action_replies.html`

**功能特性**:
- 聊天气泡样式（当前用户右对齐蓝色，其他用户左对齐灰色）
- 气泡宽度自适应内容
- 相对时间显示（刚刚、几分钟前、几小时前等）
- 点击外部区域自动折叠
- 嵌套回复（子回复）
- 深色模式支持
- 国际化支持

### **使用方式**

#### 1. 导入组件
```jinja2
{% from 'components/tw_action_replies.html' import render_tw_action_replies_script, render_reply_panel, render_reply_badge %}
```

#### 2. 设置全局变量（页面头部）
```html
<script>
    window.currentUserId = {{ current_user.id }};
    window.currentUserInitials = '{{ current_user.username[:2] if current_user.username else "Me" }}';
    window.i18nTexts = {
        justNow: '{{ _("刚刚") }}',
        minutesAgo: '{{ _("分钟前") }}',
        hoursAgo: '{{ _("小时前") }}',
        daysAgo: '{{ _("天前") }}',
        monthsAgo: '{{ _("个月前") }}',
        yearsAgo: '{{ _("年前") }}',
        delete: '{{ _("删除") }}',
        confirmDeleteReply: '{{ _("确定要删除这条回复吗？") }}'
    };
</script>
```

#### 3. 渲染回复徽章（在行动记录中）
```jinja2
{{ render_reply_badge(
    container_id='actionReplies',
    action_id=action.id,
    has_reply=action.has_reply,
    reply_count=action.reply_count
) }}
```

#### 4. 渲染回复面板（在行动记录下方）
```jinja2
{{ render_reply_panel(
    container_id='actionReplies',
    action_id=action.id
) }}
```

#### 5. 引入 JavaScript（页面底部）
```jinja2
{{ render_tw_action_replies_script(
    container_id='actionReplies',
    api_prefix='/project'
) }}
```

### **参数说明**

#### render_reply_badge()

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `container_id` | string | ✅ | 容器ID前缀 |
| `action_id` | int | ✅ | 行动记录ID |
| `has_reply` | bool | ✅ | 是否有回复 |
| `reply_count` | int | ✅ | 回复数量 |

#### render_reply_panel()

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `container_id` | string | ✅ | 容器ID前缀 |
| `action_id` | int | ✅ | 行动记录ID |

#### render_tw_action_replies_script()

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `container_id` | string | 'replies' | 容器ID前缀（需与HTML一致） |
| `api_prefix` | string | '/project' | API路径前缀（'/project' 或 '/customer'） |

### **API 接口要求**

组件需要后端提供以下API接口：

#### 获取回复列表
```
GET {api_prefix}/action/{actionId}/replies
```

**响应格式**:
```json
[
    {
        "id": 1,
        "content": "回复内容",
        "owner": "张三",
        "owner_id": 1,
        "created_at": "2025-12-06T14:30:00Z",
        "can_delete": true,
        "children": []
    }
]
```

#### 提交回复
```
POST {api_prefix}/action/{actionId}/reply
Content-Type: application/json
X-CSRFToken: {csrf_token}

{
    "content": "回复内容"
}
```

#### 删除回复
```
POST {api_prefix}/action/reply/{replyId}/delete
X-CSRFToken: {csrf_token}
```

### **JavaScript API**

组件暴露公共方法供外部调用：

```javascript
// 切换回复面板显示
window.{containerId}Replies.toggleReply(actionId, badgeElement);

// 加载回复列表
window.{containerId}Replies.loadReplies(actionId);

// 提交回复
window.{containerId}Replies.submitReply(actionId);

// 取消回复（收起面板）
window.{containerId}Replies.cancelReply(actionId);

// 删除回复
window.{containerId}Replies.deleteReply(actionId, replyId);

// 折叠所有面板
window.{containerId}Replies.collapseAll();
```

### **样式说明**

#### 气泡样式
- **当前用户**: 右对齐，蓝色气泡 (`bg-blue-100 dark:bg-blue-900/50`)，右下角无圆角
- **其他用户**: 左对齐，灰色气泡 (`bg-slate-100 dark:bg-slate-700`)，左下角无圆角

#### 回复徽章
- **有回复**: 红色圆形徽章显示数量 (`bg-red-500`)
- **无回复**: 灰色圆形徽章显示 0 (`bg-slate-300`)

#### 时间显示
- 刚刚（60秒内）
- X分钟前（60分钟内）
- X小时前（24小时内）
- X天前（30天内）
- X个月前（12个月内）
- X年前

### **注意事项**
- 组件使用 Tailwind CSS，仅适用于 Tailwind 页面
- `container_id` 在所有宏中必须保持一致
- 必须在页面中设置 `window.currentUserId` 用于判断气泡方向
- API返回的 `created_at` 必须是 ISO 8601 UTC 格式（以 'Z' 结尾）
- 点击回复面板外部区域会自动折叠面板
- 组件支持嵌套回复（通过 `children` 数组）

---

## 🔘 Tailwind 按钮组件

可复用的 Tailwind CSS 按钮组件，支持多种样式和尺寸。

**文件位置**: `app/templates/components/tw_buttons.html`

### **导入方式**
```jinja2
{% from 'components/tw_buttons.html' import tw_btn_primary, tw_btn_secondary, tw_btn_danger, tw_btn_outline, tw_btn_icon with context %}
```

### **可用宏**

#### tw_btn_primary()
主按钮 - 蓝色实心，用于主要操作

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| text | string | 必填 | 按钮文本 |
| onclick | string | '' | 点击事件 |
| type | string | 'button' | 按钮类型 |
| size | string | 'md' | 尺寸：'sm' / 'md' / 'lg' |
| icon | string | '' | Material Symbols 图标名 |
| href | string | '' | 链接地址（设置后渲染为 a 标签） |
| disabled | bool | false | 是否禁用 |
| id | string | '' | 元素 ID |

```jinja2
{{ tw_btn_primary(_('提交'), onclick='submit()') }}
{{ tw_btn_primary(_('新建项目'), href=url_for('project.add'), icon='add') }}
{{ tw_btn_primary(_('保存'), type='submit', size='lg') }}
```

#### tw_btn_secondary()
次按钮 - 透明/灰色，用于取消等次要操作

```jinja2
{{ tw_btn_secondary(_('取消'), onclick='cancel()') }}
{{ tw_btn_secondary(_('返回'), href=url_for('customer.list'), icon='arrow_back') }}
```

#### tw_btn_danger()
危险按钮 - 红色，用于删除等危险操作

```jinja2
{{ tw_btn_danger(_('删除'), onclick='confirmDelete()', icon='delete') }}
```

#### tw_btn_outline()
轮廓按钮 - 边框样式

| 额外参数 | 类型 | 默认值 | 说明 |
|---------|------|-------|------|
| color | string | 'primary' | 颜色：'primary' / 'danger' / 'slate' |

```jinja2
{{ tw_btn_outline(_('编辑'), href=edit_url, icon='edit', color='slate') }}
{{ tw_btn_outline(_('删除'), onclick='delete()', icon='delete', color='danger') }}
```

#### tw_btn_icon()
图标按钮 - 仅图标

| 额外参数 | 类型 | 默认值 | 说明 |
|---------|------|-------|------|
| variant | string | 'ghost' | 变体：'ghost' / 'primary' / 'danger' |
| title | string | '' | 悬停提示 |

```jinja2
{{ tw_btn_icon('edit', onclick='edit()', title=_('编辑')) }}
{{ tw_btn_icon('delete', onclick='delete()', variant='danger', title=_('删除')) }}
```

### **尺寸对照**

| size | 高度 | 水平内边距 | 字号 |
|-----|------|----------|------|
| sm | h-8 (32px) | px-3 | text-xs |
| md | h-9 (36px) | px-5 | text-sm |
| lg | h-11 (44px) | px-8 | text-base |

### **使用示例**

```jinja2
{% from 'components/tw_buttons.html' import tw_btn_primary, tw_btn_secondary, tw_btn_danger, tw_btn_outline with context %}

<!-- 表单底部按钮组 -->
<div class="flex justify-end gap-3">
    {{ tw_btn_secondary(_('取消'), href=url_for('customer.list')) }}
    {{ tw_btn_primary(_('保存'), type='submit') }}
</div>

<!-- 页面标题操作按钮 -->
<div class="flex items-center gap-2">
    {{ tw_btn_outline(_('编辑'), href=edit_url, icon='edit', size='sm', color='slate') }}
    {{ tw_btn_outline(_('删除'), onclick='confirmDelete()', icon='delete', size='sm', color='danger') }}
</div>

<!-- 动态生成的按钮（在循环中） -->
{% for item in items %}
<div class="flex gap-2">
    {{ tw_btn_secondary(_('取消'), onclick='cancel(' ~ item.id ~ ')') }}
    {{ tw_btn_primary(_('确认'), onclick='confirm(' ~ item.id ~ ')') }}
</div>
{% endfor %}
```

### **已使用页面**
1. `app/templates/customer/tw_view.html` - 客户详情页

### **注意事项**
- 组件使用 Tailwind CSS，仅适用于 Tailwind 页面
- 使用 `href` 参数时会渲染为 `<a>` 标签，否则为 `<button>`
- 在循环中使用动态 `onclick` 时，使用 Jinja2 字符串拼接：`onclick='fn(' ~ id ~ ')'`
- 图标使用 Google Material Symbols

---

## 🔔 Tailwind 确认模态框组件

可复用的 Tailwind CSS 确认模态框组件，用于删除确认、操作确认等场景。

**文件位置**: `app/templates/components/tw_confirm_modal.html`

### **导入方式**
```jinja2
{% from 'components/tw_confirm_modal.html' import tw_confirm_modal, tw_confirm_modal_script, tw_delete_confirm_modal with context %}
```

### **可用宏**

#### tw_confirm_modal()
通用确认模态框

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| modal_id | string | 必填 | 模态框唯一ID |
| title | string | '确认操作' | 标题文本 |
| message | string | '' | 提示消息 |
| confirm_text | string | '确认' | 确认按钮文本 |
| cancel_text | string | '取消' | 取消按钮文本 |
| variant | string | 'danger' | 样式变体：'danger' / 'warning' / 'info' |
| icon | string | '' | 图标名称，默认根据 variant 自动选择 |

#### tw_delete_confirm_modal()
删除确认模态框快捷方式（预设 variant='danger'）

#### tw_confirm_modal_script()
模态框 JavaScript 脚本，必须在页面底部引入

### **JavaScript API**

```javascript
// 打开确认模态框
openConfirmModal('modalId', {
    title: '自定义标题',      // 可选，覆盖模板中的标题
    message: '自定义消息',    // 可选，覆盖模板中的消息
    onConfirm: function() {  // 确认按钮回调
        // 执行操作
    }
});

// 关闭确认模态框
closeConfirmModal('modalId');
```

### **样式变体**

| variant | 图标 | 确认按钮颜色 | 用途 |
|---------|-----|------------|------|
| danger | warning | 红色 | 删除、危险操作 |
| warning | warning | 橙色 | 警告、需注意的操作 |
| info | info | 蓝色 | 信息确认、一般操作 |

### **使用示例**

```jinja2
{% from 'components/tw_confirm_modal.html' import tw_confirm_modal, tw_confirm_modal_script with context %}

<!-- 渲染模态框 -->
{{ tw_confirm_modal(
    modal_id='deleteConfirmModal',
    title=_('确认删除'),
    message=_('确定要删除这条记录吗？此操作无法撤销。'),
    confirm_text=_('删除'),
    cancel_text=_('取消'),
    variant='danger'
) }}

<!-- 触发按钮 -->
<button onclick="openDeleteConfirm()">删除</button>

<!-- 页面底部引入脚本 -->
{{ tw_confirm_modal_script() }}

<script>
function openDeleteConfirm() {
    openConfirmModal('deleteConfirmModal', {
        onConfirm: function() {
            // 执行删除 AJAX 请求
            fetch('/api/delete/123', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    }
                });
        }
    });
}
</script>
```

### **已使用页面**
1. `app/templates/customer/tw_view.html` - 客户详情页删除确认

### **注意事项**
- 组件使用 Tailwind CSS，仅适用于 Tailwind 页面
- 必须在页面底部引入 `tw_confirm_modal_script()` 脚本
- 模态框支持 ESC 键关闭
- 点击背景遮罩也可关闭模态框
- `onConfirm` 回调执行后会自动关闭模态框

---

## 📝 Tailwind 表单模态框组件

可复用的 Tailwind CSS 表单模态框组件，用于创建/编辑表单等场景。

**文件位置**: `app/templates/components/tw_form_modal.html`

### **导入方式**
```jinja2
{% from 'components/tw_form_modal.html' import tw_form_modal, tw_form_modal_script, tw_form_field, tw_form_select, tw_form_textarea, tw_form_checkbox, tw_form_row, tw_tab_content with context %}
```

### **可用宏**

#### tw_form_modal()
主模态框容器，使用 `{% call %}` 方式调用。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| modal_id | string | ✓ | - | 模态框唯一ID |
| title | string | | '表单' | 标题文本 |
| submit_text | string | | '提交' | 提交按钮文本 |
| cancel_text | string | | '取消' | 取消按钮文本 |
| tabs | list | | [] | 标签页配置 |
| size | string | | 'lg' | 尺寸：'sm', 'md', 'lg', 'xl' |
| form_id | string | | modal_id + '-form' | 表单ID |
| form_action | string | | '' | 表单提交地址 |
| form_method | string | | 'POST' | 表单方法 |

#### tw_form_field()
文本输入字段。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| name | string | ✓ | - | 字段名称 |
| label | string | ✓ | - | 标签文本 |
| type | string | | 'text' | 输入类型 |
| placeholder | string | | '' | 占位符文本 |
| value | string | | '' | 默认值 |
| required | bool | | false | 是否必填 |
| readonly | bool | | false | 是否只读 |
| disabled | bool | | false | 是否禁用 |
| help_text | string | | '' | 帮助文本 |
| error | string | | '' | 错误信息 |

#### tw_form_select()
下拉选择字段。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| name | string | ✓ | - | 字段名称 |
| label | string | ✓ | - | 标签文本 |
| options | list | | [] | 选项列表 [{value, label}] |
| value | string | | '' | 选中值 |
| required | bool | | false | 是否必填 |
| placeholder | string | | '' | 占位符文本 |

#### tw_form_textarea()
多行文本字段。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| name | string | ✓ | - | 字段名称 |
| label | string | ✓ | - | 标签文本 |
| rows | int | | 3 | 行数 |
| placeholder | string | | '' | 占位符文本 |
| value | string | | '' | 默认值 |
| required | bool | | false | 是否必填 |

#### tw_form_checkbox()
MD风格圆形复选框，用于 Alpine.js 动态绑定场景。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| label | string | ✓ | - | 标签文本 |
| checked | bool | | false | 默认选中状态（仅用于初始化参考） |
| help_text | string | | '' | 帮助文本 |
| alpine_model | string | ✓ | '' | Alpine.js 绑定的数据模型名称 |
| class | string | | '' | 额外的 CSS 类 |

**使用示例**：
```jinja2
{# 在 Alpine.js x-data 组件内使用 #}
{{ tw_form_checkbox(
    label=_('共享此记录'),
    help_text=_('取消勾选后，此记录仅对管理员和上级账户可见'),
    alpine_model='formData.is_shared'
) }}
```

#### tw_form_row()
表单行（用于多列布局），使用 `{% call %}` 方式调用。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| cols | int | | 2 | 列数 |

#### tw_tab_content()
标签页内容容器，使用 `{% call %}` 方式调用。

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| tab_id | string | ✓ | - | 标签页ID |
| active | bool | | false | 是否默认显示 |

#### tw_form_modal_script()
模态框 JavaScript 脚本，必须在页面底部引入。

### **JavaScript API**

```javascript
// 打开表单模态框
openFormModal('modalId', {
    title: '编辑客户',           // 可选：更新标题
    submitText: '保存',          // 可选：更新提交按钮文本
    data: {                      // 可选：填充表单数据
        company_name: '示例公司',
        industry: '制造业'
    },
    onSubmit: function(data, form) {  // 可选：提交回调
        console.log('表单数据:', data);
    },
    onClose: function() {        // 可选：关闭回调
        console.log('模态框已关闭');
    }
});

// 关闭表单模态框
closeFormModal('modalId');
```

### **基本用法示例**

```jinja2
{% from 'components/tw_form_modal.html' import tw_form_modal, tw_form_modal_script, tw_form_field, tw_form_select, tw_form_textarea, tw_form_row with context %}

<!-- 定义模态框 -->
{% call tw_form_modal(
    modal_id='customerFormModal',
    title=_('编辑客户'),
    submit_text=_('保存'),
    cancel_text=_('取消'),
    size='lg'
) %}
    {{ tw_form_field('company_name', _('企业名称'), placeholder=_('请输入企业名称'), required=true) }}

    {% call tw_form_row(cols=2) %}
        {{ tw_form_select('industry', _('行业'), options=industries, placeholder=_('请选择行业')) }}
        {{ tw_form_select('company_type', _('企业类型'), options=types, required=true) }}
    {% endcall %}

    {{ tw_form_textarea('notes', _('备注'), rows=3) }}
{% endcall %}

<!-- 引入脚本（页面底部） -->
{{ tw_form_modal_script() }}

<!-- 触发按钮 -->
<button onclick="openFormModal('customerFormModal')">编辑</button>
```

### **带标签页的用法**

```jinja2
{% call tw_form_modal(
    modal_id='clientFormModal',
    title=_('创建客户'),
    tabs=[
        {'id': 'profile', 'label': _('客户档案'), 'active': true},
        {'id': 'contacts', 'label': _('联系人')},
        {'id': 'projects', 'label': _('关联项目')}
    ]
) %}
    {% call tw_tab_content('profile', active=true) %}
        {{ tw_form_field('name', _('客户名称')) }}
    {% endcall %}

    {% call tw_tab_content('contacts') %}
        {{ tw_form_field('contact_name', _('联系人姓名')) }}
    {% endcall %}

    {% call tw_tab_content('projects') %}
        <p>项目列表...</p>
    {% endcall %}
{% endcall %}
```

### **已使用页面**
1. `app/templates/customer/tw_view.html` - 客户详情页编辑

### **注意事项**
- 组件使用 Tailwind CSS，仅适用于 Tailwind 页面
- 必须在页面底部引入 `tw_form_modal_script()` 脚本
- 模态框支持 ESC 键关闭
- 点击背景遮罩可关闭模态框
- 表单重置会在关闭时自动执行
- 打开时自动聚焦第一个输入框
- 下拉选择框需要动态加载选项时，建议在打开模态框前先初始化

---

## 📋 Tailwind 行动记录模态框组件

可复用的 Tailwind CSS 行动记录添加模态框组件，用于项目详情页和客户详情页的行动记录添加功能。

**文件位置**: `app/templates/components/tw_action_modal.html`

### **导入方式**
```jinja2
{% from 'components/tw_action_modal.html' import tw_action_modal, tw_action_modal_script with context %}
```

### **组件宏**

#### tw_action_modal()

渲染行动记录添加模态框的 HTML 结构。

```jinja2
{{ tw_action_modal(
    context_type='project',      # 上下文类型：'project' 或 'customer'
    context_id=0,                # 上下文对象ID
    context_name='',             # 上下文对象名称（显示用）
    companies=[],                # 公司列表（project模式使用）
    contacts=[],                 # 联系人列表（customer模式使用）
    projects=[],                 # 项目列表（customer模式使用）
    sidebar_info=none,           # 侧边栏信息字典
    modal_id='addActionModal',   # 模态框ID
    event_name='open-add-action-modal'  # 打开事件名称
) }}
```

**参数说明**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| context_type | string | 是 | 'project' | 上下文类型，支持 'project' 或 'customer' |
| context_id | int | 是 | 0 | 上下文对象的ID |
| context_name | string | 是 | '' | 上下文对象名称，用于只读显示 |
| companies | list | 否 | [] | 公司列表（project模式），每项需要 id, name 属性 |
| contacts | list | 否 | [] | 联系人列表（customer模式），每项需要 id, name 属性 |
| projects | list | 否 | [] | 项目列表（customer模式），每项需要 id, project_name 属性 |
| sidebar_info | dict | 否 | none | 侧边栏信息，包含 label 和 items 列表 |
| modal_id | string | 否 | 'addActionModal' | 模态框的HTML ID |
| event_name | string | 否 | 'open-add-action-modal' | Alpine.js 监听的打开事件名称 |

**sidebar_info 格式**：
```python
sidebar_info = {
    'label': '项目信息',  # 侧边栏标题
    'items': [
        {'label': '项目名称', 'value': project.project_name},
        {'label': '创建时间', 'value': project.created_at.strftime('%Y-%m-%d')},
        ...
    ]
}
```

#### tw_action_modal_script()

渲染行动记录模态框所需的 JavaScript 脚本。

```jinja2
{{ tw_action_modal_script(
    context_type='project',                    # 上下文类型
    context_id=0,                              # 上下文对象ID
    api_endpoint='/project/api/1/add_action',  # 提交API端点
    contacts_api='/project/api/get_company_contacts',  # 获取联系人API（project模式）
    modal_id='addActionModal',                 # 模态框ID
    event_name='open-add-action-modal'         # 打开事件名称
) }}
```

**参数说明**：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| context_type | string | 是 | 'project' | 上下文类型 |
| context_id | int | 是 | 0 | 上下文对象ID |
| api_endpoint | string | 是 | '' | 表单提交的API端点 |
| contacts_api | string | 否 | '' | 获取联系人的API端点（仅project模式使用） |
| modal_id | string | 否 | 'addActionModal' | 模态框ID |
| event_name | string | 否 | 'open-add-action-modal' | 打开事件名称 |

### **使用示例**

#### 项目详情页使用（project模式）

```jinja2
{% from 'components/tw_action_modal.html' import tw_action_modal, tw_action_modal_script with context %}

{# 触发按钮 #}
<button type="button" onclick="openAddActionModal()" class="text-primary">
    {{ _('添加行动记录') }}
</button>

{# 模态框HTML #}
{{ tw_action_modal(
    context_type='project',
    context_id=project.id,
    context_name=project.project_name,
    companies=customer_associations_data,
    sidebar_info={
        'label': _('项目信息'),
        'items': [
            {'label': _('项目名称'), 'value': project.project_name},
            {'label': _('立项日期'), 'value': project.initiated_date.strftime('%Y-%m-%d') if project.initiated_date else '-'}
        ]
    }
) }}

{# 模态框脚本 #}
{{ tw_action_modal_script(
    context_type='project',
    context_id=project.id,
    api_endpoint='/project/api/' ~ project.id ~ '/add_action',
    contacts_api='/project/api/get_company_contacts'
) }}
```

#### 客户详情页使用（customer模式）

```jinja2
{% from 'components/tw_action_modal.html' import tw_action_modal, tw_action_modal_script with context %}

{# 触发按钮 #}
<button type="button" onclick="openAddActionModal()" class="text-primary">
    {{ _('添加记录') }}
</button>

{# 模态框HTML #}
{{ tw_action_modal(
    context_type='customer',
    context_id=company.id,
    context_name=company.company_name,
    contacts=contacts,
    projects=viewable_projects,
    sidebar_info={
        'label': _('客户信息'),
        'items': [
            {'label': _('公司名称'), 'value': company.company_name},
            {'label': _('联系人数'), 'value': contacts|length|string ~ ' 人'}
        ]
    }
) }}

{# 模态框脚本 #}
{{ tw_action_modal_script(
    context_type='customer',
    context_id=company.id,
    api_endpoint='/customer/api/' ~ company.id ~ '/add_action'
) }}
```

### **两种模式的差异**

| 特性 | project 模式 | customer 模式 |
|-----|-------------|---------------|
| 只读字段 | 项目名称 | 客户名称 |
| 选择字段1 | 选择客户（公司） | 选择项目 |
| 选择字段2 | 选择联系人（动态加载） | 选择联系人（预加载） |
| 联系人加载 | 根据选择的公司动态获取 | 页面加载时已有完整列表 |
| API端点 | `/project/api/{id}/add_action` | `/customer/api/{id}/add_action` |

### **已使用页面**
1. `app/templates/project/tw_project_detail.html` - 项目详情页
2. `app/templates/customer/tw_view.html` - 客户详情页

### **注意事项**
- 组件使用 Tailwind CSS + Alpine.js，仅适用于 Tailwind 页面
- 必须在页面底部引入 `tw_action_modal_script()` 脚本
- 模态框支持 ESC 键关闭和点击背景遮罩关闭
- project 模式下，选择公司后会自动加载该公司的联系人列表
- customer 模式下，联系人列表在页面加载时已准备好
- 表单提交成功后会自动刷新页面
- 侧边栏信息为可选功能，不传递则不显示侧边栏

---

## 🏷️ Tailwind 用户徽章组件

### **概述**
Tailwind 风格的用户徽章有两种样式：

| 组件 | 样式 | 适用场景 |
|-----|------|---------|
| `render_tw_owner_badge` | 圆形头像（可带姓名） | 列表、表格、一般展示 |
| `render_tw_owner_pill_badge` | 胶囊形徽章（头像+姓名） | 审批流程、状态展示 |

### **1. render_tw_owner_badge - 圆形头像徽章**

基础的圆形头像徽章，颜色根据用户ID自动分配。

```jinja2
{% from 'macros/ui_helpers.html' import render_tw_owner_badge %}

{# 基础用法 - 仅显示头像 #}
{{ render_tw_owner_badge(user) }}

{# 带姓名显示 #}
{{ render_tw_owner_badge(user, show_name=true) }}

{# 不同尺寸 #}
{{ render_tw_owner_badge(user, size='sm') }}  {# 24px #}
{{ render_tw_owner_badge(user, size='md') }}  {# 32px（默认） #}
{{ render_tw_owner_badge(user, size='lg') }}  {# 40px #}
```

**参数**:
- `owner`: 用户对象（需要 id, real_name, username 属性）
- `size`: 尺寸 - 'sm'(24px), 'md'(32px, 默认), 'lg'(40px)
- `show_name`: 是否显示姓名文字，默认 false

### **2. render_tw_owner_pill_badge - 胶囊形徽章（新）**

带有小圆形头像 + 姓名的胶囊形状徽章，适用于审批流程等需要突出显示状态的场景。

```jinja2
{% from 'macros/ui_helpers.html' import render_tw_owner_pill_badge %}

{# 基础用法 - 默认蓝色 #}
{{ render_tw_owner_pill_badge(user) }}

{# 不同颜色变体 #}
{{ render_tw_owner_pill_badge(user, variant='default') }}  {# 蓝色 #}
{{ render_tw_owner_pill_badge(user, variant='success') }}  {# 绿色 - 已完成/已通过 #}
{{ render_tw_owner_pill_badge(user, variant='warning') }}  {# 琥珀色 - 进行中 #}
{{ render_tw_owner_pill_badge(user, variant='danger') }}   {# 红色 - 拒绝/错误 #}
{{ render_tw_owner_pill_badge(user, variant='muted') }}    {# 灰色 - 未开始 #}

{# 支持传入字符串 #}
{{ render_tw_owner_pill_badge('管理员', variant='success') }}

{# 小尺寸 #}
{{ render_tw_owner_pill_badge(user, variant='warning', size='sm') }}
```

**参数**:
- `owner`: 用户对象或字符串
- `variant`: 颜色变体
  - `'default'`: 蓝色（默认）
  - `'success'`: 绿色（已完成/已通过）
  - `'warning'`: 琥珀色（进行中/待处理）
  - `'danger'`: 红色（拒绝/错误）
  - `'muted'`: 灰色（未开始/禁用）
- `size`: 尺寸 - 'sm' 或 'md'（默认）

**效果预览**:
```
┌─────────────────────┐
│ [头] 管理员         │  ← 蓝色胶囊 (default)
└─────────────────────┘

┌─────────────────────┐
│ [头] 童蕾           │  ← 绿色胶囊 (success)
└─────────────────────┘

┌─────────────────────┐
│ [头] 郭小会         │  ← 琥珀色胶囊 (warning)
└─────────────────────┘
```

### **JavaScript 中使用**

在 JavaScript 动态渲染时，可以使用以下 HTML 结构：

```javascript
// 胶囊徽章 HTML 模板
function renderPillBadge(name, variant = 'default') {
    const initial = name.charAt(0).toUpperCase();

    const variants = {
        'default': {
            bg: 'bg-blue-100 dark:bg-blue-900/50',
            text: 'text-blue-700 dark:text-blue-300',
            avatar: 'bg-blue-500'
        },
        'success': {
            bg: 'bg-green-100 dark:bg-green-900/50',
            text: 'text-green-700 dark:text-green-300',
            avatar: 'bg-green-500'
        },
        'warning': {
            bg: 'bg-amber-100 dark:bg-amber-900/50',
            text: 'text-amber-700 dark:text-amber-300',
            avatar: 'bg-amber-500'
        },
        'danger': {
            bg: 'bg-red-100 dark:bg-red-900/50',
            text: 'text-red-700 dark:text-red-300',
            avatar: 'bg-red-500'
        },
        'muted': {
            bg: 'bg-slate-100 dark:bg-slate-700',
            text: 'text-slate-600 dark:text-slate-300',
            avatar: 'bg-slate-400'
        }
    };

    const config = variants[variant] || variants['default'];

    return `
        <span class="inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}">
            <span class="w-4 h-4 rounded-full ${config.avatar} text-white flex items-center justify-center text-[10px] font-bold">${initial}</span>
            ${name}
        </span>
    `;
}
```

### **已使用页面**
1. `app/templates/project/tw_project_detail.html` - 项目详情页审批流程

---

## 📦 Tailwind 信息卡片组件

### **组件概述**
可复用的键值对信息展示卡片，适用于客户档案、联系人档案、项目信息等场景。

**文件位置**: `app/templates/components/tw_info_card.html`

### **导入方式**
```jinja2
{% from 'components/tw_info_card.html' import tw_info_card, tw_info_item, tw_info_row, tw_info_card_compact %}
```

### **可用宏**

#### tw_info_card()
标准信息卡片，带图标的键值对展示。

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| title | string | '' | 卡片标题 |
| items | list | [] | 信息项列表 |
| columns | int | 1 | 列数（1或2） |
| show_icon | bool | true | 是否显示图标 |
| action_btn | dict | none | 操作按钮配置 {label, icon, onclick, href} |
| show_action | bool | true | 是否显示操作按钮 |
| empty_text | string | '未指定' | 空值显示文本 |
| card_class | string | '' | 额外的卡片CSS类 |

**items 格式**:
```python
items = [
    {'icon': 'business', 'label': _('企业类型'), 'value': company.company_type},
    {'icon': 'apartment', 'label': _('行业'), 'value': company.industry},
    {'icon': 'phone', 'label': _('电话'), 'value': contact.phone, 'link': 'tel:' ~ contact.phone},
    {'label': _('状态'), 'badge': render_status_badge(status), 'hide_empty': true},
    # 带编辑按钮的字段（按钮显示在label旁边）
    {'label': _('负责人'), 'badge': render_owner_badge(owner), 'edit_btn': {'onclick': 'openEditModal()', 'show': has_edit_permission}}
]
```

**item 参数说明**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| icon | string | Material Symbols 图标名称（可选） |
| label | string | 标签文本 |
| value | string | 值（为空时显示"未指定"或自动隐藏） |
| link | string | 值的链接（可选） |
| badge | html | 徽章HTML（可选，替代value显示） |
| hide_empty | bool | 值为空时是否隐藏该项，默认false |
| edit_btn | dict | 编辑按钮配置（可选） |

**edit_btn 配置**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| onclick | string | 点击事件处理函数 |
| show | bool | 是否显示按钮，默认true（用于权限控制） |

#### tw_info_card_compact()
紧凑样式信息卡片，标签和值在同一行。

#### tw_info_item()
单个信息项（用于自定义布局）。

#### tw_info_row()
紧凑的信息行（无图标，标签和值在同一行）。

### **使用示例**

```jinja2
{# 带图标单列 #}
{{ tw_info_card(
    title=_('客户档案'),
    items=[
        {'icon': 'business', 'label': _('企业类型'), 'value': company.company_type},
        {'icon': 'apartment', 'label': _('行业'), 'value': company.industry},
        {'icon': 'public', 'label': _('国家'), 'value': company.country},
        {'icon': 'person', 'label': _('负责人'), 'value': company.owner.real_name}
    ]
) }}

{# 无图标两列 #}
{{ tw_info_card(
    title=_('项目信息'),
    columns=2,
    show_icon=false,
    items=[
        {'label': _('项目名称'), 'value': project.project_name},
        {'label': _('当前阶段'), 'badge': render_stage_badge(project.current_stage)},
        {'label': _('负责人'), 'value': project.owner.real_name},
        {'label': _('创建日期'), 'value': project.created_at|date}
    ],
    action_btn={'label': _('编辑'), 'icon': 'edit', 'onclick': 'openEditModal()'}
) }}

{# 带链接的值 #}
{{ tw_info_card(
    title=_('联系人档案'),
    columns=2,
    items=[
        {'icon': 'phone', 'label': _('电话'), 'value': contact.phone, 'link': 'tel:' ~ contact.phone},
        {'icon': 'email', 'label': _('邮箱'), 'value': contact.email, 'link': 'mailto:' ~ contact.email},
        {'icon': 'business', 'label': _('所属企业'), 'value': company.name, 'link': url_for('customer.view', id=company.id)}
    ]
) }}

{# 带编辑按钮的字段（用于需要修改负责人等场景） #}
{{ tw_info_card(
    title=_('项目信息'),
    columns=2,
    show_icon=false,
    items=[
        {'label': _('项目名称'), 'value': project.project_name},
        {'label': _('当前阶段'), 'badge': render_stage_badge(project.current_stage)},
        {'label': _('项目负责人'), 'badge': render_owner_badge(project.owner),
         'edit_btn': {'onclick': 'openChangeOwnerModal()', 'show': has_change_owner_permission}},
        {'label': _('厂商销售负责人'), 'badge': render_owner_badge(project.vendor_sales_manager),
         'edit_btn': {'onclick': 'openChangeVendorSalesModal()', 'show': has_change_owner_permission}}
    ]
) }}
```

### **已使用页面**
1. `app/templates/customer/tw_view.html` - 客户详情页
2. `app/templates/customer/tw_contact_view.html` - 联系人详情页
3. `app/templates/project/tw_project_detail.html` - 项目详情页
4. `app/templates/quotation/tw_quotation_detail.html` - 报价单详情页

---

## 🎴 Tailwind 卡片外壳组件

### **组件概述**
提供统一的卡片外壳样式，**内容区域完全由调用者自定义**。适用于需要复杂自定义布局的卡片，如价格信息（带进度条）、产品概览（带图片）、二维码卡片等。

**文件位置**: `app/templates/components/tw_card_shell.html`

### **与 tw_info_card 的区别**

| 组件 | 适用场景 | 内容传递方式 |
|------|---------|-------------|
| `tw_info_card` | 简单键值对列表 | `items=[]` 参数 |
| `tw_card_shell` | 复杂自定义布局 | `{% call %}` 模式 |

### **导入方式**
```jinja2
{% from 'components/tw_card_shell.html' import tw_card_shell, tw_card_shell_divided, tw_card_shell_compact %}
```

### **可用宏**

#### tw_card_shell()
标准卡片外壳，标题无下边框。

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| title | string | '' | 卡片标题 |
| subtitle | string | '' | 副标题 |
| action_btn | object | none | 操作按钮 {label, icon, onclick, href} |
| show_action | bool | true | 是否显示操作按钮 |
| header_border | bool | false | 标题栏是否有下边框 |
| padding | string | 'normal' | 内边距: 'normal' / 'compact' / 'none' |
| card_class | string | '' | 额外卡片CSS类 |
| content_class | string | '' | 内容区额外CSS类 |

#### tw_card_shell_divided()
带分隔线的卡片外壳，标题栏有下边框。

#### tw_card_shell_compact()
紧凑型卡片外壳，小标题风格（灰色大写字母）。

### **使用示例**

```jinja2
{# 示例1: 价格信息卡片（带进度条） #}
{% call tw_card_shell(title=_('价格信息')) %}
<div class="space-y-5">
    <div>
        <p class="text-sm text-slate-500 font-medium mb-1">{{ _('市场价格') }}</p>
        <span class="text-3xl font-bold">¥{{ '{:,.2f}'.format(product.retail_price) }}</span>
    </div>
    <div class="pt-4">
        <div class="flex justify-between mb-2">
            <span class="text-xs text-slate-500">{{ _('订单统计') }}</span>
            <span class="font-bold">75%</span>
        </div>
        <div class="w-full bg-slate-200 rounded-full h-2">
            <div class="bg-primary h-2 rounded-full" style="width: 75%"></div>
        </div>
    </div>
</div>
{% endcall %}

{# 示例2: 产品文档卡片（带上传按钮） #}
{% call tw_card_shell(
    title=_('产品文档'),
    action_btn={'label': _('上传PDF'), 'icon': 'upload', 'onclick': 'uploadPdf()'}
) %}
<div class="text-center py-8">
    <span class="material-symbols-outlined text-5xl text-slate-300">description</span>
    <p class="mt-3 text-sm text-slate-500">{{ _('暂无产品文档') }}</p>
</div>
{% endcall %}

{# 示例3: 二维码卡片 #}
{% call tw_card_shell(title=_('产品二维码')) %}
<div class="text-center">
    <div class="inline-block p-3 bg-white rounded-lg border">
        <img src="{{ qrcode_url }}" class="w-32 h-32">
    </div>
    <p class="mt-3 text-xs text-slate-500">{{ _('扫描查看详情') }}</p>
</div>
{% endcall %}

{# 示例4: 元数据卡片（紧凑型） #}
{% call tw_card_shell_compact(title=_('元数据')) %}
<div class="space-y-3 text-sm">
    <div class="flex justify-between">
        <span class="text-slate-500">{{ _('产品ID') }}</span>
        <span>#{{ product.id }}</span>
    </div>
    <div class="flex justify-between">
        <span class="text-slate-500">{{ _('创建时间') }}</span>
        <span>{{ product.created_at.strftime('%Y-%m-%d') }}</span>
    </div>
</div>
{% endcall %}
```

### **适用场景**

| 场景 | 推荐组件 |
|------|---------|
| 价格信息（带进度条、统计） | `tw_card_shell` |
| 产品概览（带图片+信息） | `tw_card_shell` |
| 二维码卡片 | `tw_card_shell` |
| 元数据卡片 | `tw_card_shell_compact` |
| 带列表分隔的内容 | `tw_card_shell_divided` |

---

## 📊 Tailwind 表格卡片组件

### **组件概述**
可复用的 Tailwind CSS 表格卡片组件，用于展示数据表格。

**文件位置**: `app/templates/components/tw_table_card.html`

### **导入方式**
```jinja2
{% from 'components/tw_table_card.html' import render_tw_table_card, render_empty_state, render_table_card_styles %}
```

### **可用宏**

#### render_tw_table_card()
渲染表格卡片容器，使用 `{% call %}` 方式调用。

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| title | string | '' | 卡片标题 |
| view_all_url | string | none | "查看全部"链接地址 |
| view_all_text | string | '查看全部' | "查看全部"链接文本 |
| action_btn | dict | none | 操作按钮配置 `{onclick, label}` 或 `{href, label}` |
| max_height | string | '300px' | 表格区域最大高度 |
| headers | list | [] | 表头配置 `[{label, width, align}]` |
| empty_text | string | none | 无数据时显示的文本 |
| card_id | string | none | 卡片ID（用于JS操作） |

**注意**：`action_btn` 和 `view_all_url` 二选一，`action_btn` 优先。

#### render_empty_state()
渲染空状态占位（表格行形式）。

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| text | string | '' | 提示消息 |
| icon | string | 'inbox' | Material Symbol 图标名 |

### **使用示例**

```jinja2
{% from 'components/tw_table_card.html' import render_tw_table_card, render_empty_state %}

{# 带添加按钮的表格 #}
{% call render_tw_table_card(
    title=_('关联客户'),
    action_btn={'onclick': 'showAddDialog()', 'label': _('添加客户')} if has_permission else none,
    max_height='280px',
    headers=[
        {'label': _('客户'), 'width': '50%'},
        {'label': _('添加人'), 'width': '30%'},
        {'label': _('操作'), 'width': '20%'}
    ]
) %}
    {% for item in items %}
    <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/50">
        <td class="p-3">{{ item.name }}</td>
        <td class="p-3">{{ item.creator }}</td>
        <td class="p-3">...</td>
    </tr>
    {% else %}
    {{ render_empty_state(_('暂无关联客户'), 'group') }}
    {% endfor %}
{% endcall %}

{# 带查看全部链接的表格 #}
{% call render_tw_table_card(
    title=_('关联项目'),
    view_all_url=url_for('project.list'),
    headers=[{'label': _('项目名称')}, {'label': _('阶段')}]
) %}
    ...
{% endcall %}
```

### **已使用页面**
1. `app/templates/customer/tw_view.html` - 客户详情页（关联项目、报价单）
2. `app/templates/project/tw_project_detail.html` - 项目详情页（关联客户）

---

## 📝 Tailwind 项目列表卡片组件

### **组件概述**
带头像的项目列表卡片组件，适用于联系人列表、关联报价单等场景。

**文件位置**: `app/templates/components/tw_item_list_card.html`

### **导入方式**
```jinja2
{% from 'components/tw_item_list_card.html' import tw_item_list_card, tw_item_list_item, tw_item_list_empty %}
```

### **可用宏**

#### tw_item_list_card()
卡片容器，使用 `{% call %}` 方式调用。

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| title | string | '' | 卡片标题 |
| view_all_url | string | '' | "查看全部"链接地址 |
| view_all_text | string | '查看全部' | "查看全部"链接文本 |
| action_btn | dict | none | 操作按钮配置 `{onclick, label}` 或 `{href, label}` |

**注意**：`action_btn` 和 `view_all_url` 二选一，`action_btn` 优先。

#### tw_item_list_item()
列表项。

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| avatar_text | string | '?' | 头像文字（取前2个字符） |
| avatar_color_index | int | 0 | 头像颜色索引（0-5） |
| avatar_neutral | bool | false | 使用中性灰色头像 |
| title | string | '' | 标题文字 |
| subtitle | string | '' | 副标题文字 |
| link_url | string | '' | 标题链接 |
| badge | html | none | 右侧徽章 |
| show_arrow | bool | false | 显示右侧箭头 |

#### tw_item_list_empty()
空状态提示。

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| text | string | '暂无数据' | 提示文字 |

### **使用示例**

```jinja2
{% from 'components/tw_item_list_card.html' import tw_item_list_card, tw_item_list_item, tw_item_list_empty %}

{# 联系人列表（带添加按钮、中性头像、徽章） #}
{% call tw_item_list_card(
    title=_('联系人'),
    action_btn={'onclick': 'openAddModal()', 'label': _('添加')} if has_permission else none
) %}
    {% if contacts %}
        {% for contact in contacts %}
        {{ tw_item_list_item(
            avatar_text=contact.name,
            avatar_neutral=true,
            title=contact.name,
            subtitle=contact.position,
            link_url=url_for('customer.view_contact', contact_id=contact.id),
            badge=render_tw_primary_badge() if contact.is_primary else none
        ) }}
        {% endfor %}
    {% else %}
        {{ tw_item_list_empty(_('暂无联系人')) }}
    {% endif %}
{% endcall %}

{# 关联报价单（彩色头像、查看全部链接） #}
{% call tw_item_list_card(
    title=_('关联报价单'),
    view_all_url=url_for('quotation.list')
) %}
    {% for q in quotations %}
    {{ tw_item_list_item(
        avatar_text=q.owner.real_name,
        avatar_color_index=q.owner.id % 6,
        title=q.quotation_number,
        subtitle=q.amount|currency,
        link_url=url_for('quotation.view', id=q.id),
        show_arrow=true
    ) }}
    {% endfor %}
{% endcall %}
```

### **已使用页面**
1. `app/templates/customer/tw_view.html` - 客户详情页（联系人列表）
2. `app/templates/quotation/tw_quotation_detail.html` - 报价单详情页（关联报价单）

---

## ✅ Tailwind 审批流程组件

### **组件概述**
Tailwind 风格的审批流程展示组件，用于显示审批进度和执行审批操作。

**文件位置**: `app/templates/components/tw_approval_flow.html`

### **导入方式**
```jinja2
{% from 'components/tw_approval_flow.html' import render_tw_approval_flow_card, render_tw_approval_flow_script, render_tw_approval_modals %}
```

### **可用宏**

#### render_tw_approval_flow_card()
渲染审批流程卡片容器。

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| status | string | 必填 | 对象当前状态 |
| container_id | string | 'approvalFlowContainer' | 容器DOM ID |

#### render_tw_approval_flow_script()
渲染审批流程的 JavaScript 脚本。

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| object_type | string | 必填 | 对象类型（如 'expense', 'project'） |
| object_id | int | 必填 | 对象ID |
| object_status | string | 必填 | 对象状态 |
| creator_name | string | 必填 | 创建人名称 |
| api_base | string | 必填 | API基础路径 |
| container_id | string | 'approvalFlowContainer' | 容器DOM ID |

#### render_tw_approval_modals()
渲染审批确认模态框（同意/驳回）。

### **使用示例**

```jinja2
{% from 'components/tw_approval_flow.html' import render_tw_approval_flow_card, render_tw_approval_flow_script, render_tw_approval_modals %}

<!-- 渲染审批流程卡片（放在页面内容区域） -->
{{ render_tw_approval_flow_card(expense.status, container_id='approvalFlowContainer') }}

<!-- 渲染确认模态框（放在模态框区域） -->
{{ render_tw_approval_modals() }}

<!-- 渲染审批流程脚本（放在脚本区域） -->
{{ render_tw_approval_flow_script(
    'expense',
    expense.id,
    expense.status,
    expense.owner.real_name or expense.owner.username,
    '/expense/api/approval',
    'approvalFlowContainer'
) }}
```

### **功能特性**
- 纯 Tailwind 样式，无需引入额外 CSS
- 竖向时间线展示审批进度
- 内联审批操作（审批人可直接在时间线中操作）
- 当前节点脉冲动画效果
- 完整的深色模式支持
- 完整的中英文国际化支持

### **已使用页面**
1. `app/templates/project/tw_project_detail.html` - 项目详情页
2. `app/templates/expense/tw_expense_detail.html` - 报销单详情页

### **注意事项**
- 组件使用 Tailwind CSS，仅适用于 Tailwind 页面
- 需要后端提供审批流程相关 API 接口
- 审批状态变更后会自动刷新页面

---

## 🗂️ Tailwind 标签页组件

### **文件位置**
`app/templates/components/tw_tabs.html`

### **功能概述**
可复用的 Tailwind CSS 标签页导航组件，支持：
- Material Symbols 图标
- 计数徽章
- 深色模式
- 传统 JavaScript 回调模式
- Alpine.js 响应式模式（新增）

### **宏列表**

| 宏名称 | 说明 |
|-------|------|
| `render_tw_tabs()` | 传统标签页（需要 JavaScript 回调） |
| `render_tw_tabs_script()` | 标签页切换脚本 |
| `render_tw_alpine_tabs()` | Alpine.js 标签页（在 x-data 上下文中使用） |
| `render_tw_tabs_update_script()` | 更新标签页计数脚本 |

### **render_tw_tabs() - 传统模式**

用于需要 JavaScript 回调控制的场景。

#### 参数
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| tabs | list | ✓ | - | 标签页配置列表 |
| current_tab | string | ✓ | - | 当前激活的标签键 |

#### tabs 配置项
| 属性 | 类型 | 说明 |
|-----|------|------|
| key | string | 标签唯一键 |
| label | string | 显示文本 |
| icon | string | Material Symbols 图标名称 |
| icon_class | string | 图标额外样式类（如 'text-amber-500'） |
| count | number | 计数徽章（可选） |

#### 使用示例
```jinja2
{% from 'components/tw_tabs.html' import render_tw_tabs, render_tw_tabs_script %}

<!-- 渲染标签页 -->
{{ render_tw_tabs(
    tabs=[
        {'key': 'created', 'label': '我发起的', 'icon': 'upload_file', 'count': 5},
        {'key': 'pending', 'label': '待我审批', 'icon': 'hourglass_top', 'icon_class': 'text-amber-500', 'count': 3}
    ],
    current_tab='created'
) }}

<!-- 标签页内容 -->
<div id="tab-created" class="tab-panel">创建内容</div>
<div id="tab-pending" class="tab-panel hidden">待审批内容</div>

<!-- 脚本 -->
<script>
window.onTabChange = function(tabKey) {
    // 隐藏所有面板
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    // 显示当前面板
    document.getElementById('tab-' + tabKey).classList.remove('hidden');
};
</script>
{{ render_tw_tabs_script(on_change_callback='onTabChange') }}
```

### **render_tw_alpine_tabs() - Alpine.js 模式**

用于 Alpine.js x-data 上下文中的响应式标签页。

#### 参数
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| tabs | list | ✓ | - | 标签页配置列表（同上） |
| model | string | | 'activeTab' | Alpine.js 数据模型名称 |
| container_class | string | | '' | 容器额外样式类 |

#### 使用示例
```jinja2
{% from 'components/tw_tabs.html' import render_tw_alpine_tabs %}

<div x-data="{ activeTab: 'goals' }">
    <!-- 渲染标签页 -->
    {{ render_tw_alpine_tabs(
        tabs=[
            {'key': 'goals', 'label': _('目标达成'), 'icon': 'target'},
            {'key': 'expense', 'label': _('报销预算'), 'icon': 'receipt_long'},
            {'key': 'activity', 'label': _('活跃度'), 'icon': 'trending_up'}
        ],
        model='activeTab'
    ) }}

    <!-- 标签页内容 -->
    <div x-show="activeTab === 'goals'" x-cloak>目标内容</div>
    <div x-show="activeTab === 'expense'" x-cloak>报销内容</div>
    <div x-show="activeTab === 'activity'" x-cloak>活跃度内容</div>
</div>
```

### **已使用页面**
- `templates/user/tw_detail.html` - 用户详情页（基本信息、权限、归属、绩效标签页）
- `templates/components/tw_performance_dashboard.html` - 绩效看板（目标、报销、活跃度、行业分布）
- `templates/approval/tw_center.html` - 审批中心

### **样式说明**
- 激活状态：`text-primary border-b-2 border-primary bg-white dark:bg-slate-800`
- 非激活状态：`text-slate-500 hover:text-primary border-transparent`
- 徽章激活：`bg-primary/10 text-primary`
- 徽章非激活：`bg-slate-100 dark:bg-slate-700`

---

## 📈 SVG 折线图组件

`app/templates/components/tw_line_chart.html`

纯 SVG 实现的月度趋势折线图，无需 ECharts 等第三方库。

### **特点**
- 12个月数据点，贝塞尔曲线平滑连接
- 渐变面积填充
- 悬停提示显示具体数值
- 最大值点特殊高亮
- 支持暗色模式

### **可用宏**

| 宏名称 | 说明 |
|--------|------|
| `render_tw_line_chart(chart_id, color)` | 渲染 SVG 容器 |
| `render_tw_line_chart_style()` | 渲染必需的 CSS 样式（每页一次） |
| `render_tw_line_chart_script(chart_id, data_var, unit, color, month_label)` | 渲染静态初始化脚本 |
| `render_tw_line_chart_init_fn(month_label)` | 渲染动态初始化函数（用于 Alpine.js） |

### **静态使用示例（如首页仪表盘）**

```jinja2
{% from 'components/tw_line_chart.html' import render_tw_line_chart, render_tw_line_chart_script, render_tw_line_chart_style %}

{# 1. 渲染 SVG 容器 #}
{{ render_tw_line_chart(chart_id='expenseMonthlyChart', color='#2979ff') }}

{# 2. 引入样式（每页只需一次） #}
{{ render_tw_line_chart_style() }}

{# 3. 准备数据并渲染脚本 #}
<script>
    const monthlyExpenseData = {{ expense_monthly_stats | tojson }};
</script>
{{ render_tw_line_chart_script(
    chart_id='expenseMonthlyChart',
    data_var='monthlyExpenseData',
    unit='元',
    color='#2979ff',
    month_label=_('月')
) }}
```

### **动态使用示例（如 Alpine.js 组件）**

```jinja2
{% from 'components/tw_line_chart.html' import render_tw_line_chart, render_tw_line_chart_style, render_tw_line_chart_init_fn %}

{# 1. 渲染 SVG 容器 #}
{{ render_tw_line_chart(chart_id='goalTrendChart', color='#22c55e') }}

{# 2. 引入样式和初始化函数 #}
{{ render_tw_line_chart_style() }}
{{ render_tw_line_chart_init_fn(_('月')) }}

{# 3. 在 Alpine.js 中动态调用 #}
<script>
function myComponent() {
    return {
        data: [],
        initChart() {
            if (typeof window.initSvgLineChart === 'function') {
                window.initSvgLineChart('goalTrendChart', this.data, {
                    unit: '万元',
                    color: '#22c55e',
                    monthLabel: '月'
                });
            }
        }
    };
}
</script>
```

### **参数说明**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `chart_id` | string | 必填 | 图表唯一ID |
| `color` | string | `#2979ff` | 主题色（十六进制） |
| `data_var` | string | 必填 | JavaScript 数据变量名 |
| `unit` | string | `''` | 值单位（如 '元'、'万元'） |
| `month_label` | string | `'月'` | 月份标签文本 |

### **已使用页面**
- `app/templates/index.html` - 首页仪表盘报销月度趋势
- `app/templates/components/tw_performance_dashboard.html` - 绩效看板植入额趋势

---

## 📝 Tailwind Mention 编辑器组件

### **组件概述**
支持 `@` 用户和 `#` 项目引用的富文本编辑器组件。

**文件位置**: `app/templates/components/tw_mention_editor.html`

**功能特性**:
- 输入 `@` 触发用户选择下拉框（客户端过滤）
- 输入 `#` 触发项目搜索下拉框（API 搜索）
- 选择后插入为标签样式
- 编辑时标签不可点击，预览/提交后可点击跳转
- 键盘导航支持（↑↓选择，Enter/Tab确认，Esc取消）
- 完整的暗色模式支持
- 提供 `renderMentionPreview()` 函数用于预览模式渲染可点击链接

### **基本用法**

```jinja2
{% from 'components/tw_mention_editor.html' import tw_mention_editor, tw_mention_editor_script %}

{{ tw_mention_editor(
    editor_id='logEditor',
    users_data=shareable_users_tree,
    placeholder=_('描述您的工作日志、进度和成果...'),
    initial_value=log_data.additional_notes,
    max_length=5000,
    min_height='280px'
) }}

{# 在页面底部添加脚本 #}
{{ tw_mention_editor_script() }}
```

### **参数说明**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `editor_id` | string | 必填 | 编辑器唯一ID |
| `users_data` | list | 必填 | 用户树数据（格式与 shareable_users_tree 一致） |
| `placeholder` | string | `''` | 占位文本 |
| `initial_value` | string | `''` | 初始值（存储格式的文本） |
| `max_length` | int | `5000` | 最大字符数 |
| `min_height` | string | `'280px'` | 最小高度 |
| `project_search_url` | string | `'/api/v1/search/projects'` | 项目搜索 API 地址 |

### **存储格式**

文本中的用户和项目引用使用特殊标记格式存储：

```
今天和 @[张三|user:123] 讨论了 #[项目Alpha|project:456] 的需求
```

- 用户：`@[显示名|user:ID]`
- 项目：`#[显示名|project:ID]`

### **JavaScript API**

通过 Alpine.js 数据栈访问编辑器实例：

```javascript
const editorContainer = document.getElementById('logEditor-container');
if (editorContainer && editorContainer._x_dataStack) {
    const editorData = editorContainer._x_dataStack[0];

    // 获取存储格式的值
    const value = editorData.getValue();

    // 获取提及的用户和项目ID列表
    const mentionData = editorData.getMentionData();
    // { users: [123, 456], projects: [789] }

    // 设置内容
    editorData.setValue('新内容 @[张三|user:123]');
}
```

### **预览模式渲染**

使用 `renderMentionPreview()` 函数将存储格式转换为可点击链接：

```html
<div x-html="renderMentionPreview(content, '/user/detail/', '/project/')"></div>
```

参数：
- `text`: 存储格式的文本
- `userUrlPattern`: 用户链接模式，默认 `/user/{id}`
- `projectUrlPattern`: 项目链接模式，默认 `/project/{id}`

### **后端保存示例**

```python
# 接收数据
data = request.get_json()
additional_notes = data.get('additional_notes', '').strip() or None
mentioned_users = data.get('mentioned_users', [])  # [123, 456]
mentioned_projects = data.get('mentioned_projects', [])  # [789]

# 保存到数据库
worklog.additional_notes = additional_notes
worklog.mentioned_users = mentioned_users if mentioned_users else None
worklog.mentioned_projects = mentioned_projects if mentioned_projects else None
```

### **已使用页面**
- `app/templates/worklog/tw_calendar.html` - 日历日志编辑

---

## 📐 详情页卡片高度同步工具

### **文件位置**
`app/static/js/detail-card-sync.js`

### **功能描述**
用于将多个卡片的高度同步到参考列的高度，实现详情页多列布局的底部对齐效果。适用于 Tailwind 详情页的多列布局场景。

### **使用场景**
- 详情页三列或四列布局
- 左侧信息卡片需要与右侧边栏底部对齐
- 中间列（如变更历史）需要固定高度并支持内部滚动

### **HTML 结构要求**

```html
<!-- 多列布局容器 -->
<div class="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
    <!-- 基本信息列 - 需要同步高度 -->
    <div id="basicInfoColumn" class="lg:col-span-2">
        <div class="...">卡片内容</div>
    </div>

    <!-- 变更历史列 - 需要同步高度 -->
    <div class="lg:col-span-1">
        <div id="changeHistoryCard" class="... flex flex-col">
            <div class="flex-shrink-0">标题区</div>
            <div class="flex-1 overflow-y-auto">内容区（可滚动）</div>
        </div>
    </div>

    <!-- 右侧边栏 - 作为高度参考基准 -->
    <div id="rightSidebarColumn" class="lg:col-span-1 space-y-4">
        <div>关联卡片</div>
        <div>元数据卡片</div>
    </div>
</div>
```

### **API 文档**

```javascript
DetailCardSync.init(referenceId, targetIds, options)
```

**参数说明**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|-----|------|-----|--------|------|
| `referenceId` | string | 是 | - | 参考元素的ID（高度基准） |
| `targetIds` | string/string[] | 是 | - | 需要同步高度的目标元素ID数组 |
| `options.delay` | number | 否 | 100 | 初始化延迟时间（毫秒） |
| `options.syncOnResize` | boolean | 否 | true | 是否在窗口大小变化时同步 |
| `options.targetSelector` | string | 否 | null | 目标元素内部的选择器 |

**方法**

| 方法 | 说明 |
|-----|------|
| `DetailCardSync.init()` | 初始化高度同步 |
| `DetailCardSync.sync()` | 手动执行一次高度同步 |
| `DetailCardSync.reset()` | 重置高度（移除固定高度） |

### **使用示例**

**基础用法**
```html
<script src="{{ url_for('static', filename='js/detail-card-sync.js') }}"></script>
<script>
// 以右侧列为基准，同步变更历史卡片高度
DetailCardSync.init('rightSidebarColumn', ['changeHistoryCard']);
</script>
```

**同步多个卡片**
```html
<script>
// 同步变更历史卡片（直接设置高度）
DetailCardSync.init('rightSidebarColumn', ['changeHistoryCard'], {
    delay: 150
});

// 同步基本信息卡片（需要选择内部子元素）
DetailCardSync.init('rightSidebarColumn', ['basicInfoColumn'], {
    delay: 150,
    targetSelector: '> div'  // 选择直接子元素
});
</script>
```

**手动同步**
```javascript
// 在某些操作后手动同步高度
DetailCardSync.sync();
```

### **注意事项**

1. **Grid 布局**: 使用 `items-start` 而非 `items-stretch`，让每列保持自然高度
2. **内部滚动**: 需要同步高度的卡片内容区域应添加 `flex-1 overflow-y-auto`
3. **延迟执行**: 默认延迟 100ms 执行，确保 DOM 渲染完成
4. **响应式**: 默认在窗口大小变化时自动重新同步

### **已使用页面**
- `app/templates/quotation/tw_quotation_detail.html` - 报价单详情页

---

## ✍️ Tailwind 签字板组件

可复用的手写签名组件，支持鼠标和触摸屏输入，用于供应商确认、合同签署等场景。

**文件位置**: `app/templates/components/tw_signature_pad.html`

### **导入方式**
```jinja2
{% from 'components/tw_signature_pad.html' import tw_signature_pad, tw_signature_pad_script with context %}
```

### **可用宏**

#### tw_signature_pad()
签字板 HTML 组件

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|-------|------|
| container_id | string | 'signaturePad' | 容器ID（必须唯一） |
| label | string | '签名' | 标签文本 |
| required | boolean | false | 是否必填 |
| readonly | boolean | false | 只读模式（仅显示已有签名） |
| existing_signature | string | '' | 已有签名URL（只读模式用） |
| height | int | 150 | 画布高度（像素） |

#### tw_signature_pad_script()
签字板 JavaScript 脚本，页面底部只需调用一次

### **JavaScript API**

```javascript
// 初始化（通常自动完成）
SignaturePadManager.init('containerId');

// 获取签字板实例
const pad = SignaturePadManager.get('containerId');

// 检查是否为空
if (pad.isEmpty()) {
    alert('请签名');
    return;
}

// 获取签名 base64 数据
const signatureData = pad.toDataURL();

// 清除签名
pad.clear();
```

### **使用示例**

**基本使用**
```jinja2
{% from 'components/tw_signature_pad.html' import tw_signature_pad, tw_signature_pad_script with context %}

<!-- 签字板 -->
{{ tw_signature_pad(
    container_id='mySignature',
    label=_('确认签名'),
    required=true,
    height=120
) }}

<!-- 脚本（页面底部，只需一次） -->
{{ tw_signature_pad_script() }}
```

**只读模式（显示已有签名）**
```jinja2
{{ tw_signature_pad(
    container_id='viewSignature',
    label=_('签名'),
    readonly=true,
    existing_signature=order.supplier_signature_url
) }}
```

**表单提交时获取签名**
```javascript
// 验证签名
const signaturePad = SignaturePadManager.get('mySignature');
if (!signaturePad || signaturePad.isEmpty()) {
    alert('请签名确认');
    return;
}

// 获取 base64 数据
const signatureData = signaturePad.toDataURL();

// 添加到 FormData
const formData = new FormData();
formData.append('signature', signatureData);
```

### **功能特性**
- ✅ 支持鼠标和触摸屏绘制
- ✅ 高分辨率支持（devicePixelRatio）
- ✅ 深色模式自动适配
- ✅ 导出为 PNG base64
- ✅ 只读模式显示已有签名
- ✅ 窗口大小变化时自动重绘

### **已使用页面**
1. `app/templates/inventory/tw_purchase_order_detail.html` - 采购订单供应商确认签名

### **创建日期**
2026-01-11

---

## 📝 更新日志

- **2026-01-11**: 新增签字板组件（`tw_signature_pad.html`），支持手写签名、触摸屏、导出 base64
- **2026-01-09**: 新增详情页卡片高度同步工具（`detail-card-sync.js`），支持多列布局底部对齐
- **2026-01-03**: 新增 Mention 编辑器组件（`tw_mention_editor.html`），支持 @ 用户和 # 项目引用
- **2025-12-27**: 新增 SVG 折线图组件（`tw_line_chart.html`），从首页仪表盘提取，支持静态和 Alpine.js 动态初始化
- **2025-12-27**: 新增 Tailwind 标签页组件文档（`tw_tabs.html`）
- **2025-12-27**: 扩展标签页组件，新增 `render_tw_alpine_tabs()` 宏支持 Alpine.js 响应式模式
- **2025-12-12**: 从 CLAUDE-COMPONENTS.md 拆分创建本文档
- **2025-12-12**: 新增 `tw_action_list_card` 组件完整功能（表格布局、回复、快速添加、分页）
- **2025-12-12**: 新增 Tailwind 审批流程组件文档
