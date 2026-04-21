# 任务管理系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 建立通用任务管理系统，支持子任务/节点、里程碑确认、协作人、时间线追踪，以"左列表+右详情"分栏页面为主界面，所有操作在一个页面完成。

**Architecture:** 在现有 Task/TaskAttachment/TaskReply 基础上扩展 3 个字段 + 新建 3 张表（SubTask、SubTaskUpdate、SubTaskAttachment）。前端采用 Tailwind + Alpine.js 分栏布局（参考 tw_wiki.html），弹窗处理创建/编辑/确认操作。复用现有审批通知、文件存储、用户搜索等基础设施。

**Tech Stack:** Flask + SQLAlchemy + PostgreSQL / Tailwind CSS + Alpine.js / smart_storage_manager / Message 通知

---

## 现有基础（可复用）

| 组件 | 文件 | 可复用内容 |
|------|------|-----------|
| Task 模型 | `app/models/task.py:22-80` | 核心字段、to_dict()、to_calendar_event() |
| TaskAttachment | `app/models/task.py:150-163` | 附件模型 |
| TaskReply | `app/models/task.py:166-176` | 回复模型 |
| Task API | `app/views/task.py` (605行) | 完整 CRUD + 附件 + 回复 + 日历 |
| Task 弹窗组件 | `app/templates/components/tw_task_modal.html` (950+行) | 创建/详情弹窗、Alpine.js 数据结构 |
| 通知系统 | `app/models/message.py:657-720` | create_task_assigned/completed |
| 智能存储 | `app/utils/smart_storage_manager.py` | upload_file(bucket_type='task') |
| 用户搜索 | `/user/api/users/active` | 活跃用户列表 |
| 分栏布局参考 | `app/templates/knowledge/tw_wiki.html:74-294` | flex 左右分栏 + 可折叠侧栏 |
| 迁移链 | `migrations/versions/add_tasks_tables_20260210.py` | 当前最新 Task 迁移 |
| 模型注册 | `app/models/__init__.py:42` | Task 导入位置 |
| Blueprint | `app/__init__.py:918` | task_bp 注册位置 |

---

## 子任务并行化评估

### 依赖图

```
Task 1 (数据模型)
  ├──→ Task 2 (子任务 API)        ──┐
  │                                  ├──→ Task 4 (通知) ──→ Task 5 (前端页面) ──→ Task 6 (翻译)
  └──→ Task 3 (Task API 扩展)     ──┘
```

### 并行化建议

| 阶段 | 任务 | 可否并行 | 方式 |
|------|------|---------|------|
| Phase 1 | Task 1: 数据模型 + 迁移 | ❌ 必须先完成 | 顺序执行 |
| Phase 2 | Task 2 + Task 3: API 开发 | ✅ 可并行 | 两个子任务同时开发，Task 2 处理 SubTask 相关，Task 3 处理 Task 扩展 |
| Phase 3 | Task 4: 通知扩展 | ❌ 依赖 API | 顺序执行 |
| Phase 4 | Task 5: 前端页面 | ❌ 依赖全部 API | 顺序执行（最大工作量） |
| Phase 5 | Task 6: 翻译 + 收尾 | ❌ 最后 | 顺序执行 |

**结论：Phase 2 的 Task 2 和 Task 3 适合用子任务并行开发（两个独立的 API 模块），其余顺序执行。**

---

## Task 1: 数据模型 + 数据库迁移

**Files:**
- Modify: `app/models/task.py:22-80` — 扩展 Task 模型
- Create: `app/models/subtask.py` — SubTask + SubTaskUpdate + SubTaskAttachment 模型
- Modify: `app/models/__init__.py:42` — 注册新模型
- Create: `migrations/versions/add_subtask_tables_YYYYMMDD.py` — 迁移文件

### Step 1: 扩展 Task 模型（3 个字段）

在 `app/models/task.py` 的 Task 类中添加：

```python
# 在 due_date (行 46) 之后添加
start_date = db.Column(db.Date, nullable=True, comment='任务开始日期')

# 在 customer_id (行 61) 之后添加
shared_with_users = db.Column(db.JSON, default=list, comment='协助人员ID列表')
task_type = db.Column(db.String(30), default='general', comment='任务类型: general/product_dev/custom')
```

更新 `to_dict()` 方法（行 82-109），添加：

```python
'start_date': self.start_date.isoformat() if self.start_date else None,
'shared_with_users': self.shared_with_users or [],
'task_type': self.task_type or 'general',
'subtask_count': len([s for s in self.subtasks if not s.is_deleted]) if hasattr(self, 'subtasks') else 0,
'subtask_completed': len([s for s in self.subtasks if not s.is_deleted and s.status == 'completed']) if hasattr(self, 'subtasks') else 0,
'milestone_count': len([s for s in self.subtasks if not s.is_deleted and s.is_milestone]) if hasattr(self, 'subtasks') else 0,
'milestone_confirmed': len([s for s in self.subtasks if not s.is_deleted and s.is_milestone and s.milestone_status == 'confirmed']) if hasattr(self, 'subtasks') else 0,
```

在 Task 类中添加 subtasks 关系：

```python
subtasks = db.relationship('SubTask', backref='task', lazy='dynamic',
                           cascade='all, delete-orphan')
```

### Step 2: 创建 SubTask 模型

创建 `app/models/subtask.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""子任务模型 - 任务下的节点/子任务，支持里程碑确认"""

from datetime import datetime, timezone
from app import db


class SubTask(db.Model):
    """子任务/节点"""
    __tablename__ = 'subtasks'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # 人员
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 时间
    start_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)

    # 状态: pending / in_progress / completed / delayed
    status = db.Column(db.String(20), default='pending', nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    # 排序
    sort_order = db.Column(db.Integer, default=0)

    # 里程碑
    is_milestone = db.Column(db.Boolean, default=False, nullable=False)
    milestone_confirmer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    milestone_status = db.Column(db.String(20), nullable=True, comment='pending_confirmation/confirmed/rejected')
    milestone_confirmed_at = db.Column(db.DateTime, nullable=True)
    milestone_comment = db.Column(db.Text, nullable=True, comment='确认/驳回意见')

    # 系统字段
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # 关系
    assignee = db.relationship('User', foreign_keys=[assignee_id], lazy='joined')
    milestone_confirmer = db.relationship('User', foreign_keys=[milestone_confirmer_id], lazy='joined')
    updates = db.relationship('SubTaskUpdate', backref='subtask', lazy='dynamic',
                              cascade='all, delete-orphan',
                              order_by='SubTaskUpdate.created_at.desc()')

    __table_args__ = (
        db.Index('ix_subtasks_task_status', 'task_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'assignee_id': self.assignee_id,
            'assignee_name': (self.assignee.real_name or self.assignee.username) if self.assignee else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'sort_order': self.sort_order,
            'is_milestone': self.is_milestone,
            'milestone_confirmer_id': self.milestone_confirmer_id,
            'milestone_confirmer_name': (self.milestone_confirmer.real_name or self.milestone_confirmer.username) if self.milestone_confirmer else None,
            'milestone_status': self.milestone_status,
            'milestone_confirmed_at': self.milestone_confirmed_at.isoformat() if self.milestone_confirmed_at else None,
            'milestone_comment': self.milestone_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'update_count': self.updates.filter_by(is_deleted=False).count(),
        }


class SubTaskUpdate(db.Model):
    """子任务跟进记录"""
    __tablename__ = 'subtask_updates'

    id = db.Column(db.Integer, primary_key=True)
    subtask_id = db.Column(db.Integer, db.ForeignKey('subtasks.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # 关系
    author = db.relationship('User', lazy='joined')
    attachments = db.relationship('SubTaskAttachment', backref='update', lazy='joined',
                                  cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'subtask_id': self.subtask_id,
            'author_id': self.author_id,
            'author_name': (self.author.real_name or self.author.username) if self.author else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'attachments': [a.to_dict() for a in self.attachments if not a.is_deleted],
        }


class SubTaskAttachment(db.Model):
    """子任务跟进附件"""
    __tablename__ = 'subtask_attachments'

    id = db.Column(db.Integer, primary_key=True)
    update_id = db.Column(db.Integer, db.ForeignKey('subtask_updates.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    file_type = db.Column(db.String(100), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    uploader = db.relationship('User', lazy='joined')

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'storage_path': self.storage_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'uploaded_by': self.uploaded_by,
            'uploader_name': (self.uploader.real_name or self.uploader.username) if self.uploader else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

### Step 3: 注册模型

在 `app/models/__init__.py` 的 Task 导入行（行 42）附近添加：

```python
from app.models.subtask import SubTask, SubTaskUpdate, SubTaskAttachment
```

在 `__all__` 列表中添加 `'SubTask', 'SubTaskUpdate', 'SubTaskAttachment'`。

### Step 4: 创建迁移文件

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && cd /Users/nijie/Documents/PMA && flask db migrate -m "add_subtask_tables_and_extend_task"
```

检查生成的迁移文件，确认包含：
- `tasks` 表新增 `start_date`、`shared_with_users`、`task_type` 三列
- 创建 `subtasks` 表 + 索引
- 创建 `subtask_updates` 表 + 索引
- 创建 `subtask_attachments` 表 + 索引

### Step 5: 执行迁移

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

### Step 6: 提交

```bash
git add app/models/task.py app/models/subtask.py app/models/__init__.py migrations/versions/
git commit -m "feat(task): add SubTask model with milestone support + extend Task with start_date/shared_users"
```

---

## Task 2: 子任务 API（可与 Task 3 并行）

**Files:**
- Create: `app/views/subtask.py` — 子任务相关所有 API
- Modify: `app/__init__.py:918` — 注册新 blueprint

### Step 1: 创建子任务 API Blueprint

创建 `app/views/subtask.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""子任务 API"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timezone, date
from app import db
from app.models.task import Task
from app.models.subtask import SubTask, SubTaskUpdate, SubTaskAttachment
from app.models.message import Message
from app.utils.smart_storage_manager import get_smart_storage

subtask_bp = Blueprint('subtask', __name__, url_prefix='/subtask')


def _can_access_task(task):
    """检查当前用户是否有权访问任务（创建人/负责人/协助人）"""
    if current_user.id == task.creator_id or current_user.id == task.assignee_id:
        return True
    shared = task.shared_with_users or []
    return current_user.id in shared


def _can_edit_task(task):
    """检查当前用户是否有权编辑任务（创建人）"""
    return current_user.id == task.creator_id


# ── 子任务 CRUD ──────────────────────────────────────────────

@subtask_bp.route('/api/task/<int:task_id>/subtasks', methods=['GET'])
@login_required
def list_subtasks(task_id):
    """获取任务的所有子任务"""
    task = Task.query.get_or_404(task_id)
    if not _can_access_task(task):
        return jsonify({'success': False, 'message': '无权访问'}), 403

    subtasks = SubTask.query.filter_by(task_id=task_id, is_deleted=False)\
        .order_by(SubTask.sort_order, SubTask.created_at).all()

    result = []
    for st in subtasks:
        d = st.to_dict()
        # 附带最近的跟进记录
        recent_updates = st.updates.filter_by(is_deleted=False)\
            .order_by(SubTaskUpdate.created_at.desc()).limit(5).all()
        d['updates'] = [u.to_dict() for u in recent_updates]
        result.append(d)

    return jsonify({'success': True, 'data': result})


@subtask_bp.route('/api/task/<int:task_id>/subtasks', methods=['POST'])
@login_required
def create_subtask(task_id):
    """创建子任务"""
    task = Task.query.get_or_404(task_id)
    if not _can_access_task(task):
        return jsonify({'success': False, 'message': '无权操作'}), 403

    data = request.get_json()
    if not data or not data.get('title', '').strip():
        return jsonify({'success': False, 'message': '标题不能为空'}), 400

    # 获取当前最大 sort_order
    max_order = db.session.query(db.func.max(SubTask.sort_order))\
        .filter_by(task_id=task_id, is_deleted=False).scalar() or 0

    subtask = SubTask(
        task_id=task_id,
        title=data['title'].strip(),
        description=data.get('description', '').strip() or None,
        assignee_id=data.get('assignee_id'),
        start_date=_parse_date(data.get('start_date')),
        due_date=_parse_date(data.get('due_date')),
        sort_order=max_order + 1,
        is_milestone=data.get('is_milestone', False),
        milestone_confirmer_id=data.get('milestone_confirmer_id') if data.get('is_milestone') else None,
    )
    db.session.add(subtask)
    db.session.commit()

    # 通知负责人
    if subtask.assignee_id and subtask.assignee_id != current_user.id:
        Message.create_subtask_assigned(
            sender=current_user,
            recipient_id=subtask.assignee_id,
            task=task,
            subtask=subtask
        )
        db.session.commit()

    return jsonify({'success': True, 'data': subtask.to_dict(), 'message': '子任务已创建'})


@subtask_bp.route('/api/subtask/<int:subtask_id>', methods=['PUT'])
@login_required
def update_subtask(subtask_id):
    """更新子任务"""
    subtask = SubTask.query.get_or_404(subtask_id)
    task = Task.query.get_or_404(subtask.task_id)
    if not _can_access_task(task):
        return jsonify({'success': False, 'message': '无权操作'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无数据'}), 400

    updatable = ['title', 'description', 'assignee_id', 'sort_order',
                 'is_milestone', 'milestone_confirmer_id']
    for field in updatable:
        if field in data:
            setattr(subtask, field, data[field])

    if 'start_date' in data:
        subtask.start_date = _parse_date(data['start_date'])
    if 'due_date' in data:
        subtask.due_date = _parse_date(data['due_date'])

    # 非里程碑时清除确认人
    if not subtask.is_milestone:
        subtask.milestone_confirmer_id = None
        subtask.milestone_status = None

    db.session.commit()
    return jsonify({'success': True, 'data': subtask.to_dict(), 'message': '已更新'})


@subtask_bp.route('/api/subtask/<int:subtask_id>', methods=['DELETE'])
@login_required
def delete_subtask(subtask_id):
    """删除子任务（软删除）"""
    subtask = SubTask.query.get_or_404(subtask_id)
    task = Task.query.get_or_404(subtask.task_id)
    if not _can_edit_task(task):
        return jsonify({'success': False, 'message': '仅创建人可删除'}), 403

    subtask.is_deleted = True
    db.session.commit()
    return jsonify({'success': True, 'message': '已删除'})


# ── 子任务状态变更 ────────────────────────────────────────────

@subtask_bp.route('/api/subtask/<int:subtask_id>/start', methods=['POST'])
@login_required
def start_subtask(subtask_id):
    """开始子任务"""
    subtask = SubTask.query.get_or_404(subtask_id)
    task = Task.query.get_or_404(subtask.task_id)
    if not _can_access_task(task):
        return jsonify({'success': False, 'message': '无权操作'}), 403

    subtask.status = 'in_progress'
    db.session.commit()
    return jsonify({'success': True, 'data': subtask.to_dict()})


@subtask_bp.route('/api/subtask/<int:subtask_id>/complete', methods=['POST'])
@login_required
def complete_subtask(subtask_id):
    """完成子任务"""
    subtask = SubTask.query.get_or_404(subtask_id)
    task = Task.query.get_or_404(subtask.task_id)
    if not _can_access_task(task):
        return jsonify({'success': False, 'message': '无权操作'}), 403

    # 里程碑子任务：提交确认而非直接完成
    if subtask.is_milestone and subtask.milestone_confirmer_id:
        subtask.status = 'in_progress'
        subtask.milestone_status = 'pending_confirmation'
        db.session.commit()

        # 通知确认人
        Message.create_milestone_confirmation_request(
            sender=current_user,
            recipient_id=subtask.milestone_confirmer_id,
            task=task,
            subtask=subtask
        )
        db.session.commit()
        return jsonify({'success': True, 'data': subtask.to_dict(), 'message': '已提交里程碑确认'})

    # 非里程碑：直接完成
    subtask.status = 'completed'
    subtask.completed_at = datetime.now(timezone.utc)
    db.session.commit()

    # 通知任务创建人
    if task.creator_id != current_user.id:
        Message.create_subtask_completed(
            sender=current_user,
            recipient_id=task.creator_id,
            task=task,
            subtask=subtask
        )
        db.session.commit()

    return jsonify({'success': True, 'data': subtask.to_dict(), 'message': '子任务已完成'})


# ── 里程碑确认 ────────────────────────────────────────────────

@subtask_bp.route('/api/subtask/<int:subtask_id>/milestone/confirm', methods=['POST'])
@login_required
def confirm_milestone(subtask_id):
    """确认里程碑"""
    subtask = SubTask.query.get_or_404(subtask_id)
    task = Task.query.get_or_404(subtask.task_id)

    if current_user.id != subtask.milestone_confirmer_id:
        return jsonify({'success': False, 'message': '仅指定确认人可操作'}), 403

    data = request.get_json() or {}
    action = data.get('action')  # 'confirm' or 'reject'
    comment = data.get('comment', '').strip()

    if action == 'confirm':
        subtask.milestone_status = 'confirmed'
        subtask.milestone_confirmed_at = datetime.now(timezone.utc)
        subtask.milestone_comment = comment or None
        subtask.status = 'completed'
        subtask.completed_at = datetime.now(timezone.utc)
        msg = '里程碑已确认'
    elif action == 'reject':
        subtask.milestone_status = 'rejected'
        subtask.milestone_comment = comment or None
        subtask.status = 'delayed'
        msg = '里程碑已驳回，节点标记为延迟'
    else:
        return jsonify({'success': False, 'message': '无效操作'}), 400

    db.session.commit()

    # 通知任务负责人和创建人
    notify_ids = set()
    if task.assignee_id:
        notify_ids.add(task.assignee_id)
    if task.creator_id:
        notify_ids.add(task.creator_id)
    if subtask.assignee_id:
        notify_ids.add(subtask.assignee_id)
    notify_ids.discard(current_user.id)

    for uid in notify_ids:
        Message.create_milestone_result(
            sender=current_user,
            recipient_id=uid,
            task=task,
            subtask=subtask,
            action=action,
            comment=comment
        )
    db.session.commit()

    return jsonify({'success': True, 'data': subtask.to_dict(), 'message': msg})


# ── 子任务跟进记录 ────────────────────────────────────────────

@subtask_bp.route('/api/subtask/<int:subtask_id>/updates', methods=['GET'])
@login_required
def list_updates(subtask_id):
    """获取子任务的所有跟进记录"""
    subtask = SubTask.query.get_or_404(subtask_id)
    task = Task.query.get_or_404(subtask.task_id)
    if not _can_access_task(task):
        return jsonify({'success': False, 'message': '无权访问'}), 403

    updates = SubTaskUpdate.query.filter_by(subtask_id=subtask_id, is_deleted=False)\
        .order_by(SubTaskUpdate.created_at.desc()).all()

    return jsonify({'success': True, 'data': [u.to_dict() for u in updates]})


@subtask_bp.route('/api/subtask/<int:subtask_id>/updates', methods=['POST'])
@login_required
def create_update(subtask_id):
    """添加子任务跟进"""
    subtask = SubTask.query.get_or_404(subtask_id)
    task = Task.query.get_or_404(subtask.task_id)
    if not _can_access_task(task):
        return jsonify({'success': False, 'message': '无权操作'}), 403

    # 支持 form data (含文件) 或 JSON
    content = request.form.get('content', '').strip() if request.content_type and 'multipart' in request.content_type else (request.get_json() or {}).get('content', '').strip()

    if not content:
        return jsonify({'success': False, 'message': '内容不能为空'}), 400

    update = SubTaskUpdate(
        subtask_id=subtask_id,
        author_id=current_user.id,
        content=content,
    )
    db.session.add(update)
    db.session.flush()

    # 处理附件
    files = request.files.getlist('files')
    if files:
        smart_storage = get_smart_storage()
        for f in files:
            if f.filename:
                result = smart_storage.upload_file(
                    object_id=subtask_id,
                    file=f,
                    filename=f.filename,
                    file_type='attachment',
                    bucket_type='task',
                    business_type='subtask'
                )
                if result.get('success'):
                    att = SubTaskAttachment(
                        update_id=update.id,
                        filename=f.filename,
                        storage_path=result['path'],
                        file_size=result.get('size', 0),
                        file_type=f.content_type,
                        uploaded_by=current_user.id,
                    )
                    db.session.add(att)

    # 自动将子任务状态从 pending 切为 in_progress
    if subtask.status == 'pending':
        subtask.status = 'in_progress'

    db.session.commit()

    # 通知任务相关人（排除自己）
    notify_ids = set()
    if task.creator_id:
        notify_ids.add(task.creator_id)
    if task.assignee_id:
        notify_ids.add(task.assignee_id)
    for uid in (task.shared_with_users or []):
        notify_ids.add(uid)
    notify_ids.discard(current_user.id)

    for uid in notify_ids:
        Message.create_subtask_update_notification(
            sender=current_user,
            recipient_id=uid,
            task=task,
            subtask=subtask,
            content_preview=content[:50]
        )
    db.session.commit()

    return jsonify({'success': True, 'data': update.to_dict(), 'message': '跟进已添加'})


@subtask_bp.route('/api/subtask/attachment/<int:att_id>/download', methods=['GET'])
@login_required
def download_attachment(att_id):
    """下载子任务附件"""
    att = SubTaskAttachment.query.get_or_404(att_id)
    update = SubTaskUpdate.query.get_or_404(att.update_id)
    subtask = SubTask.query.get_or_404(update.subtask_id)
    task = Task.query.get_or_404(subtask.task_id)

    if not _can_access_task(task):
        return jsonify({'success': False, 'message': '无权访问'}), 403

    smart_storage = get_smart_storage()
    return smart_storage.download_file(att.storage_path, att.filename, bucket_type='task')


# ── 工具函数 ──────────────────────────────────────────────────

def _parse_date(val):
    """解析日期字符串为 date 对象"""
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return datetime.fromisoformat(val.replace('Z', '+00:00')).date() if 'T' in val else date.fromisoformat(val)
    except (ValueError, AttributeError):
        return None
```

### Step 2: 注册 Blueprint

在 `app/__init__.py` 的 task_bp 注册位置（行 918 附近）之后添加：

```python
from app.views.subtask import subtask_bp
app.register_blueprint(subtask_bp)
```

### Step 3: 提交

```bash
git add app/views/subtask.py app/__init__.py
git commit -m "feat(task): add SubTask API with CRUD, milestone confirmation, progress updates"
```

---

## Task 3: Task API 扩展（可与 Task 2 并行）

**Files:**
- Modify: `app/views/task.py` — 扩展现有 API

### Step 1: 扩展 _can_access 权限检查

修改 `app/views/task.py:34-36` 的 `_can_access` 函数：

```python
def _can_access(task):
    """创建人、被指派人、协助人均可访问"""
    if current_user.id == task.creator_id or current_user.id == task.assignee_id:
        return True
    shared = task.shared_with_users or []
    return current_user.id in shared
```

### Step 2: 更新创建接口支持新字段

在 `app/views/task.py` 的创建路由（行 39-120）中，Task 对象构造区域添加：

```python
start_date=_parse_date(data.get('start_date')),
shared_with_users=data.get('shared_with_users', []),
task_type=data.get('task_type', 'general'),
```

（复用 subtask.py 中的 `_parse_date` 或在 task.py 中添加同样的工具函数）

同时给协助人发送通知：

```python
# 通知协助人
for uid in (task.shared_with_users or []):
    if uid != current_user.id:
        Message.create_task_shared(
            sender=current_user,
            recipient_id=uid,
            task=task
        )
```

### Step 3: 更新修改接口支持新字段

在 `app/views/task.py` 的 PUT 路由中添加对 `start_date`、`shared_with_users`、`task_type` 的处理。

### Step 4: 新增任务管理页面列表 API

在 `app/views/task.py` 中新增：

```python
@task.route('/management')
@login_required
def task_management():
    """任务管理页面"""
    return render_template('task/tw_task_management.html')


@task.route('/api/management/list', methods=['GET'])
@login_required
def management_list():
    """任务管理页面的任务列表 API，支持筛选和排序"""
    tab = request.args.get('tab', 'my')  # my / created / shared / all
    sort = request.args.get('sort', 'updated')  # updated / due_date / priority / created
    status = request.args.get('status', '')  # pending / in_progress / completed / cancelled / 空=全部
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    query = Task.query.filter(Task.is_deleted == False)

    # Tab 筛选
    if tab == 'my':
        query = query.filter(Task.assignee_id == current_user.id)
    elif tab == 'created':
        query = query.filter(Task.creator_id == current_user.id)
    elif tab == 'shared':
        query = query.filter(Task.shared_with_users.contains([current_user.id]))
    elif tab == 'all':
        # 我能看到的所有任务：我创建 + 我负责 + 我参与
        query = query.filter(
            db.or_(
                Task.creator_id == current_user.id,
                Task.assignee_id == current_user.id,
                Task.shared_with_users.contains([current_user.id])
            )
        )

    # 状态筛选
    if status:
        query = query.filter(Task.status == status)

    # 搜索
    if search:
        query = query.filter(Task.title.ilike(f'%{search}%'))

    # 排序
    if sort == 'updated':
        query = query.order_by(Task.updated_at.desc().nullslast())
    elif sort == 'due_date':
        query = query.order_by(Task.due_date.asc().nullslast())
    elif sort == 'priority':
        priority_order = db.case(
            (Task.priority == 'urgent', 1),
            (Task.priority == 'high', 2),
            (Task.priority == 'normal', 3),
            (Task.priority == 'low', 4),
            else_=5
        )
        query = query.order_by(priority_order)
    elif sort == 'created':
        query = query.order_by(Task.created_at.desc())

    tasks = query.limit(per_page).offset((page - 1) * per_page).all()
    total = query.count()

    return jsonify({
        'success': True,
        'data': [t.to_dict() for t in tasks],
        'total': total,
        'page': page,
        'per_page': per_page,
    })
```

### Step 5: 提交

```bash
git add app/views/task.py
git commit -m "feat(task): extend Task API with shared_users, start_date, management list endpoint"
```

---

## Task 4: 通知系统扩展

**Files:**
- Modify: `app/models/message.py` — 新增 4 个通知方法

### Step 1: 在 Message 类中添加新的通知方法

在 `app/models/message.py` 的 `create_task_completed` 方法（行 720）之后添加：

```python
@staticmethod
def create_task_shared(sender, recipient_id, task):
    """任务协助人通知"""
    msg = Message(
        sender_id=sender.id,
        recipient_id=recipient_id,
        message_type='task_shared',
        related_object_type='task',
        related_object_id=task.id,
        content=f'{sender.real_name or sender.username} 邀请你协助任务「{task.title}」',
        extra_data={'task_id': task.id, 'title': task.title}
    )
    db.session.add(msg)

@staticmethod
def create_subtask_assigned(sender, recipient_id, task, subtask):
    """子任务分配通知"""
    msg = Message(
        sender_id=sender.id,
        recipient_id=recipient_id,
        message_type='subtask_assigned',
        related_object_type='task',
        related_object_id=task.id,
        content=f'{sender.real_name or sender.username} 分配了子任务「{subtask.title}」给你',
        extra_data={'task_id': task.id, 'subtask_id': subtask.id, 'title': subtask.title}
    )
    db.session.add(msg)

@staticmethod
def create_subtask_completed(sender, recipient_id, task, subtask):
    """子任务完成通知"""
    msg = Message(
        sender_id=sender.id,
        recipient_id=recipient_id,
        message_type='subtask_completed',
        related_object_type='task',
        related_object_id=task.id,
        content=f'{sender.real_name or sender.username} 完成了子任务「{subtask.title}」',
        extra_data={'task_id': task.id, 'subtask_id': subtask.id, 'title': subtask.title}
    )
    db.session.add(msg)

@staticmethod
def create_milestone_confirmation_request(sender, recipient_id, task, subtask):
    """里程碑确认请求通知"""
    msg = Message(
        sender_id=sender.id,
        recipient_id=recipient_id,
        message_type='milestone_confirmation',
        related_object_type='task',
        related_object_id=task.id,
        content=f'🏁 {sender.real_name or sender.username} 请求你确认里程碑「{subtask.title}」',
        extra_data={
            'task_id': task.id,
            'subtask_id': subtask.id,
            'title': subtask.title,
            'action_required': True,
        }
    )
    db.session.add(msg)

@staticmethod
def create_milestone_result(sender, recipient_id, task, subtask, action, comment=''):
    """里程碑确认/驳回结果通知"""
    action_text = '确认通过' if action == 'confirm' else '驳回'
    emoji = '✅' if action == 'confirm' else '⚠️'
    msg = Message(
        sender_id=sender.id,
        recipient_id=recipient_id,
        message_type='milestone_result',
        related_object_type='task',
        related_object_id=task.id,
        content=f'{emoji} {sender.real_name or sender.username} {action_text}了里程碑「{subtask.title}」' + (f'：{comment[:50]}' if comment else ''),
        extra_data={
            'task_id': task.id,
            'subtask_id': subtask.id,
            'title': subtask.title,
            'action': action,
            'comment': comment,
        }
    )
    db.session.add(msg)

@staticmethod
def create_subtask_update_notification(sender, recipient_id, task, subtask, content_preview=''):
    """子任务跟进更新通知"""
    msg = Message(
        sender_id=sender.id,
        recipient_id=recipient_id,
        message_type='subtask_update',
        related_object_type='task',
        related_object_id=task.id,
        content=f'{sender.real_name or sender.username} 更新了「{subtask.title}」: {content_preview}',
        extra_data={
            'task_id': task.id,
            'subtask_id': subtask.id,
            'title': subtask.title,
        }
    )
    db.session.add(msg)
```

### Step 2: 提交

```bash
git add app/models/message.py
git commit -m "feat(task): add notification methods for subtask, milestone, and shared users"
```

---

## Task 5: 前端页面 — 任务管理中心

**Files:**
- Create: `app/templates/task/tw_task_management.html` — 主页面（左列表+右详情）
- Create: `app/static/js/task-management.js` — 页面逻辑（Alpine.js 组件）
- Modify: `app/templates/components/tw_task_modal.html` — 扩展创建弹窗支持新字段

**布局参考:** `app/templates/knowledge/tw_wiki.html:74-294`

### Step 1: 创建主页面模板

创建 `app/templates/task/tw_task_management.html`，采用分栏布局：

```html
{% extends "components/tw_fixed_header_page.html" %}
{% block title %}{{ _('任务中心') }}{% endblock %}

{% block head_extra %}
<style>
  /* 分栏布局：左列表+右详情 */
  .task-panel { height: calc(100vh - 56px); }
  .task-list-panel { width: 380px; min-width: 320px; }
  .task-detail-panel { flex: 1; }

  @media (max-width: 768px) {
    .task-list-panel { width: 100%; }
    .task-detail-panel { display: none; }
    .task-detail-panel.active { display: flex; width: 100%; }
    .task-list-panel.hidden-mobile { display: none; }
  }
</style>
{% endblock %}

{% block content %}
<div x-data="taskManagement()" x-init="init()" class="task-panel flex overflow-hidden">

  <!-- ═══ 左侧：任务列表 ═══ -->
  <aside class="task-list-panel flex-shrink-0 border-r border-gray-200 dark:border-gray-700 flex flex-col bg-white dark:bg-gray-900"
         :class="{ 'hidden-mobile': selectedTask }">

    <!-- 顶部操作栏 -->
    <div class="p-3 border-b border-gray-200 dark:border-gray-700 space-y-2">
      <!-- 搜索 -->
      <div class="relative">
        <input type="text" x-model="search" @input.debounce.300ms="loadTasks()"
               :placeholder="_t('搜索任务...')"
               class="w-full pl-8 pr-3 py-1.5 text-sm border rounded-lg dark:bg-gray-800 dark:border-gray-600">
        <svg class="absolute left-2.5 top-2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
      </div>

      <!-- Tab 切换 -->
      <div class="flex text-xs space-x-1">
        <template x-for="t in tabs">
          <button @click="tab = t.key; loadTasks()"
                  :class="tab === t.key ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'"
                  class="px-2 py-1 rounded-md transition" x-text="t.label"></button>
        </template>
      </div>

      <!-- 排序 -->
      <div class="flex items-center justify-between text-xs text-gray-500">
        <select x-model="sort" @change="loadTasks()"
                class="text-xs border-0 bg-transparent focus:ring-0 py-0">
          <option value="updated">最近更新</option>
          <option value="due_date">截止日期</option>
          <option value="priority">优先级</option>
          <option value="created">创建时间</option>
        </select>
        <span x-text="'共 ' + totalTasks + ' 个'" class="text-gray-400"></span>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="flex-1 overflow-y-auto">
      <template x-for="task in tasks" :key="task.id">
        <div @click="selectTask(task.id)"
             :class="selectedTaskId === task.id ? 'bg-blue-50 border-l-2 border-l-blue-500 dark:bg-blue-900/20' : 'border-l-2 border-l-transparent hover:bg-gray-50 dark:hover:bg-gray-800'"
             class="p-3 border-b border-gray-100 dark:border-gray-800 cursor-pointer transition">

          <!-- 第一行：优先级 + 标题 -->
          <div class="flex items-start gap-2">
            <span :class="priorityDotClass(task.priority)" class="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"></span>
            <span class="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-2" x-text="task.title"></span>
          </div>

          <!-- 第二行：负责人 + 协助人数 + 进度 -->
          <div class="flex items-center justify-between mt-1.5 text-xs text-gray-500">
            <div class="flex items-center gap-1">
              <span x-text="task.assignee_name || '未分配'"></span>
              <template x-if="task.shared_with_users && task.shared_with_users.length > 0">
                <span class="text-gray-400" x-text="'+' + task.shared_with_users.length + '人'"></span>
              </template>
            </div>
            <span :class="statusClass(task.status)" class="px-1.5 py-0.5 rounded text-[10px]" x-text="statusText(task.status)"></span>
          </div>

          <!-- 第三行：子任务进度条 + 截止日期 -->
          <div class="flex items-center justify-between mt-1.5">
            <div class="flex items-center gap-1.5 text-[10px] text-gray-400">
              <template x-if="task.subtask_count > 0">
                <div class="flex items-center gap-1">
                  <div class="w-16 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div :style="'width:' + (task.subtask_completed / task.subtask_count * 100) + '%'"
                         class="h-full bg-blue-500 rounded-full"></div>
                  </div>
                  <span x-text="task.subtask_completed + '/' + task.subtask_count"></span>
                </div>
              </template>
              <template x-if="task.milestone_count > 0">
                <span class="text-amber-500" x-text="'🏁' + task.milestone_confirmed + '/' + task.milestone_count"></span>
              </template>
            </div>
            <span x-text="formatDate(task.due_date)" class="text-[10px] text-gray-400"
                  :class="isOverdue(task) && 'text-red-500 font-medium'"></span>
          </div>
        </div>
      </template>

      <!-- 空状态 -->
      <template x-if="tasks.length === 0 && !loading">
        <div class="p-8 text-center text-gray-400 text-sm">暂无任务</div>
      </template>
    </div>
  </aside>

  <!-- ═══ 右侧：任务详情 ═══ -->
  <main class="task-detail-panel flex flex-col overflow-hidden bg-gray-50 dark:bg-gray-950"
        :class="{ 'active': selectedTask }">

    <!-- 未选中态 -->
    <template x-if="!selectedTask">
      <div class="flex-1 flex items-center justify-center text-gray-400">
        <div class="text-center">
          <svg class="mx-auto w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
          <p>选择一个任务查看详情</p>
          <button @click="openCreateModal()" class="mt-4 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">
            + 新建任务
          </button>
        </div>
      </div>
    </template>

    <!-- 选中态：详情内容 -->
    <template x-if="selectedTask">
      <div class="flex-1 overflow-y-auto">

        <!-- 头部信息 -->
        <div class="p-4 bg-white dark:bg-gray-900 border-b dark:border-gray-700">
          <!-- 移动端返回 -->
          <button @click="selectedTask = null; selectedTaskId = null"
                  class="md:hidden mb-2 text-sm text-blue-600">← 返回列表</button>

          <div class="flex items-start justify-between">
            <div class="flex-1">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white" x-text="selectedTask.title"></h2>
              <div class="flex items-center gap-2 mt-1">
                <span :class="priorityBadgeClass(selectedTask.priority)"
                      class="px-2 py-0.5 rounded text-xs" x-text="priorityText(selectedTask.priority)"></span>
                <span :class="statusBadgeClass(selectedTask.status)"
                      class="px-2 py-0.5 rounded text-xs" x-text="statusText(selectedTask.status)"></span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button @click="openEditModal()" class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500" title="编辑">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
              </button>
              <div x-data="{ menuOpen: false }" class="relative">
                <button @click="menuOpen = !menuOpen" class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 6a2 2 0 110-4 2 2 0 010 4zm0 6a2 2 0 110-4 2 2 0 010 4zm0 6a2 2 0 110-4 2 2 0 010 4z"/></svg>
                </button>
                <div x-show="menuOpen" @click.away="menuOpen = false"
                     class="absolute right-0 mt-1 w-36 bg-white dark:bg-gray-800 rounded-lg shadow-lg border dark:border-gray-700 py-1 z-10">
                  <button @click="completeTask(); menuOpen = false"
                          class="w-full text-left px-3 py-1.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-700">✓ 完成任务</button>
                  <button @click="cancelTask(); menuOpen = false"
                          class="w-full text-left px-3 py-1.5 text-sm text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700">✕ 取消任务</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 基本信息网格 -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 text-sm">
            <div>
              <span class="text-gray-500 text-xs">创建人</span>
              <p class="text-gray-900 dark:text-gray-100" x-text="selectedTask.creator_name"></p>
            </div>
            <div>
              <span class="text-gray-500 text-xs">负责人</span>
              <p class="text-gray-900 dark:text-gray-100" x-text="selectedTask.assignee_name || '未分配'"></p>
            </div>
            <div>
              <span class="text-gray-500 text-xs">开始</span>
              <p class="text-gray-900 dark:text-gray-100" x-text="formatDate(selectedTask.start_date) || '-'"></p>
            </div>
            <div>
              <span class="text-gray-500 text-xs">截止</span>
              <p :class="isOverdue(selectedTask) && 'text-red-500 font-medium'" x-text="formatDate(selectedTask.due_date) || '-'"></p>
            </div>
          </div>

          <!-- 协助人 -->
          <template x-if="sharedUserNames && sharedUserNames.length > 0">
            <div class="mt-2 text-sm">
              <span class="text-gray-500 text-xs">协助人</span>
              <p class="text-gray-900 dark:text-gray-100" x-text="sharedUserNames.join('、')"></p>
            </div>
          </template>

          <!-- 描述 -->
          <template x-if="selectedTask.description">
            <div class="mt-3 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800 rounded-lg p-3"
                 x-text="selectedTask.description"></div>
          </template>
        </div>

        <!-- ── 子任务区域 ── -->
        <div class="p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300">
              子任务
              <template x-if="subtasks.length > 0">
                <span class="text-gray-400 font-normal"
                      x-text="'(' + subtasks.filter(s => s.status === \'completed\').length + '/' + subtasks.length + ')'"></span>
              </template>
            </h3>
            <button @click="openSubtaskModal()"
                    class="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
              新增子任务
            </button>
          </div>

          <!-- 子任务列表 -->
          <div class="space-y-2">
            <template x-for="st in subtasks" :key="st.id">
              <div class="bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-700 overflow-hidden">
                <!-- 子任务头部行 -->
                <div @click="toggleSubtask(st.id)"
                     class="flex items-center gap-2 p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition">
                  <!-- 状态图标 -->
                  <span x-html="subtaskStatusIcon(st)"></span>
                  <!-- 标题 -->
                  <span class="flex-1 text-sm" :class="st.status === 'completed' ? 'line-through text-gray-400' : 'text-gray-900 dark:text-gray-100'"
                        x-text="st.title"></span>
                  <!-- 里程碑标记 -->
                  <template x-if="st.is_milestone">
                    <span class="text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300">🏁 里程碑</span>
                  </template>
                  <!-- 负责人 -->
                  <span class="text-xs text-gray-400" x-text="st.assignee_name || ''"></span>
                  <!-- 日期 -->
                  <span class="text-xs text-gray-400" x-text="formatDateRange(st.start_date, st.due_date)"></span>
                  <!-- 跟进数 -->
                  <span class="text-xs text-gray-400" x-text="st.update_count > 0 ? st.update_count + '条' : ''"></span>
                  <!-- 展开箭头 -->
                  <svg :class="expandedSubtasks.includes(st.id) && 'rotate-180'" class="w-4 h-4 text-gray-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                  </svg>
                </div>

                <!-- 展开的子任务详情 -->
                <div x-show="expandedSubtasks.includes(st.id)" x-collapse class="border-t dark:border-gray-700">
                  <!-- 操作按钮 -->
                  <div class="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800 text-xs">
                    <template x-if="st.status === 'pending'">
                      <button @click.stop="startSubtask(st.id)" class="text-blue-600 hover:underline">开始</button>
                    </template>
                    <template x-if="st.status === 'in_progress' || st.status === 'delayed'">
                      <button @click.stop="completeSubtask(st.id)" class="text-green-600 hover:underline"
                              x-text="st.is_milestone ? '提交确认' : '完成'"></button>
                    </template>
                    <template x-if="st.is_milestone && st.milestone_status === 'pending_confirmation' && currentUserId == st.milestone_confirmer_id">
                      <div class="flex gap-2">
                        <button @click.stop="openMilestoneConfirmModal(st)" class="text-green-600 hover:underline">✅ 确认</button>
                        <button @click.stop="openMilestoneRejectModal(st)" class="text-red-600 hover:underline">❌ 驳回</button>
                      </div>
                    </template>
                    <button @click.stop="openSubtaskModal(st)" class="text-gray-500 hover:underline">编辑</button>
                    <button @click.stop="deleteSubtask(st.id)" class="text-red-500 hover:underline">删除</button>

                    <!-- 里程碑状态 -->
                    <template x-if="st.is_milestone && st.milestone_status">
                      <span :class="{
                        'text-amber-600': st.milestone_status === 'pending_confirmation',
                        'text-green-600': st.milestone_status === 'confirmed',
                        'text-red-600': st.milestone_status === 'rejected'
                      }" x-text="milestoneStatusText(st)"></span>
                    </template>
                  </div>

                  <!-- 跟进记录 -->
                  <div class="px-3 py-2 space-y-2 max-h-60 overflow-y-auto">
                    <template x-for="upd in (subtaskUpdates[st.id] || [])" :key="upd.id">
                      <div class="text-sm border-l-2 border-gray-200 dark:border-gray-600 pl-3 py-1">
                        <div class="flex items-center gap-2 text-xs text-gray-500">
                          <span class="font-medium text-gray-700 dark:text-gray-300" x-text="upd.author_name"></span>
                          <span x-text="formatDateTime(upd.created_at)"></span>
                        </div>
                        <p class="text-gray-800 dark:text-gray-200 mt-0.5" x-text="upd.content"></p>
                        <template x-if="upd.attachments && upd.attachments.length > 0">
                          <div class="flex flex-wrap gap-1 mt-1">
                            <template x-for="att in upd.attachments" :key="att.id">
                              <a :href="'/subtask/api/subtask/attachment/' + att.id + '/download'"
                                 class="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline bg-blue-50 dark:bg-blue-900/30 px-2 py-0.5 rounded">
                                📎 <span x-text="att.filename"></span>
                              </a>
                            </template>
                          </div>
                        </template>
                      </div>
                    </template>
                  </div>

                  <!-- 添加跟进输入框 -->
                  <div class="px-3 py-2 border-t dark:border-gray-700">
                    <div class="flex gap-2">
                      <input type="text" x-model="newUpdateContent[st.id]"
                             @keydown.enter="addUpdate(st.id)"
                             placeholder="输入跟进内容..."
                             class="flex-1 text-sm border rounded-lg px-3 py-1.5 dark:bg-gray-800 dark:border-gray-600">
                      <label class="cursor-pointer p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500">
                        📎
                        <input type="file" multiple class="hidden" @change="handleUpdateFiles($event, st.id)">
                      </label>
                      <button @click="addUpdate(st.id)"
                              class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">发送</button>
                    </div>
                    <!-- 待上传文件列表 -->
                    <template x-if="pendingUpdateFiles[st.id] && pendingUpdateFiles[st.id].length > 0">
                      <div class="flex flex-wrap gap-1 mt-1">
                        <template x-for="(f, idx) in pendingUpdateFiles[st.id]" :key="idx">
                          <span class="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded flex items-center gap-1">
                            <span x-text="f.name"></span>
                            <button @click="pendingUpdateFiles[st.id].splice(idx, 1)" class="text-red-400 hover:text-red-600">×</button>
                          </span>
                        </template>
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- 无子任务 -->
          <template x-if="subtasks.length === 0">
            <div class="text-center text-gray-400 text-sm py-8 bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-700">
              <p>暂无子任务</p>
              <button @click="openSubtaskModal()"
                      class="mt-2 text-blue-600 hover:underline text-xs">+ 新增子任务</button>
            </div>
          </template>
        </div>

        <!-- ── 时间线(简化版 - 子任务甘特条) ── -->
        <template x-if="subtasks.length > 0 && subtasks.some(s => s.start_date || s.due_date)">
          <div class="px-4 pb-4">
            <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">时间线</h3>
            <div class="bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-700 p-3 overflow-x-auto"
                 x-html="renderTimeline()"></div>
          </div>
        </template>

        <!-- ── 任务讨论区 ── -->
        <div class="px-4 pb-4">
          <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            讨论
            <span class="text-gray-400 font-normal" x-text="'(' + (taskReplies || []).length + ')'"></span>
          </h3>
          <div class="bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-700">
            <!-- 讨论列表 -->
            <div class="max-h-60 overflow-y-auto p-3 space-y-2">
              <template x-for="reply in taskReplies" :key="reply.id">
                <div class="text-sm">
                  <span class="font-medium text-gray-700 dark:text-gray-300" x-text="reply.author_name"></span>
                  <span class="text-xs text-gray-400 ml-1" x-text="formatDateTime(reply.created_at)"></span>
                  <p class="text-gray-800 dark:text-gray-200 mt-0.5" x-text="reply.content"></p>
                </div>
              </template>
              <template x-if="!taskReplies || taskReplies.length === 0">
                <p class="text-gray-400 text-xs text-center py-2">暂无讨论</p>
              </template>
            </div>
            <!-- 输入框 -->
            <div class="border-t dark:border-gray-700 p-3 flex gap-2">
              <input type="text" x-model="newReplyContent"
                     @keydown.enter="addReply()"
                     placeholder="输入讨论内容..."
                     class="flex-1 text-sm border rounded-lg px-3 py-1.5 dark:bg-gray-800 dark:border-gray-600">
              <button @click="addReply()"
                      class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">发送</button>
            </div>
          </div>
        </div>

      </div>
    </template>
  </main>
</div>

<!-- ═══ 弹窗区域 ═══ -->

<!-- 1. 新建/编辑任务弹窗（复用现有 tw_task_modal 或新建） -->
<!-- 参见 Step 2 的弹窗组件 -->

<!-- 2. 新建/编辑子任务弹窗 -->
<div x-show="showSubtaskModal" x-cloak
     class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
     @click.self="showSubtaskModal = false">
  <div class="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-md mx-4 p-5">
    <h3 class="text-lg font-semibold mb-4" x-text="editingSubtask ? '编辑子任务' : '新建子任务'"></h3>
    <div class="space-y-3">
      <div>
        <label class="text-sm text-gray-600 dark:text-gray-400">标题 *</label>
        <input type="text" x-model="subtaskForm.title"
               class="w-full mt-1 border rounded-lg px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-600">
      </div>
      <div>
        <label class="text-sm text-gray-600 dark:text-gray-400">描述</label>
        <textarea x-model="subtaskForm.description" rows="2"
                  class="w-full mt-1 border rounded-lg px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-600"></textarea>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-sm text-gray-600 dark:text-gray-400">负责人</label>
          <!-- 用户搜索下拉（复用现有模式） -->
          <select x-model="subtaskForm.assignee_id"
                  class="w-full mt-1 border rounded-lg px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-600">
            <option value="">未分配</option>
            <template x-for="u in allUsers" :key="u.id">
              <option :value="u.id" x-text="u.real_name || u.username"></option>
            </template>
          </select>
        </div>
        <div>
          <label class="text-sm text-gray-600 dark:text-gray-400">
            <input type="checkbox" x-model="subtaskForm.is_milestone" class="mr-1"> 设为里程碑
          </label>
          <template x-if="subtaskForm.is_milestone">
            <select x-model="subtaskForm.milestone_confirmer_id"
                    class="w-full mt-1 border rounded-lg px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-600">
              <option value="">选择确认人</option>
              <template x-for="u in allUsers" :key="u.id">
                <option :value="u.id" x-text="u.real_name || u.username"></option>
              </template>
            </select>
          </template>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-sm text-gray-600 dark:text-gray-400">开始日期</label>
          <input type="date" x-model="subtaskForm.start_date"
                 class="w-full mt-1 border rounded-lg px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-600">
        </div>
        <div>
          <label class="text-sm text-gray-600 dark:text-gray-400">结束日期</label>
          <input type="date" x-model="subtaskForm.due_date"
                 class="w-full mt-1 border rounded-lg px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-600">
        </div>
      </div>
    </div>
    <div class="flex justify-end gap-2 mt-5">
      <button @click="showSubtaskModal = false" class="px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">取消</button>
      <button @click="saveSubtask()" class="px-4 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700">保存</button>
    </div>
  </div>
</div>

<!-- 3. 里程碑确认弹窗 -->
<div x-show="showMilestoneModal" x-cloak
     class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
     @click.self="showMilestoneModal = false">
  <div class="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-sm mx-4 p-5">
    <h3 class="text-lg font-semibold mb-2" x-text="milestoneAction === 'confirm' ? '确认里程碑' : '驳回里程碑'"></h3>
    <p class="text-sm text-gray-600 mb-3" x-text="'子任务：' + (milestoneTarget?.title || '')"></p>
    <textarea x-model="milestoneComment" rows="3" placeholder="输入意见（可选）..."
              class="w-full border rounded-lg px-3 py-1.5 text-sm dark:bg-gray-800 dark:border-gray-600"></textarea>
    <div class="flex justify-end gap-2 mt-4">
      <button @click="showMilestoneModal = false" class="px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">取消</button>
      <button @click="submitMilestoneDecision()"
              :class="milestoneAction === 'confirm' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'"
              class="px-4 py-1.5 text-sm text-white rounded-lg" x-text="milestoneAction === 'confirm' ? '确认通过' : '驳回'"></button>
    </div>
  </div>
</div>

{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/task-management.js') }}"></script>
{% endblock %}
```

注意：以上模板为核心结构框架，实际实现时需根据项目现有 Tailwind 组件模式调整（如使用 `tw_fixed_header_page.html` 基础模板、暗色模式 class 等）。

### Step 2: 创建 JavaScript 逻辑文件

创建 `app/static/js/task-management.js`，包含 Alpine.js 组件 `taskManagement()`：

核心数据结构：
```javascript
function taskManagement() {
  return {
    // 列表状态
    tasks: [],
    totalTasks: 0,
    loading: false,
    tab: 'all',
    sort: 'updated',
    search: '',
    tabs: [
      { key: 'all', label: '全部' },
      { key: 'my', label: '我负责的' },
      { key: 'created', label: '我创建的' },
      { key: 'shared', label: '我参与的' },
    ],

    // 详情状态
    selectedTaskId: null,
    selectedTask: null,
    subtasks: [],
    subtaskUpdates: {},  // { subtaskId: [updates] }
    expandedSubtasks: [],
    taskReplies: [],
    sharedUserNames: [],

    // 子任务跟进
    newUpdateContent: {},
    pendingUpdateFiles: {},
    newReplyContent: '',

    // 弹窗状态
    showSubtaskModal: false,
    editingSubtask: null,
    subtaskForm: { title: '', description: '', assignee_id: '', start_date: '', due_date: '', is_milestone: false, milestone_confirmer_id: '' },
    showMilestoneModal: false,
    milestoneTarget: null,
    milestoneAction: '',
    milestoneComment: '',

    // 用户列表
    allUsers: [],
    currentUserId: null,  // 从模板传入

    async init() {
      this.currentUserId = window.CURRENT_USER_ID;
      await this.loadUsers();
      await this.loadTasks();
    },

    // ── API 调用方法 ──
    async loadTasks() { /* GET /task/api/management/list?tab=&sort=&search= */ },
    async selectTask(taskId) { /* GET /task/api/<id> + GET /subtask/api/task/<id>/subtasks */ },
    async loadSubtaskUpdates(subtaskId) { /* GET /subtask/api/subtask/<id>/updates */ },
    async saveSubtask() { /* POST/PUT subtask */ },
    async deleteSubtask(id) { /* DELETE subtask */ },
    async startSubtask(id) { /* POST start */ },
    async completeSubtask(id) { /* POST complete */ },
    async submitMilestoneDecision() { /* POST milestone confirm/reject */ },
    async addUpdate(subtaskId) { /* POST update with files */ },
    async addReply() { /* POST /task/api/<id>/replies */ },
    async completeTask() { /* POST /task/api/<id>/complete */ },
    async cancelTask() { /* POST /task/api/<id>/cancel */ },
    async loadUsers() { /* GET /user/api/users/active */ },

    // ── UI 辅助方法 ──
    toggleSubtask(id) { /* 展开/收起子任务 */ },
    priorityDotClass(p) { /* 优先级圆点颜色 */ },
    priorityBadgeClass(p) { /* 优先级徽章 */ },
    priorityText(p) { /* 优先级文本 */ },
    statusClass(s) { /* 状态样式 */ },
    statusText(s) { /* 状态文本 */ },
    statusBadgeClass(s) { /* 状态徽章 */ },
    subtaskStatusIcon(st) { /* 子任务状态图标 */ },
    milestoneStatusText(st) { /* 里程碑状态文本 */ },
    formatDate(d) { /* 日期格式化 */ },
    formatDateTime(dt) { /* 日期时间格式化 */ },
    formatDateRange(s, e) { /* 日期范围 */ },
    isOverdue(task) { /* 是否逾期 */ },
    renderTimeline() { /* 渲染简易时间线 HTML */ },

    // ── 弹窗方法 ──
    openCreateModal() { /* 打开新建任务弹窗 */ },
    openEditModal() { /* 打开编辑任务弹窗 */ },
    openSubtaskModal(st = null) { /* 打开子任务弹窗 */ },
    openMilestoneConfirmModal(st) { /* 打开里程碑确认弹窗 */ },
    openMilestoneRejectModal(st) { /* 打开里程碑驳回弹窗 */ },
    handleUpdateFiles(event, subtaskId) { /* 处理文件选择 */ },
  }
}
```

注意：以上为数据结构和方法签名，实际实现时每个方法需完整的 fetch 调用、错误处理、状态更新逻辑。参考 `tw_task_modal.html:374-` 中现有的 Alpine.js 模式。

### Step 3: 扩展创建任务弹窗

修改 `app/templates/components/tw_task_modal.html` 中的 `render_task_create_modal` 宏，在表单中添加：
- `start_date` 日期选择器（与 due_date 并排）
- `shared_with_users` 多选用户组件
- `task_type` 类型选择下拉

### Step 4: 添加导航入口

在导航菜单中添加"任务中心"链接，指向 `/task/management`。

### Step 5: 提交

```bash
git add app/templates/task/ app/static/js/task-management.js app/templates/components/tw_task_modal.html
git commit -m "feat(task): add task management page with split-panel layout, subtask UI, milestone confirmation"
```

---

## Task 6: 翻译与收尾

**Files:**
- Modify: `app/translations/en/LC_MESSAGES/messages.po`
- Modify: `app/templates/` 导航菜单

### Step 1: 添加翻译条目

需要翻译的中文 msgid：
```
任务中心, 子任务, 里程碑, 确认人, 协助人, 开始日期, 截止日期,
新建子任务, 编辑子任务, 跟进记录, 添加跟进, 输入跟进内容,
里程碑确认, 确认通过, 驳回, 等待确认, 已确认, 已驳回,
待处理, 进行中, 已完成, 已延迟, 已取消,
我负责的, 我创建的, 我参与的, 全部,
最近更新, 截止日期, 优先级, 创建时间,
选择一个任务查看详情, 暂无任务, 暂无子任务, 暂无讨论,
提交确认, 节点标记为延迟
```

### Step 2: 编译翻译

```bash
pybabel compile -d app/translations
```

### Step 3: 最终提交

```bash
git add app/translations/
git commit -m "feat(task): add i18n translations for task management system"
```

---

## API 端点汇总

### 现有端点（扩展）

| 方法 | 路径 | 功能 | 变更 |
|------|------|------|------|
| GET | `/task/management` | 任务管理页面 | 新增 |
| GET | `/task/api/management/list` | 管理列表（筛选+排序） | 新增 |
| POST | `/task/api/create` | 创建任务 | 扩展 start_date/shared_with_users |
| PUT | `/task/api/<id>` | 更新任务 | 扩展新字段 |

### 新增端点（subtask blueprint）

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/subtask/api/task/<id>/subtasks` | 获取子任务列表 |
| POST | `/subtask/api/task/<id>/subtasks` | 创建子任务 |
| PUT | `/subtask/api/subtask/<id>` | 更新子任务 |
| DELETE | `/subtask/api/subtask/<id>` | 删除子任务 |
| POST | `/subtask/api/subtask/<id>/start` | 开始子任务 |
| POST | `/subtask/api/subtask/<id>/complete` | 完成/提交确认 |
| POST | `/subtask/api/subtask/<id>/milestone/confirm` | 里程碑确认/驳回 |
| GET | `/subtask/api/subtask/<id>/updates` | 获取跟进记录 |
| POST | `/subtask/api/subtask/<id>/updates` | 添加跟进（含附件） |
| GET | `/subtask/api/subtask/attachment/<id>/download` | 下载附件 |

---

## 新增数据表汇总

| 表名 | 核心字段 | 关系 |
|------|---------|------|
| `subtasks` | task_id, title, assignee_id, start_date, due_date, status, is_milestone, milestone_confirmer_id, milestone_status | → tasks, → users |
| `subtask_updates` | subtask_id, author_id, content | → subtasks, → users |
| `subtask_attachments` | update_id, filename, storage_path, file_size, uploaded_by | → subtask_updates, → users |

现有 `tasks` 表新增：`start_date`, `shared_with_users`, `task_type`

---

## 通知类型汇总

| message_type | 触发时机 | 接收人 |
|---|---|---|
| `task_shared` | 任务添加协助人 | 协助人 |
| `subtask_assigned` | 子任务分配 | 子任务负责人 |
| `subtask_completed` | 子任务完成 | 任务创建人 |
| `milestone_confirmation` | 提交里程碑确认 | 确认人 |
| `milestone_result` | 里程碑确认/驳回 | 任务负责人+创建人+子任务负责人 |
| `subtask_update` | 子任务新增跟进 | 任务相关人 |
