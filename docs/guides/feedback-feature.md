# 用户反馈/问题上报功能 — 开发计划

> **状态**: 待开发
> **创建日期**: 2026-01-29
> **优先级**: 中

---

## 概述

在系统中添加一个反馈机制，让用户遇到故障时可以：
1. 描述问题（标题 + 详细描述）
2. 截取屏幕截图（支持文件上传、Ctrl+V 粘贴、拖拽）
3. 后台日志自动随之提交（最近50行 `app.log`）

**入口**：每个页面右下角的浮动按钮（所有登录用户可见），管理员通过导航菜单管理反馈。

---

## 新建文件（5个）

### 1. `app/models/feedback.py` — 数据模型

**Feedback 主表字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| title | String(200) | 反馈标题 |
| description | Text | 详细描述 |
| feedback_type | String(20) | bug / suggestion / question |
| priority | String(20) | low / medium / high |
| status | String(20) | open / in_progress / resolved / closed |
| page_url | String(500) | 发生问题的页面URL（前端自动捕获） |
| user_agent | String(500) | 浏览器信息（前端自动捕获） |
| captured_logs | Text | 后端日志（提交时自动读取 app.log 最后50行） |
| admin_notes | Text | 管理员备注 |
| created_by | Integer FK→users.id | 创建者 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| resolved_at | DateTime | 解决时间 |
| is_deleted | Boolean | 软删除 |

**FeedbackAttachment 附件表：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| feedback_id | Integer FK→feedbacks.id | 关联反馈 |
| filename | String(255) | 文件名 |
| storage_path | String(500) | 存储路径 |
| file_url | String(500) | 访问URL |
| file_size | Integer | 文件大小 |
| file_type | String(50) | 文件类型 |
| created_at | DateTime | 创建时间 |

**模型模式**：遵循 `app/models/announcement.py` 模式，使用 `get_local_time()` 上海时区、`is_deleted` 软删除、`to_dict()` 序列化方法、关系定义使用 `cascade='all, delete-orphan'`。

---

### 2. `app/views/feedback.py` — 路由蓝图

```python
feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')
```

**路由定义：**

| 方法 | 端点 | 权限 | 说明 |
|------|------|------|------|
| GET | `/feedback/my` | @login_required | 我的反馈列表页面 |
| GET | `/feedback/admin` | @permission_required('feedback', 'view') | 管理员管理页面 |
| POST | `/feedback/api/create` | @login_required | 提交反馈（自动捕获日志） |
| GET | `/feedback/api/get/<id>` | @login_required（owner 或 admin） | 获取反馈详情 |
| POST | `/feedback/api/update-status/<id>` | @permission_required('feedback', 'edit') | 更新反馈状态 |
| POST | `/feedback/api/add-notes/<id>` | @permission_required('feedback', 'edit') | 添加管理员备注 |
| POST | `/feedback/api/upload-screenshot/<id>` | @login_required | 上传截图附件 |
| POST | `/feedback/api/delete/<id>` | @permission_required('feedback', 'delete') | 软删除反馈 |

**关键实现细节：**

- **日志捕获逻辑**：`api/create` 路由中，用 seek-from-end 方式高效读取 `app.log` 最后50行，存入 `captured_logs` 字段。避免读取整个文件。
- **截图上传**：参考公告附件模式（`app/views/announcement.py` 的 `api_upload_attachment`），使用 `smart_storage_manager`，复用 `invoice` bucket。
- **详情权限**：检查 `feedback.created_by == current_user.id` 或 `has_permission('feedback', 'view')`，确保普通用户只能看自己的反馈。

---

### 3. `app/templates/components/tw_feedback_button.html` — 浮动按钮+模态框组件

全局组件，包含两个 Jinja2 宏：

**`render_tw_feedback_button()`**
- 右下角浮动按钮（`fixed bottom-6 right-6 z-50`）
- 使用 `bug_report` Material 图标
- 点击打开 Alpine.js 内联模态框（`x-teleport="body"`）

**`render_tw_feedback_script()`**
- Alpine.js `feedbackWidget()` 组件逻辑
- 管理模态框开关状态
- 处理文件选择、剪贴板粘贴（`@paste.window`）、拖拽
- 截图预览（`FileReader` + `URL.createObjectURL`）
- 提交流程：
  1. `fetch('/feedback/api/create', { ... })` 创建反馈记录
  2. 成功后逐个 `fetch('/feedback/api/upload-screenshot/<id>')` 上传截图
  3. 显示成功通知（使用 `showNotification()`）

**模态框表单内容：**
- 反馈类型选择按钮组（缺陷报告 / 功能建议 / 使用问题）
- 标题输入框（必填）
- 详细描述文本域（必填）
- 截图区域：拖拽区 + 文件选择 + 粘贴提示 + 缩略图预览网格
- 自动捕获：`window.location.href`（page_url）、`navigator.userAgent`（user_agent）
- 底部提示："系统日志将自动附带提交"

---

### 4. `app/templates/feedback/tw_admin_list.html` — 管理员管理页面

参考 `app/templates/announcement/tw_list.html` 结构：

**组件使用：**
- `tw_layout`（active_page='feedback_admin'）
- `tw_fixed_page`（固定头部+可滚动内容）
- `tw_filter_bar`（筛选栏：状态、类型、搜索）
- `tw_data_table`（数据表格）

**页面内容：**
- 统计卡片：总数、待处理、处理中、已解决
- 表格列：标题、类型、优先级、状态、提交人、创建时间、操作
- 操作按钮：查看详情、更新状态、删除
- 详情模态框（`tw_custom_modal`）：
  - 基本信息：标题、描述、类型、优先级、状态
  - 截图预览（图片缩略图网格）
  - 上下文信息：页面URL、浏览器信息
  - 后端日志：`<pre>` 块，带滚动条，最大高度限制
  - 管理员备注：可编辑文本域
  - 状态操作按钮：标记处理中 / 已解决 / 已关闭

---

### 5. `app/templates/feedback/tw_my_list.html` — 用户反馈列表

简化版管理页面：
- 使用 `tw_layout`（active_page='feedback_my'）
- 只显示 `current_user` 自己提交的反馈
- 只读查看，不含管理操作（无删除、无状态更新）
- 状态徽章显示处理进度
- 详情模态框（简化版，不含管理员备注编辑和日志）

---

## 修改文件（5个）

### 1. `app/models/__init__.py`

**位置**：第39行（announcement 导入之后）

```python
# 添加导入
from app.models.feedback import Feedback, FeedbackAttachment
```

在 `__all__` 列表末尾（第77行附近）添加：
```python
'Feedback', 'FeedbackAttachment'
```

---

### 2. `app/__init__.py`

**位置**：第824行（announcement_bp 注册之后）

```python
# 注册反馈管理蓝图
from app.views.feedback import feedback_bp
app.register_blueprint(feedback_bp)
csrf.exempt(feedback_bp)  # 豁免反馈蓝图的CSRF保护（含文件上传）
```

---

### 3. `app/templates/components/tw_layout.html`

**位置1**：`render_tw_layout` 宏中第196行（`</div>` 之前，`{% endmacro %}` 之前）

```jinja2
{# 浮动反馈按钮 - 所有登录用户可见 #}
{% if current_user.is_authenticated %}
{% from 'components/tw_feedback_button.html' import render_tw_feedback_button %}
{{ render_tw_feedback_button() }}
{% endif %}
```

**位置2**：`render_tw_layout_script()` 宏中第207行附近（`render_onboarding_resources()` 之后）

```jinja2
{# 反馈按钮脚本 #}
{% if current_user.is_authenticated %}
{% from 'components/tw_feedback_button.html' import render_tw_feedback_script %}
{{ render_tw_feedback_script() }}
{% endif %}
```

---

### 4. `app/templates/components/tw_nav_menu.html`

**修改1 - 第238行**：系统管理组条件中添加反馈权限检查

```jinja2
{% if has_permission('system_settings', 'edit') or has_permission('announcement', 'view') or has_permission('feedback', 'view') or ... %}
```

**修改2 - 第239行**：`active_page` 列表中添加 `'feedback_admin'`

```jinja2
<div x-data="{ open: {{ 'true' if active_page in ['admin', 'version', 'approval_config', 'notification', 'history', 'backup', 'announcement', 'feedback_admin'] else 'false' }} }">
```

**修改3 - 第253行**：公告菜单项 `{% endif %}` 之后添加反馈管理菜单项

```jinja2
{% if has_permission('feedback', 'view') %}
<a class="flex items-center gap-3 px-3 py-2 rounded-lg {% if active_page == 'feedback_admin' %}bg-primary/20 dark:bg-primary/30{% else %}hover:bg-slate-100 dark:hover:bg-slate-800{% endif %}" href="{{ url_for('feedback.admin_list') }}">
    <span class="material-symbols-outlined text-base {% if active_page == 'feedback_admin' %}fill text-primary{% else %}text-slate-500 dark:text-slate-400{% endif %}">bug_report</span>
    <span class="{% if active_page == 'feedback_admin' %}text-primary{% else %}text-slate-600 dark:text-slate-300{% endif %} text-sm">{{ _('反馈管理') }}</span>
</a>
{% endif %}
```

---

### 5. `app/translations/en/LC_MESSAGES/messages.po`

添加约20条翻译条目：

```po
# ===== 反馈管理模块 =====

msgid "问题反馈"
msgstr "Feedback"

msgid "反馈管理"
msgstr "Feedback Management"

msgid "我的反馈"
msgstr "My Feedback"

msgid "反馈类型"
msgstr "Feedback Type"

msgid "缺陷报告"
msgstr "Bug Report"

msgid "功能建议"
msgstr "Feature Suggestion"

msgid "使用问题"
msgstr "Usage Question"

msgid "简要描述遇到的问题"
msgstr "Briefly describe the issue"

msgid "请详细描述问题的操作步骤和期望结果..."
msgstr "Please describe the steps to reproduce and expected result..."

msgid "截图"
msgstr "Screenshots"

msgid "拖拽、粘贴截图或"
msgstr "Drag, paste screenshot or"

msgid "点击上传"
msgstr "click to upload"

msgid "支持 Ctrl+V 粘贴截图"
msgstr "Ctrl+V paste supported"

msgid "系统日志将自动附带提交"
msgstr "System logs will be automatically attached"

msgid "提交反馈"
msgstr "Submit Feedback"

msgid "提交中..."
msgstr "Submitting..."

msgid "反馈提交成功"
msgstr "Feedback submitted successfully"

msgid "请输入反馈标题"
msgstr "Please enter feedback title"

msgid "请输入反馈描述"
msgstr "Please enter feedback description"

msgid "管理员备注"
msgstr "Admin Notes"

msgid "后端日志"
msgstr "Backend Logs"

msgid "页面地址"
msgstr "Page URL"

msgid "浏览器信息"
msgstr "Browser Info"
```

编译命令：
```bash
pybabel compile -d app/translations
```

---

## 数据库迁移

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db migrate -m "add_feedback_tables"
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

---

## 权限配置

| 角色 | 提交反馈 | 查看自己的反馈 | 管理所有反馈 |
|------|---------|--------------|------------|
| 所有登录用户 | ✅ | ✅ | ❌ |
| admin / CEO | ✅ | ✅ | ✅ |

- 提交反馈：`@login_required`（无需特殊权限）
- 查看自己的反馈：`/feedback/my`（`@login_required`）
- 管理所有反馈：`/feedback/admin`（需 `feedback:view/edit/delete` 权限）
- 详情接口权限检查：`feedback.created_by == current_user.id` 或 `has_permission('feedback', 'view')`

---

## 实施顺序

| 步骤 | 任务 | 文件 | 依赖 |
|------|------|------|------|
| 1 | 创建数据模型 | `app/models/feedback.py` | 无 |
| 2 | 注册模型 | `app/models/__init__.py` | 步骤1 |
| 3 | 运行数据库迁移 | `migrations/versions/xxx.py`（自动生成） | 步骤2 |
| 4 | 创建路由蓝图 | `app/views/feedback.py` | 步骤1 |
| 5 | 注册蓝图 | `app/__init__.py` | 步骤4 |
| 6 | 创建浮动按钮组件 | `app/templates/components/tw_feedback_button.html` | 无 |
| 7 | 集成浮动按钮到布局 | `app/templates/components/tw_layout.html` | 步骤6 |
| 8 | 创建管理员页面 | `app/templates/feedback/tw_admin_list.html` | 步骤4 |
| 9 | 创建用户页面 | `app/templates/feedback/tw_my_list.html` | 步骤4 |
| 10 | 添加导航菜单项 | `app/templates/components/tw_nav_menu.html` | 步骤4 |
| 11 | 更新翻译文件并编译 | `messages.po` | 步骤6-10 |

---

## 验证清单

- [ ] 启动应用，确认数据库迁移成功（`feedbacks` 和 `feedback_attachments` 表已创建）
- [ ] 登录任意用户，确认右下角浮动 bug_report 按钮可见
- [ ] 点击浮动按钮，确认模态框正常弹出
- [ ] 选择反馈类型，填写标题和描述
- [ ] 使用 Ctrl+V 粘贴截图，确认缩略图预览正常
- [ ] 使用文件上传添加截图，确认预览和删除正常
- [ ] 提交反馈，确认成功提示出现
- [ ] 进入"我的反馈"页面（`/feedback/my`），确认能看到刚提交的反馈
- [ ] 以管理员登录，确认导航菜单出现"反馈管理"
- [ ] 进入"反馈管理"页面（`/feedback/admin`），确认能看到所有用户的反馈
- [ ] 查看反馈详情，确认截图可预览、后端日志已捕获
- [ ] 更新反馈状态（待处理→处理中→已解决），确认状态变更正常
- [ ] 添加管理员备注，确认保存成功
- [ ] 切换中英文，确认所有翻译正确
- [ ] 非管理员用户确认看不到"反馈管理"菜单，无法访问管理页面

---

## 参考文件

| 用途 | 文件路径 |
|------|---------|
| 模型参考 | `app/models/announcement.py` |
| 路由参考 | `app/views/announcement.py` |
| 模板参考 | `app/templates/announcement/tw_list.html` |
| 布局组件 | `app/templates/components/tw_layout.html` |
| 导航菜单 | `app/templates/components/tw_nav_menu.html` |
| 文件上传组件 | `app/templates/components/tw_file_upload.html` |
| 文件上传JS | `app/static/js/file-upload-component.js` |
| 智能存储 | `app/utils/smart_storage_manager.py` |
| 通知组件 | `app/static/js/common/tw-notification.js` |
| 模型注册 | `app/models/__init__.py` |
| 蓝图注册 | `app/__init__.py`（第822-824行附近） |
