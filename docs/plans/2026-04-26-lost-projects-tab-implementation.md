# 流失项目标签 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在市场情报库新增"流失项目"标签，把已流失的正式项目（含负责人离职 / 无负责人）暴露给其他销售/代理商，支持公开详情页 + AI 调研补全 + 申请参与发待办。

**Architecture:**
- 数据源：实时查 `projects` 表（`activity_status='churned'`）。活跃度计算新增"负责人离职/无负责人"规则。
- AI 调研补全：复用 `prospect_projects` 表，加 `link_type` 区分语义；不修改 `projects` 表。
- 申请参与：极简通知机制 — 创建 `prospect_claim_requests` 记录 + 发 Message 到原负责人待办，原负责人线下处理。

**Tech Stack:**
- Flask + SQLAlchemy + Alembic
- Tailwind 模板（`tw_*.html` 体系）
- 现有 Message / can_view_project / activity_tracker 机制

**关联设计文档：** [`2026-04-26-lost-projects-tab-design.md`](./2026-04-26-lost-projects-tab-design.md)

**重要前置约束**：
- 本地环境跑 Flask 命令必须前缀 `export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && ` 否则 WeasyPrint 加载失败
- Project 模型字段是 `current_stage`（不是 `stage`），`FROZEN_STAGES = ['signed', 'lost', 'paused']`
- `can_view_project` 在 `app/utils/access_control.py:1746`
- 测试以独立 Python 脚本形式（PMA 现有 `tests/` 目录的惯例），通过 `app.test_client()` 或直接 db session 验证

---

## Phase 1: 数据模型与迁移

### Task 1.1：在 ProspectProject 模型加 link_type 字段

**Files:**
- Modify: `app/models/prospect_project.py:42` (在 `source` 字段后插入)

**Step 1: 修改模型**

在 `class ProspectProject` 中，找到 `source = Column(String(20), nullable=True)` 这一行，**之后**插入：

```python
    # link_type: 标识 prospect 与 project 的关联语义
    #   'converted' = 该线索已转化为 converted_project_id 指向的项目（原用法）
    #   'research'  = 该记录是为已存在项目反向调研产生的补全数据
    link_type = Column(String(20), nullable=False, default='converted',
                       server_default='converted', index=True)
```

**Step 2: 生成 migration**

运行：
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  flask db migrate -m "add link_type to prospect_projects, add prospect_claim_requests"
```

期望输出：生成 `migrations/versions/<hash>_add_link_type_*.py`

**Step 3: 检查并补全 migration**

打开新生成的 migration 文件，确认 `upgrade()` 包含：

```python
op.add_column('prospect_projects',
    sa.Column('link_type', sa.String(length=20), nullable=False,
              server_default='converted'))
op.create_index('ix_prospect_projects_link_type', 'prospect_projects', ['link_type'])
```

若 alembic 没自动生成 index 创建语句，手动加上。

### Task 1.2：创建 ProspectClaimRequest 模型

**Files:**
- Create: `app/models/prospect_claim_request.py`

**Step 1: 写文件**

```python
from app import db
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, DateTime, ForeignKey,
                        UniqueConstraint, Index)
from sqlalchemy.orm import relationship


class ProspectClaimRequest(db.Model):
    """申请参与流失项目的记录。

    业务约束：同一申请人对同一项目永久去重（uniqueness on (project_id, applicant_id)）。
    系统不维护审批结果，原负责人收到 Message 后线下处理。
    """
    __tablename__ = 'prospect_claim_requests'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    project = relationship('Project', foreign_keys=[project_id])
    applicant = relationship('User', foreign_keys=[applicant_id])

    __table_args__ = (
        UniqueConstraint('project_id', 'applicant_id',
                         name='uq_claim_project_applicant'),
        Index('ix_claim_project', 'project_id'),
        Index('ix_claim_applicant', 'applicant_id'),
    )
```

### Task 1.3：注册新模型

**Files:**
- Modify: `app/models/__init__.py`

**Step 1: 添加 import**

在文件末尾的 import 区段，按字母顺序找到合适位置插入：

```python
from app.models.prospect_claim_request import ProspectClaimRequest
```

**Step 2: 重新生成 migration（合并表创建）**

如果 Task 1.1 的 migration 已生成但只含 link_type，需重新生成包含新表的 migration：

```bash
# 先回退 Task 1.1 的 migration 文件（如果想合并）
# 或保留并新生成一个 migration
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  flask db migrate -m "add prospect_claim_requests table"
```

确认 migration `upgrade()` 包含 `op.create_table('prospect_claim_requests', ...)` 和唯一约束。

**Step 3: 应用 migration（本地）**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  flask db upgrade
```

期望：无错误，`prospect_projects.link_type` 列存在，`prospect_claim_requests` 表存在。

**Step 4: 验证脚本**

Create: `scripts/temp/verify_lost_projects_models.py`

```python
#!/usr/bin/env python3
import sys, os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("project root not found")

sys.path.insert(0, get_project_root())
from app import create_app, db
from app.models.prospect_project import ProspectProject
from app.models.prospect_claim_request import ProspectClaimRequest

app = create_app()
with app.app_context():
    # 1. link_type 列存在
    cols = [c.name for c in ProspectProject.__table__.columns]
    assert 'link_type' in cols, 'link_type column missing'

    # 2. claim_requests 表能查询
    n = ProspectClaimRequest.query.count()
    print(f'OK: prospect_claim_requests row count = {n}')

    # 3. 唯一约束存在
    uniques = [
        c.name for c in ProspectClaimRequest.__table__.constraints
        if c.__class__.__name__ == 'UniqueConstraint'
    ]
    assert 'uq_claim_project_applicant' in uniques, 'unique constraint missing'

    print('All model checks passed.')
```

Run:
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  python3 scripts/temp/verify_lost_projects_models.py
```

期望输出：`All model checks passed.`

**Step 5: Commit**

```bash
git add app/models/prospect_project.py \
        app/models/prospect_claim_request.py \
        app/models/__init__.py \
        migrations/versions/*add_link_type* \
        migrations/versions/*prospect_claim_requests* \
        scripts/temp/verify_lost_projects_models.py
git commit -m "feat(prospect): add link_type column and prospect_claim_requests table"
```

---

## Phase 2: 活跃度计算 — 离职/无负责人规则

### Task 2.1：修改 calculate_project_activity

**Files:**
- Modify: `app/utils/activity_tracker.py:550-570` (函数 `calculate_project_activity`)

**Step 1: 阅读当前函数**

打开 `app/utils/activity_tracker.py`，找到 `def calculate_project_activity(project)` 函数。注意现有的 frozen 检查在前几行。

**Step 2: 在 frozen 检查之后、其余逻辑之前插入新规则**

在函数的 frozen-stage 检查（约 561 行的 `if project.current_stage in FROZEN_STAGES:`）的 `return` 之后，**正常活动天数计算之前**，插入：

```python
    # 【离职/无负责人规则】优先级仅次于 frozen
    if not project.owner_id:
        return 'churned', '无负责人', project.last_activity_date
    if project.owner is not None and not project.owner.is_active:
        return 'churned', '负责人已离职', project.last_activity_date
```

**Step 3: 验证脚本**

Create: `scripts/temp/verify_churn_owner_rule.py`

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app, db
from app.models.project import Project
from app.models.user import User
from app.utils.activity_tracker import calculate_project_activity, FROZEN_STAGES

app = create_app()
with app.app_context():
    # 找一个非冻结、有活跃负责人的项目
    p = Project.query.filter(
        Project.is_deleted == False,
        Project.owner_id.isnot(None),
        ~Project.current_stage.in_(FROZEN_STAGES)
    ).first()

    if not p:
        print('SKIP: no candidate project for test')
        sys.exit(0)

    original_owner = p.owner
    original_active = original_owner.is_active

    try:
        # case 1: owner inactive
        original_owner.is_active = False
        db.session.flush()
        status, reason, _ = calculate_project_activity(p)
        assert status == 'churned', f"expected churned, got {status}"
        assert reason == '负责人已离职', f"unexpected reason: {reason}"
        print(f'PASS: inactive owner → churned ({reason})')

        # case 2: no owner
        original_owner.is_active = original_active
        original_owner_id = p.owner_id
        p.owner_id = None
        db.session.flush()
        status, reason, _ = calculate_project_activity(p)
        assert status == 'churned' and reason == '无负责人'
        print(f'PASS: no owner → churned ({reason})')

    finally:
        # 清理：回滚所有内存修改（不 commit）
        db.session.rollback()
        print('OK: all reverted')
```

Run:
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  python3 scripts/temp/verify_churn_owner_rule.py
```

期望：两条 PASS。

### Task 2.2：用户停用时同步刷新名下项目活跃度

**Files:**
- Modify: `app/views/admin.py` (找到切换 `is_active` 的路由)
- Modify: `app/utils/activity_tracker.py` (新增辅助函数)

**Step 1: 在 activity_tracker.py 加辅助函数**

在文件末尾追加：

```python
def recompute_projects_for_user(user_id):
    """用户停用/启用后，刷新该用户名下所有非 frozen 项目的活跃度。

    供 admin 路由在切换 is_active 后同步调用。
    """
    from app.models.project import Project

    projects = Project.query.filter(
        Project.is_deleted == False,
        Project.owner_id == user_id,
        ~Project.current_stage.in_(FROZEN_STAGES),
    ).all()

    updated = 0
    for p in projects:
        new_status, reason, last_active = calculate_project_activity(p)
        if p.activity_status != new_status:
            p.activity_status = new_status
            p.activity_reason = reason
            p.last_activity_date = last_active
            updated += 1
    db.session.commit()
    return updated
```

**Step 2: 在 admin 用户停用路由调用**

在 `app/views/admin.py` 用 grep 找到设置 `user.is_active = ...` 的位置：
```bash
grep -n "is_active" app/views/admin.py
```

通常在 `/admin/users/<id>/toggle_active` 之类的路由里。在 `db.session.commit()` 之后追加：

```python
from app.utils.activity_tracker import recompute_projects_for_user
n = recompute_projects_for_user(user.id)
current_app.logger.info(f"用户 {user.id} 状态变更后刷新 {n} 个项目活跃度")
```

**Step 3: 验证脚本**

Create: `scripts/temp/verify_user_deactivation_hook.py`

```python
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app, db
from app.models.project import Project
from app.models.user import User
from app.utils.activity_tracker import recompute_projects_for_user, FROZEN_STAGES

app = create_app()
with app.app_context():
    # 找一个有非冻结项目的用户
    p = Project.query.filter(
        Project.is_deleted == False,
        Project.owner_id.isnot(None),
        ~Project.current_stage.in_(FROZEN_STAGES)
    ).first()

    if not p or not p.owner:
        print('SKIP: no candidate'); sys.exit(0)

    user = p.owner
    original_active = user.is_active
    original_status = p.activity_status

    try:
        user.is_active = False
        db.session.flush()
        n = recompute_projects_for_user(user.id)
        db.session.refresh(p)
        assert p.activity_status == 'churned', f"got {p.activity_status}"
        assert '离职' in (p.activity_reason or '')
        print(f'PASS: deactivation hook flipped {n} projects, sample reason: {p.activity_reason}')
    finally:
        db.session.rollback()
        # 强制还原原状态
        user.is_active = original_active
        p.activity_status = original_status
        db.session.commit()
        print('OK: reverted')
```

Run + 期望两条 PASS。

**Step 4: Commit**

```bash
git add app/utils/activity_tracker.py app/views/admin.py \
        scripts/temp/verify_churn_owner_rule.py \
        scripts/temp/verify_user_deactivation_hook.py
git commit -m "feat(activity): treat owner-inactive/orphan projects as churned"
```

---

## Phase 3: 后端 API

### Task 3.1：list_view 支持 tab 参数

**Files:**
- Modify: `app/views/prospect.py:20-138` (函数 `list_view`)

**Step 1: 在 list_view 顶部读取 tab 参数**

```python
@prospect_bp.route('/')
@login_required
@permission_required('prospect', 'view')   # 沿用原有装饰器
def list_view():
    tab = request.args.get('tab', 'intel')   # 'intel' | 'lost'
    if tab == 'lost':
        return _list_lost_projects()
    return _list_intel(...)   # 原有逻辑封装到这里（重命名）
```

**Step 2: 把原 `list_view` 函数体抽出为私有函数 `_list_intel`**

确保 `_list_intel` 的 prospect 查询加上 `link_type='converted'` 过滤（避免 'research' 类型记录污染情报库）：

```python
query = ProspectProject.query.filter(
    ProspectProject.is_deleted == False,
    ProspectProject.link_type == 'converted',
)
```

**Step 3: 实现 `_list_lost_projects`**

```python
def _list_lost_projects():
    from app.models.project import Project
    from app.utils.activity_tracker import FROZEN_STAGES

    region   = request.args.get('region', '').strip()
    industry = request.args.get('industry', '').strip()
    stage    = request.args.get('stage', '').strip()

    q = Project.query.filter(
        Project.is_deleted == False,
        Project.activity_status == 'churned',
        ~Project.current_stage.in_(FROZEN_STAGES),
    )
    if region:
        q = q.filter(Project.region.ilike(f'%{region}%'))
    if industry == '__none__':
        q = q.filter((Project.industry.is_(None)) | (Project.industry == ''))
    elif industry:
        q = q.filter(Project.industry == industry)
    if stage:
        q = q.filter(Project.current_stage == stage)

    projects = q.order_by(Project.last_activity_date.desc().nullslast()).all()

    return render_template(
        'prospect/tw_list.html',
        tab='lost',
        lost_projects=projects,
    )
```

**Step 4: 引入需要的 import**

文件头部确保有：
```python
from app.models.prospect_project import ProspectProject
```
保持原状即可，无需新加。

### Task 3.2：流失项目公开详情页路由

**Files:**
- Modify: `app/views/prospect.py` (新增路由)

**Step 1: 添加权限辅助函数（顶部 import 区下方）**

```python
def _can_see_lost_sensitive(user, project):
    """是否能看到流失项目的敏感信息（联系人、报价、跟进）。"""
    from app.utils.access_control import can_view_project
    return can_view_project(user, project)
```

**Step 2: 添加路由**

```python
@prospect_bp.route('/lost/<int:project_id>')
@login_required
@permission_required('prospect', 'view')
def lost_detail(project_id):
    from app.models.project import Project
    from app.utils.activity_tracker import FROZEN_STAGES

    project = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()

    # 仅展示真正流失的项目
    if (project.activity_status != 'churned'
            or project.current_stage in FROZEN_STAGES):
        flash('该项目当前不属于流失项目', 'warning')
        return redirect(url_for('prospect.list_view', tab='lost'))

    # 关联的 research 类 prospect（如果有）
    research = ProspectProject.query.filter_by(
        converted_project_id=project.id,
        link_type='research',
    ).first()

    can_view_sensitive = _can_see_lost_sensitive(current_user, project)

    # 已申请记录（用于按钮态）
    from app.models.prospect_claim_request import ProspectClaimRequest
    has_applied = ProspectClaimRequest.query.filter_by(
        project_id=project.id,
        applicant_id=current_user.id,
    ).first() is not None

    return render_template(
        'prospect/tw_lost_detail.html',
        project=project,
        research=research,
        can_view_sensitive=can_view_sensitive,
        has_applied=has_applied,
    )
```

### Task 3.3：申请参与 POST 接口

**Files:**
- Modify: `app/views/prospect.py`

**Step 1: 添加路由**

```python
@prospect_bp.route('/lost/<int:project_id>/apply', methods=['POST'])
@login_required
@permission_required('prospect', 'view')
def lost_apply(project_id):
    from app.models.project import Project
    from app.models.prospect_claim_request import ProspectClaimRequest
    from app.models.message import Message
    from app.utils.activity_tracker import FROZEN_STAGES
    from app.utils.access_control import can_view_project

    project = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()

    if project.activity_status != 'churned' or project.current_stage in FROZEN_STAGES:
        return jsonify(success=False, message='项目不在流失状态'), 400

    # owner / 共享 / admin 不允许申请自己的项目
    if can_view_project(current_user, project):
        return jsonify(success=False, message='您已拥有此项目权限，无需申请'), 400

    reason = (request.json or request.form).get('reason', '').strip()
    if len(reason) < 10:
        return jsonify(success=False, message='申请理由至少 10 个字'), 400
    if len(reason) > 500:
        return jsonify(success=False, message='申请理由不超过 500 字'), 400

    # 唯一约束兜底：检查是否已申请
    existing = ProspectClaimRequest.query.filter_by(
        project_id=project.id, applicant_id=current_user.id
    ).first()
    if existing:
        return jsonify(success=False, message='您已申请过此项目，等待负责人处理'), 409

    # 创建申请
    cr = ProspectClaimRequest(
        project_id=project.id,
        applicant_id=current_user.id,
        reason=reason,
    )
    db.session.add(cr)
    db.session.flush()   # 拿到 cr.id

    # 收件人：owner_id；若空则发给所有 admin
    recipients = []
    if project.owner_id:
        recipients = [project.owner_id]
    else:
        from app.models.user import User
        recipients = [u.id for u in User.query.filter_by(role='admin', is_active=True).all()]

    applicant_name = current_user.real_name or current_user.username
    for rid in recipients:
        msg = Message(
            recipient_id=rid,
            sender_id=current_user.id,
            message_type='prospect_claim_request',
            title=f'{applicant_name} 申请参与流失项目《{project.project_name}》',
            content=reason,
            related_object_type='project',
            related_object_id=project.id,
            extra_data={'claim_request_id': cr.id},
        )
        db.session.add(msg)

    db.session.commit()
    return jsonify(success=True, message='申请已提交，等待负责人处理')
```

### Task 3.4：AI 调研补全接口

**Files:**
- Modify: `app/views/prospect.py`

**Step 1: 添加路由**

```python
@prospect_bp.route('/lost/<int:project_id>/ai-research', methods=['POST'])
@login_required
@permission_required('prospect', 'view')
def lost_ai_research(project_id):
    from app.models.project import Project
    from app.utils.access_control import can_view_project
    from app.services.ai_research_service import research_project_basics

    project = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()

    # 权限：必须能看到这个项目（owner/shared/部门上级/admin）
    if not can_view_project(current_user, project):
        return jsonify(success=False, message='无权限触发 AI 调研'), 403

    # 找已有 research 记录或新建
    research = ProspectProject.query.filter_by(
        converted_project_id=project.id,
        link_type='research',
    ).first()

    if not research:
        research = ProspectProject(
            project_name=project.project_name,
            industry=project.industry,
            region=project.region,
            stage='planning',           # 占位，仅展示
            converted_project_id=project.id,
            link_type='research',
            source='ai',
        )
        db.session.add(research)
        db.session.flush()

    try:
        # 调用现有 AI 调研服务（按需调整参数与函数名）
        result = research_project_basics(project)
        if result.get('description'):
            research.description = result['description']
        if result.get('progress'):
            research.progress = result['progress']
        # stakeholders 写入 ProspectStakeholder（清旧建新）
        from app.models.prospect_project import ProspectStakeholder
        ProspectStakeholder.query.filter_by(prospect_id=research.id).delete()
        for sh in result.get('stakeholders', []):
            db.session.add(ProspectStakeholder(prospect_id=research.id, **sh))

        research.info_updated_at = datetime.utcnow()
        research.info_updated_by = current_user.username
        db.session.commit()
        return jsonify(success=True, message='AI 调研完成')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("AI research failed")
        return jsonify(success=False, message=f'调研失败：{e}'), 500
```

**Step 2: 检查 `research_project_basics` 是否存在**

```bash
grep -n "def research_" app/services/ai_research_service.py
```

如不存在或签名不同，需要：
- 复用最接近的函数（如 `research_prospect`），按其入参/出参适配
- 或新写一个薄封装 `research_project_basics(project)`，内部调现有调研接口，把结果整理成 `{description, progress, stakeholders[]}` 形态

**Step 3: 验证脚本（手工跑）**

Create: `scripts/temp/verify_lost_apply_flow.py`

```python
#!/usr/bin/env python3
"""端到端走一遍：找一个流失项目 → 模拟另一用户调用 apply API → 检查 ClaimRequest + Message 创建"""
import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app, db
from app.models.project import Project
from app.models.user import User
from app.models.prospect_claim_request import ProspectClaimRequest
from app.models.message import Message

app = create_app()
with app.app_context():
    project = Project.query.filter(
        Project.is_deleted == False,
        Project.activity_status == 'churned',
    ).first()
    if not project:
        print('SKIP: no churned project'); sys.exit(0)

    # 选一个非 owner 的用户
    other = User.query.filter(
        User.id != project.owner_id, User.is_active == True
    ).first()
    if not other:
        print('SKIP: no candidate applicant'); sys.exit(0)

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(other.id)

    rv = client.post(f'/prospect/lost/{project.id}/apply',
                     json={'reason': '我有相关行业经验，希望能跟进'})
    body = rv.get_json()
    print('apply response:', rv.status_code, body)

    # 校验
    if rv.status_code == 200:
        cr = ProspectClaimRequest.query.filter_by(
            project_id=project.id, applicant_id=other.id
        ).first()
        assert cr, 'ClaimRequest not created'
        msgs = Message.query.filter_by(
            message_type='prospect_claim_request',
            related_object_id=project.id,
        ).all()
        assert msgs, 'Message not created'
        print('PASS: claim + message created')

        # 清理
        for m in msgs: db.session.delete(m)
        db.session.delete(cr)
        db.session.commit()
        print('OK: cleaned up')
    else:
        # 可能因为权限/重复申请而被拒，也 OK
        print('NOTE: expected business rejection, not a bug')
```

**Step 4: 跑验证**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  python3 scripts/temp/verify_lost_apply_flow.py
```

**Step 5: Commit**

```bash
git add app/views/prospect.py \
        scripts/temp/verify_lost_apply_flow.py
git commit -m "feat(prospect): add lost-projects tab routes (list, detail, apply, ai-research)"
```

---

## Phase 4: 前端模板

### Task 4.1：tw_list.html 加 Tab 切换器

**Files:**
- Modify: `app/templates/prospect/tw_list.html`

**Step 1: 在页面标题下方插入 Tab 切换栏**

找到 `<h1 class="text-xl font-bold ...">市场情报库</h1>` 这行（约 74 行），在它的父 `<div>` 之外、表格之上，插入：

```html
{# Tab 切换 #}
<div class="border-b border-slate-200 dark:border-slate-700 mb-4">
  <nav class="flex gap-6" aria-label="Tabs">
    <a href="{{ url_for('prospect.list_view') }}"
       class="py-3 px-1 border-b-2 text-sm font-medium
              {% if tab != 'lost' %}border-blue-600 text-blue-600
              {% else %}border-transparent text-slate-500 hover:text-slate-700{% endif %}">
      {{ _('市场情报') }}
    </a>
    <a href="{{ url_for('prospect.list_view', tab='lost') }}"
       class="py-3 px-1 border-b-2 text-sm font-medium
              {% if tab == 'lost' %}border-blue-600 text-blue-600
              {% else %}border-transparent text-slate-500 hover:text-slate-700{% endif %}">
      {{ _('流失项目') }}
    </a>
  </nav>
</div>
```

**Step 2: 用 `{% if tab == 'lost' %}` 包裹原有列表 / 新列表**

把原有 `{% call render_tw_data_table(...) %}` 整段包在：

```jinja2
{% if tab != 'lost' %}
  {# 原有市场情报表格 #}
  {% call render_tw_data_table(...) %}
    ...
  {% endcall %}
{% else %}
  {% include 'prospect/_tw_lost_list.html' %}
{% endif %}
```

### Task 4.2：流失项目列表片段

**Files:**
- Create: `app/templates/prospect/_tw_lost_list.html`

**Step 1: 写文件**

```jinja2
{% from 'components/tw_data_table.html' import render_tw_data_table with context %}
{% from 'components/tw_table_cells.html' import tw_cell_link, tw_cell_text, tw_cell_badge with context %}

{% call render_tw_data_table(
    table_id='lostProjectsTable',
    columns=[
      {'label': _('项目名称'), 'key': 'project_name'},
      {'label': _('阶段'), 'key': 'stage'},
      {'label': _('行业'), 'key': 'industry'},
      {'label': _('地区'), 'key': 'region'},
      {'label': _('投资规模'), 'key': 'investment'},
      {'label': _('关联方'), 'key': 'stakeholders'},
      {'label': _('申领人'), 'key': 'owner'},
      {'label': _('活跃度'), 'key': 'activity'},
    ],
    rows=lost_projects,
) %}
  {% for p in lost_projects %}
  <tr class="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
      onclick="window.location='{{ url_for('prospect.lost_detail', project_id=p.id) }}'">
    {{ tw_cell_link(p.project_name, url_for('prospect.lost_detail', project_id=p.id)) }}
    {{ tw_cell_text(p.current_stage or _('未知')) }}
    {{ tw_cell_text(p.industry or _('未分类')) }}
    {{ tw_cell_text(p.region or '-') }}
    {{ tw_cell_text(p.total_investment or '-') }}
    <td class="px-4 py-3 text-sm">
      {# 关联方类型聚合统计：从 Project 关联到的客户/供应商/合作方推断 #}
      {{ stakeholder_summary(p) }}
    </td>
    <td class="px-4 py-3 text-sm">
      {% if p.owner %}
        {{ p.owner.real_name or p.owner.username }}
        <span class="text-xs text-slate-500">({{ _('销售') }})</span>
      {% else %}
        <span class="text-rose-500">{{ _('无负责人') }}</span>
      {% endif %}
    </td>
    <td class="px-4 py-3 text-sm">
      <span class="inline-flex items-center rounded-full bg-rose-100 text-rose-700 px-2 py-0.5 text-xs"
            title="{{ p.activity_reason or '' }}">
        {{ _('流失') }}
      </span>
    </td>
  </tr>
  {% endfor %}
{% endcall %}
```

**Step 2: 关联方聚合宏**

如果 `stakeholder_summary(p)` 不存在，在 `app/templates/macros/ui_helpers.html` 末尾添加：

```jinja2
{% macro stakeholder_summary(project) %}
  {# 从 project 关联推断："设计院 1·总包 1" 形式
     PMA 现有 Project 模型可能没有直接的 stakeholders 关系；
     若有 ProspectProject(link_type='research', converted_project_id=p.id) 才能拿到。
     无关联调研记录 → 显示 "—" #}
  {% set research = project.research_prospect if project.research_prospect is defined else None %}
  {% if research %}
    {% set groups = research.stakeholder_groups %}
    {% if groups %}
      {% for g in groups[:3] %}
        {{ {'owner': '建设单位', 'design': '设计院', 'epc': 'EPC',
            'construction': '总包', 'other': '其他'}.get(g.type, g.type) }} 1{% if not loop.last %}·{% endif %}
      {% endfor %}
    {% else %}—{% endif %}
  {% else %}—{% endif %}
{% endmacro %}
```

**注意**：`project.research_prospect` 这个反向关系需要在 Project 模型加（可选优化）。或者在 view 层预先 attach。**简化方案**：直接在 view 中给每个 lost project 注入 `_research` 属性：

```python
# 在 _list_lost_projects 中加：
research_map = {
    r.converted_project_id: r for r in
    ProspectProject.query.filter(
        ProspectProject.link_type == 'research',
        ProspectProject.converted_project_id.in_([p.id for p in projects]),
    ).all()
}
for p in projects:
    p._research = research_map.get(p.id)
```

模板里改用 `p._research`。

**Step 3: Commit**

```bash
git add app/templates/prospect/tw_list.html \
        app/templates/prospect/_tw_lost_list.html \
        app/templates/macros/ui_helpers.html \
        app/views/prospect.py
git commit -m "feat(prospect): add tab switcher and lost-projects list view"
```

### Task 4.3：流失项目公开详情页

**Files:**
- Create: `app/templates/prospect/tw_lost_detail.html`

**Step 1: 写模板（基础骨架）**

```jinja2
{% extends 'tw_base.html' %}
{% block title %}{{ _('流失项目详情') }} - {{ project.project_name }}{% endblock %}

{% block content %}
<div class="max-w-5xl mx-auto p-6 space-y-6">

  {# 顶部：返回 + 标题 #}
  <div class="flex items-center justify-between">
    <a href="{{ url_for('prospect.list_view', tab='lost') }}"
       class="text-sm text-slate-600 hover:text-slate-900">← {{ _('返回流失项目列表') }}</a>
    {% if not has_applied and not can_view_sensitive %}
      <button id="applyBtn"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm">
        {{ _('申请参与') }}
      </button>
    {% elif has_applied %}
      <span class="text-sm text-slate-500">{{ _('已申请，等待处理') }}</span>
    {% endif %}
  </div>

  <h1 class="text-2xl font-bold">{{ project.project_name }}</h1>

  {# 基本信息 #}
  <section class="bg-white dark:bg-slate-800 rounded-lg p-6 shadow">
    <h2 class="text-lg font-semibold mb-4">{{ _('项目基本信息') }}</h2>
    <dl class="grid grid-cols-2 gap-4 text-sm">
      <div><dt class="text-slate-500">{{ _('阶段') }}</dt><dd>{{ project.current_stage or '-' }}</dd></div>
      <div><dt class="text-slate-500">{{ _('行业') }}</dt><dd>{{ project.industry or _('未分类') }}</dd></div>
      <div><dt class="text-slate-500">{{ _('地区') }}</dt><dd>{{ project.region or '-' }}</dd></div>
      <div><dt class="text-slate-500">{{ _('投资规模') }}</dt><dd>{{ project.total_investment or '-' }}</dd></div>
      <div><dt class="text-slate-500">{{ _('流失原因') }}</dt><dd class="text-rose-600">{{ project.activity_reason or _('120天无活动') }}</dd></div>
      <div><dt class="text-slate-500">{{ _('申领人') }}</dt><dd>
        {% if project.owner %}{{ project.owner.real_name or project.owner.username }}
        {% else %}<span class="text-rose-500">{{ _('无负责人') }}</span>{% endif %}
      </dd></div>
    </dl>

    {% if research and research.description %}
      <div class="mt-4">
        <dt class="text-slate-500 text-sm">{{ _('项目描述') }}</dt>
        <dd class="mt-1 whitespace-pre-line">{{ research.description }}</dd>
      </div>
    {% endif %}

    {% if research and research.progress %}
      <div class="mt-4">
        <dt class="text-slate-500 text-sm">{{ _('最新进展') }}</dt>
        <dd class="mt-1 whitespace-pre-line">{{ research.progress }}</dd>
      </div>
    {% endif %}
  </section>

  {# 关联方 — 公司层公开 #}
  <section class="bg-white dark:bg-slate-800 rounded-lg p-6 shadow">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-lg font-semibold">{{ _('参与方（公司）') }}</h2>
      {% if can_view_sensitive %}
        <button id="aiResearchBtn"
                class="px-3 py-1 bg-emerald-600 text-white text-xs rounded">
          🔍 {{ _('AI 调研补全') }}
        </button>
      {% endif %}
    </div>

    {% if research and research.stakeholder_groups %}
      <ul class="space-y-3">
      {% for g in research.stakeholder_groups %}
        <li class="border-l-2 border-blue-500 pl-3">
          <div class="font-medium">{{ g.company_name }}
            <span class="text-xs text-slate-500">({{ g.type }})</span>
          </div>
          {% if g.primary.address %}
            <div class="text-sm text-slate-600">📍 {{ g.primary.address }}</div>
          {% endif %}
          {% if g.primary.business_scope %}
            <div class="text-sm text-slate-500">{{ g.primary.business_scope }}</div>
          {% endif %}
          {% if can_view_sensitive %}
            {# 联系人列表 #}
            <ul class="mt-2 ml-3 text-sm space-y-1">
              {% for c in g.contacts if c.contact_person %}
                <li>👤 {{ c.contact_person }}{% if c.phone %} · {{ c.phone }}{% endif %}{% if c.email %} · {{ c.email }}{% endif %}</li>
              {% endfor %}
            </ul>
          {% else %}
            <div class="mt-2 text-xs text-slate-400">🔒 {{ _('联系人信息申请参与后可见') }}</div>
          {% endif %}
        </li>
      {% endfor %}
      </ul>
    {% else %}
      <div class="text-sm text-slate-500">
        {{ _('暂无关联方信息。') }}
        {% if can_view_sensitive %}{{ _('点击右上"AI 调研补全"以填充信息。') }}{% endif %}
      </div>
    {% endif %}
  </section>

  {# 受保护区域提示 #}
  {% if not can_view_sensitive %}
  <section class="bg-slate-100 dark:bg-slate-900 rounded-lg p-6">
    <div class="flex items-center text-slate-500">
      <span class="text-2xl mr-3">🔒</span>
      <div>
        <div class="font-medium">{{ _('客户、报价、跟进记录等敏感信息') }}</div>
        <div class="text-sm">{{ _('需获得项目权限或申请参与后由负责人共享后可见') }}</div>
      </div>
    </div>
  </section>
  {% endif %}

</div>

{# 申请参与弹窗 #}
<div id="applyModal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
  <div class="bg-white dark:bg-slate-800 rounded-lg p-6 w-full max-w-md">
    <h3 class="text-lg font-semibold mb-3">{{ _('申请参与项目') }}</h3>
    <textarea id="applyReason" rows="5"
              class="w-full border rounded p-2 text-sm"
              placeholder="{{ _('请填写申请理由（10~500 字）') }}"></textarea>
    <div class="flex justify-end gap-2 mt-4">
      <button id="applyCancel" class="px-4 py-2 text-sm">{{ _('取消') }}</button>
      <button id="applySubmit" class="px-4 py-2 bg-blue-600 text-white rounded text-sm">
        {{ _('提交申请') }}
      </button>
    </div>
  </div>
</div>

<script>
(function(){
  const projectId = {{ project.id }};

  document.getElementById('applyBtn')?.addEventListener('click',
    () => document.getElementById('applyModal').classList.remove('hidden'));
  document.getElementById('applyCancel')?.addEventListener('click',
    () => document.getElementById('applyModal').classList.add('hidden'));

  document.getElementById('applySubmit')?.addEventListener('click', async () => {
    const reason = document.getElementById('applyReason').value.trim();
    if (reason.length < 10) { alert('{{ _("理由至少 10 字") }}'); return; }
    const rv = await fetch(`/prospect/lost/${projectId}/apply`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.content || ''},
      body: JSON.stringify({reason})
    });
    const data = await rv.json();
    alert(data.message);
    if (data.success) location.reload();
  });

  document.getElementById('aiResearchBtn')?.addEventListener('click', async () => {
    if (!confirm('{{ _("调研可能耗时 30~60 秒，确认开始？") }}')) return;
    const btn = document.getElementById('aiResearchBtn');
    btn.disabled = true; btn.textContent = '⏳ ' + '{{ _("调研中...") }}';
    const rv = await fetch(`/prospect/lost/${projectId}/ai-research`, {
      method: 'POST',
      headers: {'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.content || ''},
    });
    const data = await rv.json();
    alert(data.message);
    if (data.success) location.reload();
  });
})();
</script>
{% endblock %}
```

**Step 2: 检查 base 模板名**

```bash
ls app/templates/tw_base.html 2>/dev/null || ls app/templates/_base*.html app/templates/tailwind*.html 2>/dev/null
```

如果不是 `tw_base.html`，改成实际的 base 名（PMA 多个 tw_*.html 详情页都 extends 同一个 base，可参考 `app/templates/expense/tw_expense_detail.html` 第 1 行）。

**Step 3: Commit**

```bash
git add app/templates/prospect/tw_lost_detail.html
git commit -m "feat(prospect): add lost-project public detail page with masked sensitive sections"
```

### Task 4.4：消息收件箱渲染新类型

**Files:**
- Modify: `app/templates/messages/_inbox.html`（或对应渲染消息列表的模板，用 grep 定位）

**Step 1: 找消息渲染模板**

```bash
grep -rn "message_type\|workitem_shared\|worklog_mention" app/templates/ | head -10
```

定位到分类型渲染消息的模板。

**Step 2: 添加 prospect_claim_request 分支**

参考已有 `workitem_shared` 类型的渲染样式，加：

```jinja2
{% elif msg.message_type == 'prospect_claim_request' %}
  <div class="flex items-start gap-3">
    <span class="text-xl">📩</span>
    <div class="flex-1">
      <div class="font-medium">{{ msg.title }}</div>
      <div class="text-sm text-slate-600 mt-1">{{ msg.content }}</div>
      <a href="{{ url_for('project.detail', project_id=msg.related_object_id) }}"
         class="text-xs text-blue-600 mt-1 inline-block">
        {{ _('打开项目页处理') }} →
      </a>
    </div>
  </div>
```

**Step 3: Commit**

```bash
git add app/templates/messages/_inbox.html
git commit -m "feat(messages): render prospect_claim_request notification type"
```

---

## Phase 5: i18n 与最终验证

### Task 5.1：翻译文件

**Files:**
- Modify: `app/translations/en/LC_MESSAGES/messages.po`

**Step 1: 提取新文案**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  pybabel extract -F babel.cfg -k _l -o messages.pot . && \
  pybabel update -i messages.pot -d app/translations
```

**Step 2: 在 en/.../messages.po 编辑新增 msgid 的英文翻译**

主要新增条目：
- "流失项目" → "Lost Projects"
- "市场情报" → "Market Intel"
- "未分类" → "Uncategorized"
- "申请参与" → "Apply to Join"
- "申请理由" → "Application Reason"
- "AI 调研补全" → "AI Research Enrich"
- "无负责人" → "No Owner"
- "负责人已离职" → "Owner Left"
- "联系人信息申请参与后可见" → "Contact info visible after application is approved"
- "已申请，等待处理" → "Submitted, pending"
- "返回流失项目列表" → "Back to Lost Projects"
- "项目基本信息" → "Project Info"
- "参与方（公司）" → "Stakeholders (Companies)"
- "客户、报价、跟进记录等敏感信息" → "Sensitive info (customer, quotation, follow-ups)"
- "需获得项目权限或申请参与后由负责人共享后可见" → "Requires project permission or owner approval"

**Step 3: 编译翻译**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
  pybabel compile -d app/translations
```

**Step 4: Commit**

```bash
git add app/translations/ messages.pot
git commit -m "i18n(prospect): add lost-projects tab translations"
```

### Task 5.2：本地手工冒烟测试清单

**Files:**
- 不改代码，按清单逐项验证

**测试矩阵**：

启动应用：
```bash
./start.sh
```

| # | 场景 | 预期 |
|---|---|---|
| 1 | 用 admin 账号访问 `/prospect/?tab=lost` | 看到流失项目列表，含申领人/活跃度列 |
| 2 | 列表显示"未分类"行业列 | 行业为空的项目显示"未分类" |
| 3 | 点击某行进入详情 | 跳到 `/prospect/lost/<id>`，看到基本信息 |
| 4 | 用 admin 看详情 | "AI 调研补全"按钮显示，"申请参与"按钮不显示 |
| 5 | 用 owner 看详情 | 同 admin |
| 6 | 用其他销售看详情 | "AI 调研补全"按钮**不**显示，"申请参与"按钮显示 |
| 7 | 其他销售点"申请参与" → 输入理由 → 提交 | 提示成功；按钮变"已申请，等待处理" |
| 8 | owner 用户访问 `/messages/` | 看到 prospect_claim_request 消息，含申请理由 |
| 9 | 同一申请人重复申请同一项目 | 接口返回 409，前端 alert 提示 |
| 10 | 把某用户停用（admin /admin/users），其名下非 frozen 项目 activity_status 改 churned，reason='负责人已离职' | 立即在流失列表出现 |
| 11 | 重新激活该用户 → 跑一次定时任务（或调 `recompute_projects_for_user`） | 项目活跃度按真实活动天数重算 |
| 12 | 已签约项目即使 owner 离职，仍 frozen | 不出现在流失列表 |

**任何一条不符 → 回到对应 Task 修复并 commit。**

### Task 5.3：清理临时脚本

**Step 1: 移动验证脚本**

`scripts/temp/` 中的 `verify_*.py` 已完成使命，决定：
- **保留**到 `scripts/archived/2026-Q2/lost-projects-verify/`：作为历史回归参考
- 或**删除**：纯粹的一次性脚本

**Step 2: Commit 最终状态**

```bash
git add scripts/temp/ scripts/archived/  # 视实际操作
git commit -m "chore: archive lost-projects verification scripts"
```

### Task 5.4：完成

**Step 1：自检清单**
- [ ] migration 已 apply 到本地库
- [ ] 5 个 verify_*.py 全部 PASS
- [ ] 12 项手工冒烟全部通过
- [ ] 中英文界面均无未翻译文案
- [ ] 所有改动已 commit

**Step 2：合并主分支前最后一步**
- 跑一遍部署前检查（参考 CLAUDE-DATABASE.md 的备份规范）
- 部署到 NAS 前先在生产备库 apply migration 验证

---

## 依赖关系图

```
Task 1.1 (link_type)  ┐
Task 1.2 (claim model)├─ Task 1.3 (migrate + register)
                      │
Task 2.1 (activity rule) ─ Task 2.2 (admin hook)
                                │
                Task 3.1 (tab) ─┼─ Task 3.2 (detail) ─ Task 3.3 (apply API)
                                │                       │
                                │              Task 3.4 (AI research)
                                │
            Task 4.1 (tab UI) ─ Task 4.2 (list) ─ Task 4.3 (detail page)
                                                  │
                                       Task 4.4 (message render)
                                                  │
                                       Task 5.1 (i18n) ─ Task 5.2 (smoke) ─ Task 5.3 (cleanup)
```

---

## 风险与缓解

| 风险 | 缓解 |
|---|---|
| `research_project_basics` 不存在或签名差异大 | Task 3.4 提供 fallback 方案：写薄封装适配现有调研接口 |
| `can_view_project` 引入循环 import | 局部 `from ... import` 已在路由内做延迟引入 |
| `Project.research_prospect` 反向关系不存在导致模板报错 | 改用 view 层注入 `_research`（已在 Task 4.2 给出） |
| 用户停用 hook 漏覆盖（其他停用入口） | 现有 admin.py 是主路径；如有其他 hook，作为 follow-up 加 |
| 流失项目数量过大列表慢 | 当前不分页；如生产数据量大，后续追加分页参数 |

---

**Plan complete.** Saved to `docs/plans/2026-04-26-lost-projects-tab-implementation.md`.
