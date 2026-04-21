# Task Team View Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 部门负责人和管理员可在任务中心顶部看到一排成员头像（仅显示有活跃任务的人），点击后切换查看该成员的任务视角。

**Architecture:** 分三层改动：① 路由层 `task_management()` 查询有权限查看的活跃成员并传入模板；② API 层 `management_list()` 支持 `view_user_id` 参数并做权限校验；③ 前端层在模板头像栏 + JS 中加入切换逻辑。

**Tech Stack:** Flask/SQLAlchemy, Alpine.js, Tailwind CSS, Jinja2

---

### Task 1: 后端 - 路由层查询活跃成员

**Files:**
- Modify: `app/views/task.py:780-784`

**背景知识：**
- `current_user.role == 'admin'` 或 `current_user.role == 'ceo'` → 管理员
- `current_user.is_department_manager == True` → 部门负责人
- `current_user.department` + `current_user.company_name` → 所在部门+公司
- 活跃任务定义：`Task.status NOT IN ('completed', 'cancelled')` 且 `Task.is_deleted == False`
- User 字段：`real_name`（优先）、`username`（备用）

**Step 1: 修改 `task_management()` 路由，查询活跃成员**

找到 `app/views/task.py` 第 780 行，将：
```python
@task.route('/management')
@login_required
def task_management():
    """任务管理页面"""
    return render_template('task/tw_task_management.html')
```

替换为：
```python
@task.route('/management')
@login_required
def task_management():
    """任务管理页面"""
    team_members = []
    can_view_team = False

    is_admin = current_user.role in ('admin', 'ceo')
    is_dept_mgr = getattr(current_user, 'is_department_manager', False)

    if is_admin or is_dept_mgr:
        can_view_team = True

        # 有活跃任务的 user_id 集合
        active_assignee_ids = db.session.query(Task.assignee_id).filter(
            Task.is_deleted == False,
            Task.status.notin_(['completed', 'cancelled']),
        )

        if is_admin:
            # 管理员：全公司范围
            users = User.query.filter(
                User.id.in_(active_assignee_ids),
                User._is_active == True,
            ).order_by(User.real_name).all()
        else:
            # 部门负责人：仅本部门
            users = User.query.filter(
                User.id.in_(active_assignee_ids),
                User.department == current_user.department,
                User.company_name == current_user.company_name,
                User._is_active == True,
            ).order_by(User.real_name).all()

        for u in users:
            if u.id == current_user.id:
                continue  # "我" 单独处理，始终排第一
            name = u.real_name or u.username
            team_members.append({
                'id': u.id,
                'name': name,
                'initials': name[:2] if name else '?',
            })

    return render_template(
        'task/tw_task_management.html',
        can_view_team=can_view_team,
        team_members=team_members,
    )
```

**注意：** 需要在文件顶部确认已导入 `User`。用 grep 检查：
```bash
grep "from app.models" app/views/task.py | head -5
```

**Step 2: 手工验证**

启动应用后，用管理员账号访问 `/task/management`，打开浏览器开发者工具确认页面无 500 错误。

**Step 3: Commit**
```bash
git add app/views/task.py
git commit -m "feat(task): route passes active team members to management template"
```

---

### Task 2: 后端 - API 层支持 view_user_id

**Files:**
- Modify: `app/views/task.py:787-888`（`management_list` 函数）

**Step 1: 在 `management_list()` 函数内，`uid = current_user.id` 这行之后加入权限校验**

找到第 800 行附近：
```python
        uid = current_user.id
        query = Task.query.filter(Task.is_deleted == False)
```

替换为：
```python
        uid = current_user.id

        # 代理查看：管理员或部门负责人可查看他人任务
        view_user_id = request.args.get('view_user_id', type=int)
        if view_user_id and view_user_id != uid:
            is_admin = current_user.role in ('admin', 'ceo')
            is_dept_mgr = getattr(current_user, 'is_department_manager', False)
            if is_admin:
                uid = view_user_id
            elif is_dept_mgr:
                target = User.query.get(view_user_id)
                if target and target.department == current_user.department \
                        and target.company_name == current_user.company_name:
                    uid = view_user_id
                # 若不在同部门，忽略参数（安全降级，不报错）

        query = Task.query.filter(Task.is_deleted == False)
```

**Step 2: 验证 API 行为**

在浏览器或 curl 测试：
```bash
curl -b cookies.txt "http://localhost:5000/task/api/management/list?tab=all&view_user_id=999"
```
- 管理员调用 → 返回 user 999 的任务
- 普通用户调用 → 忽略 view_user_id，返回自己的任务（安全降级）

**Step 3: Commit**
```bash
git add app/views/task.py
git commit -m "feat(task): management list API supports view_user_id for team leaders/admins"
```

---

### Task 3: 前端 - 模板头像栏 HTML

**Files:**
- Modify: `app/templates/task/tw_task_management.html`

**背景：** 头像栏插在左侧栏顶部操作区的「标题+新建按钮」行之后，搜索框之前。找到第 53-65 行区域：

```html
{# 顶部操作栏 #}
<div class="px-3 pt-3 pb-2 border-b border-slate-100 dark:border-slate-800 space-y-2">
    {# 标题 + 新建按钮 #}
    <div class="flex items-center justify-between">
        ...
    </div>

    {# 搜索 #}
    <div class="relative">
```

**Step 1: 在标题行 `</div>` 和 `{# 搜索 #}` 之间插入头像栏**

```jinja2
    {% if can_view_team %}
    {# 成员切换栏 #}
    <div class="flex items-center gap-1.5 overflow-x-auto pb-0.5 scrollbar-none">
        {# 我 - 始终第一 #}
        <button @click="setViewUser(null)"
                :class="viewUserId === null
                    ? 'ring-2 ring-primary bg-primary/10'
                    : 'bg-slate-100 dark:bg-slate-700 hover:bg-primary/10'"
                class="flex-shrink-0 flex flex-col items-center gap-0.5 px-1.5 py-1 rounded-lg transition cursor-pointer">
            <div class="w-7 h-7 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center">
                {{ (current_user.real_name or current_user.username)[:2] }}
            </div>
            <span class="text-[10px] text-slate-600 dark:text-slate-400 w-8 text-center truncate">{{ _('我') }}</span>
        </button>

        {% for m in team_members %}
        <button @click="setViewUser({{ m.id }}, '{{ m.name }}')"
                :class="viewUserId === {{ m.id }}
                    ? 'ring-2 ring-primary bg-primary/10'
                    : 'bg-slate-100 dark:bg-slate-700 hover:bg-primary/10'"
                class="flex-shrink-0 flex flex-col items-center gap-0.5 px-1.5 py-1 rounded-lg transition cursor-pointer">
            <div class="w-7 h-7 rounded-full bg-slate-400 text-white text-xs font-bold flex items-center justify-center">
                {{ m.initials }}
            </div>
            <span class="text-[10px] text-slate-600 dark:text-slate-400 w-8 text-center truncate">{{ m.name[:3] }}</span>
        </button>
        {% endfor %}
    </div>

    {# 正在查看他人时显示提示条 #}
    <div x-show="viewUserId !== null"
         x-cloak
         class="flex items-center gap-1 text-xs text-primary bg-primary/5 rounded-md px-2 py-1">
        <span class="material-symbols-outlined text-sm">visibility</span>
        <span>{{ _('正在查看') }}：<span x-text="viewUserName"></span></span>
        <button @click="setViewUser(null)" class="ml-auto text-slate-400 hover:text-primary transition">
            <span class="material-symbols-outlined text-sm">close</span>
        </button>
    </div>
    {% endif %}
```

**Step 2: 在模板的 `<script>` 初始化块（第 801 行附近）加入团队权限标记**

找到：
```html
<script>window.CURRENT_USER_ID = {{ current_user.id }};</script>
```

在其后加：
```html
<script>window.CAN_VIEW_TEAM = {{ 'true' if can_view_team else 'false' }};</script>
```

**Step 3: Commit**
```bash
git add app/templates/task/tw_task_management.html
git commit -m "feat(task): add team member avatar switcher to task management UI"
```

---

### Task 4: 前端 - JS 切换逻辑

**Files:**
- Modify: `app/static/js/task-management.js`

**Step 1: 在 Alpine data 对象中加入新状态变量**

找到 `currentUserId: null,` 这行（约第 99 行），在其后加入：
```javascript
        // ── 团队视图 ──
        viewUserId: null,
        viewUserName: '',
```

**Step 2: 在 `loadTasks()` 的 URLSearchParams 中加入 view_user_id**

找到（约第 154 行）：
```javascript
                const params = new URLSearchParams({
                    tab: this.tab,
                    sort: this.sortBy,
                    search: this.search,
                    per_page: '50',
                });
```

替换为：
```javascript
                const params = new URLSearchParams({
                    tab: this.tab,
                    sort: this.sortBy,
                    search: this.search,
                    per_page: '50',
                });
                if (this.viewUserId) {
                    params.set('view_user_id', this.viewUserId);
                }
```

**Step 3: 在 Alpine 方法列表中加入 `setViewUser` 方法**

在 `loadTasks()` 函数之后加入：
```javascript
        setViewUser(userId, userName = '') {
            this.viewUserId = userId;
            this.viewUserName = userName;
            this.selectedTaskId = null;
            this.selectedTask = null;
            this.loadTasks();
        },
```

**Step 4: 手工测试**

1. 管理员账号进入 `/task/management`
2. 确认头像栏显示（若有其他人有活跃任务）
3. 点击某成员头像 → 任务列表刷新 → 顶部显示蓝色提示条"正在查看：张三"
4. 点击提示条右侧 ✕ → 恢复自己的任务视图
5. 普通用户账号进入 → 头像栏不显示，行为与之前完全一致

**Step 5: Commit**
```bash
git add app/static/js/task-management.js
git commit -m "feat(task): JS setViewUser logic for team task switching"
```

---

### Task 5: 翻译补全

**Files:**
- Modify: `app/translations/en/LC_MESSAGES/messages.po`

**Step 1: 检查新增的中文字符串是否已有翻译**

```bash
grep -n "正在查看" app/translations/en/LC_MESSAGES/messages.po
```

**Step 2: 若无，在 messages.po 末尾（`#~ msgid` 之前）添加**

```po
msgid "正在查看"
msgstr "Viewing"
```

**Step 3: 编译翻译**
```bash
pybabel compile -d app/translations
```

**Step 4: Commit**
```bash
git add app/translations/
git commit -m "i18n(task): add translation for team view label"
```

---

## 完成验证清单

- [ ] 管理员进入任务中心，头像栏显示有活跃任务的成员
- [ ] 部门负责人只看到本部门成员
- [ ] 普通用户无头像栏，页面行为不变
- [ ] 点击成员头像切换视角，顶部显示"正在查看：xxx"
- [ ] 点击 ✕ 恢复自己的任务
- [ ] 切换后所有 tab（我的/创建/协助/审核/全部）均以被查看者的视角工作
- [ ] 非授权用户直接调用 API 加 `view_user_id` → 被忽略，不报错
