# 潜在项目市场情报库 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 新建独立的"潜在项目市场情报库"模块，销售可按行业/地区/阶段/关键词筛选潜在项目，查看关联方详情，申领项目，批量导入关联方为客户，并预填新建正式项目。

**Architecture:** 独立 `prospect` Blueprint，两张新表（`prospect_projects` + `prospect_stakeholders`），管理员维护数据，所有登录用户可查看/申领，入口在项目列表页顶部按钮。所有模板使用 Tailwind 风格，与现有 `tw_*.html` 保持一致。

**Tech Stack:** Flask Blueprint, SQLAlchemy, Alembic migration, Jinja2 Tailwind 模板, Alpine.js, 现有权限系统 `admin_required` + `permission_required`

---

## Task 1: 数据模型

**Files:**
- Create: `app/models/prospect_project.py`

**Step 1: 创建模型文件**

```python
# app/models/prospect_project.py
from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

PROSPECT_STAGES = {
    'planning': '规划中',
    'designing': '设计中',
    'construction': '在建',
    'completed': '竣工',
}

STAKEHOLDER_TYPES = {
    'owner': '建设单位',
    'design': '设计院',
    'epc': 'EPC承包商',
    'construction': '施工单位',
    'other': '其他',
}

INFO_SOURCES = {
    'eia': '环评公示',
    'tender': '招标公告',
    'ai': 'AI调研',
    'manual': '人工录入',
}


class ProspectProject(db.Model):
    __tablename__ = 'prospect_projects'

    id = Column(Integer, primary_key=True)
    project_name = Column(String(200), nullable=False, index=True)
    industry = Column(String(50), nullable=True)        # 复用现有行业分类
    region = Column(String(100), nullable=True)         # 省份
    city = Column(String(100), nullable=True)           # 城市
    stage = Column(String(20), nullable=False, default='planning')  # 4个阶段
    total_investment = Column(String(50), nullable=True)  # 文本，如"300亿"
    description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)              # 标签数组
    source = Column(String(20), nullable=True)          # 情报来源

    # 申领字段
    claimed_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    claimed_at = Column(DateTime, nullable=True)

    # 转化字段
    converted_project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)

    # 信息更新追踪
    info_updated_at = Column(DateTime, nullable=True)   # 项目情报最近更新时间
    info_updated_by = Column(String(50), nullable=True) # 更新来源标注，如"AI调研"

    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    claimed_by = relationship('User', foreign_keys=[claimed_by_id])
    converted_project = relationship('Project', foreign_keys=[converted_project_id])
    stakeholders = relationship('ProspectStakeholder', backref='prospect',
                                cascade='all, delete-orphan', lazy='dynamic')

    @property
    def stage_label(self):
        return PROSPECT_STAGES.get(self.stage, self.stage)

    @property
    def is_claimed(self):
        return self.claimed_by_id is not None

    @property
    def is_converted(self):
        return self.converted_project_id is not None


class ProspectStakeholder(db.Model):
    __tablename__ = 'prospect_stakeholders'

    id = Column(Integer, primary_key=True)
    prospect_id = Column(Integer, ForeignKey('prospect_projects.id'), nullable=False, index=True)
    stakeholder_type = Column(String(20), nullable=False)  # owner/design/epc/construction/other
    company_name = Column(String(200), nullable=False)
    department = Column(String(100), nullable=True)        # 如"电气电信室"
    address = Column(String(300), nullable=True)
    phone = Column(String(50), nullable=True)
    contact_person = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    @property
    def type_label(self):
        return STAKEHOLDER_TYPES.get(self.stakeholder_type, self.stakeholder_type)
```

**Step 2: 验证模型可导入**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 -c "from app.models.prospect_project import ProspectProject, ProspectStakeholder; print('OK')"
```
Expected: `OK`

**Step 3: Commit**

```bash
git add app/models/prospect_project.py
git commit -m "feat(prospect): add ProspectProject and ProspectStakeholder models"
```

---

## Task 2: 数据库迁移

**Files:**
- Auto-generate: `migrations/versions/XXXX_add_prospect_projects.py`

**Step 1: 在 `app/models/__init__.py` 或导入点注册模型**

在 `app/__init__.py` 中找到其他模型的导入位置，添加：
```python
from app.models.prospect_project import ProspectProject, ProspectStakeholder
```

**Step 2: 生成迁移**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db migrate -m "add prospect projects and stakeholders"
```

检查生成的迁移文件确认包含两张表的 `create_table`。

**Step 3: 执行迁移**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```
Expected: 无报错，数据库新增 `prospect_projects` 和 `prospect_stakeholders` 表。

**Step 4: Commit**

```bash
git add migrations/
git commit -m "feat(prospect): add DB migration for prospect tables"
```

---

## Task 3: Blueprint 基础路由

**Files:**
- Create: `app/views/prospect.py`
- Modify: `app/__init__.py`

**Step 1: 创建 Blueprint 文件**

```python
# app/views/prospect.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app import db
from app.models.prospect_project import ProspectProject, ProspectStakeholder, PROSPECT_STAGES, STAKEHOLDER_TYPES
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.user import User
from app.permissions import admin_required, permission_required, is_admin_or_ceo
from sqlalchemy import or_
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

prospect_bp = Blueprint('prospect', __name__)


@prospect_bp.route('/')
@login_required
@permission_required('project', 'view')
def list_view():
    """潜在项目列表 - 所有有项目查看权限的用户可访问"""
    search = request.args.get('search', '').strip()
    industry = request.args.get('industry', '')
    region = request.args.get('region', '')
    stage = request.args.get('stage', '')

    query = ProspectProject.query.filter(ProspectProject.is_deleted == False)

    if search:
        query = query.filter(
            or_(
                ProspectProject.project_name.ilike(f'%{search}%'),
                ProspectProject.city.ilike(f'%{search}%'),
                ProspectProject.description.ilike(f'%{search}%'),
            )
        )
    if industry:
        query = query.filter(ProspectProject.industry == industry)
    if region:
        query = query.filter(ProspectProject.region.ilike(f'%{region}%'))
    if stage:
        query = query.filter(ProspectProject.stage == stage)

    prospects = query.order_by(ProspectProject.info_updated_at.desc().nullslast(),
                               ProspectProject.created_at.desc()).all()

    # 行业选项复用 Project 模型的映射
    from app.models.project import Project as Proj
    industry_options = [
        ('manufacturing', '制造业'), ('healthcare', '医疗健康'), ('education', '教育'),
        ('finance', '金融'), ('real_estate', '房地产'), ('retail', '零售'),
        ('transportation', '交通运输'), ('energy', '能源'), ('technology', '科技'),
        ('government', '政府'), ('hospitality', '酒店服务'), ('agriculture', '农业'),
    ]

    return render_template(
        'prospect/tw_list.html',
        prospects=prospects,
        industry_options=industry_options,
        stage_options=PROSPECT_STAGES,
        search=search,
        industry=industry,
        region=region,
        stage=stage,
    )


@prospect_bp.route('/<int:id>/panel')
@login_required
@permission_required('project', 'view')
def detail_panel(id):
    """潜在项目详情面板（供列表页 modal 通过 fetch 调用，返回 JSON）"""
    from flask import render_template_string
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()

    # 用 tw_panel.html 中的 macro 渲染各 HTML 片段
    env = current_app.jinja_env
    panel_tmpl = env.get_template('prospect/tw_panel.html')
    stage_badge_html  = panel_tmpl.module.render_stage_badge(p.stage)
    body_html         = panel_tmpl.module.render_body(p)
    footer_left_html  = panel_tmpl.module.render_footer_left(p, current_user)
    footer_actions_html = panel_tmpl.module.render_footer_actions(p, current_user)

    return jsonify({
        'project_name':        p.project_name,
        'city':                p.city or '',
        'region':              p.region or '',
        'stage_badge_html':    stage_badge_html,
        'body_html':           body_html,
        'footer_left_html':    footer_left_html,
        'footer_actions_html': footer_actions_html,
    })


@prospect_bp.route('/<int:prospect_id>/claim', methods=['POST'])
@login_required
@permission_required('project', 'view')
def claim(prospect_id):
    """申领潜在项目"""
    prospect = ProspectProject.query.filter_by(
        id=prospect_id, is_deleted=False
    ).first_or_404()

    if prospect.is_claimed and not is_admin_or_ceo():
        return jsonify({'success': False, 'message': '该项目已被申领'}), 400

    prospect.claimed_by_id = current_user.id
    prospect.claimed_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'claimed_by': current_user.real_name or current_user.username
    })


@prospect_bp.route('/<int:prospect_id>/unclaim', methods=['POST'])
@login_required
@admin_required
def unclaim(prospect_id):
    """管理员取消申领"""
    prospect = ProspectProject.query.filter_by(id=prospect_id, is_deleted=False).first_or_404()
    prospect.claimed_by_id = None
    prospect.claimed_at = None
    db.session.commit()
    return jsonify({'success': True})


@prospect_bp.route('/<int:id>/check-import')
@login_required
@permission_required('project', 'view')
def check_import(id):
    """
    分析关联方与客户库的重复情况，返回 JSON 供前端展示确认弹窗。
    不修改任何数据。

    返回结构:
    {
      "stakeholders": [
        {
          "id": 1,
          "company_name": "茂名瑞派石化工程",
          "stakeholder_type": "design",
          "department": "电气电信室",
          "contact_person": "张工",
          "phone": "0668-2234148",
          "address": "...",
          "company_status": "new",        # new / similar / exact
          "similar_companies": [           # 仅 similar 时有值
            {"id": 5, "name": "茂名瑞派工程设计", "score": 82}
          ],
          "contact_status": "new",        # new / duplicate_name / duplicate_phone
          "duplicate_contact": null        # 仅重复时有值: {"id":3,"name":"张工","phone":"...","company_name":"..."}
        },
        ...
      ]
    }
    """
    import difflib, re

    def _strip_suffix(name):
        """去掉常见企业后缀，用于模糊比较"""
        return re.sub(r'(有限公司|股份有限公司|集团|分公司|工程公司|设计院|研究院|工程设计|工程咨询)$', '', name).strip()

    def _similarity(a, b):
        return int(difflib.SequenceMatcher(None, _strip_suffix(a), _strip_suffix(b)).ratio() * 100)

    prospect = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    all_companies = Company.query.filter_by(is_deleted=False).all()

    result = []
    for s in prospect.stakeholders.all():
        item = {
            'id': s.id,
            'company_name': s.company_name,
            'stakeholder_type': s.stakeholder_type,
            'department': s.department or '',
            'contact_person': s.contact_person or '',
            'phone': s.phone or '',
            'address': s.address or '',
            'notes': s.notes or '',
        }

        # ── 公司查重 ──────────────────────────────────
        exact = next((c for c in all_companies if c.company_name == s.company_name), None)
        if exact:
            item['company_status'] = 'exact'
            item['similar_companies'] = [{'id': exact.id, 'name': exact.company_name, 'score': 100}]
        else:
            similar = [
                {'id': c.id, 'name': c.company_name, 'score': _similarity(c.company_name, s.company_name)}
                for c in all_companies
            ]
            similar = [x for x in similar if x['score'] >= 70]
            similar.sort(key=lambda x: -x['score'])
            item['company_status'] = 'similar' if similar else 'new'
            item['similar_companies'] = similar[:3]

        # ── 联系人查重（仅有联系人时）────────────────
        item['contact_status'] = 'none'
        item['duplicate_contact'] = None
        if s.contact_person:
            dup_name = Contact.query.filter_by(name=s.contact_person, is_deleted=False).first() if hasattr(Contact, 'is_deleted') else Contact.query.filter_by(name=s.contact_person).first()
            dup_phone = None
            if s.phone:
                dup_phone = Contact.query.filter_by(phone=s.phone).first()

            if dup_name:
                item['contact_status'] = 'duplicate_name'
                item['duplicate_contact'] = {
                    'id': dup_name.id, 'name': dup_name.name,
                    'phone': dup_name.phone or '',
                    'company_name': dup_name.company.company_name if dup_name.company else ''
                }
            elif dup_phone:
                item['contact_status'] = 'duplicate_phone'
                item['duplicate_contact'] = {
                    'id': dup_phone.id, 'name': dup_phone.name,
                    'phone': dup_phone.phone or '',
                    'company_name': dup_phone.company.company_name if dup_phone.company else ''
                }
            else:
                item['contact_status'] = 'new'

        result.append(item)

    return jsonify({'stakeholders': result})


@prospect_bp.route('/<int:id>/import-stakeholders', methods=['POST'])
@login_required
@permission_required('project', 'view')
def import_stakeholders(id):
    """
    执行导入。接收前端确认后的选择，批量创建/合并公司和联系人。

    请求体:
    {
      "items": [
        {
          "stakeholder_id": 1,
          "company_action": "new" | "merge",   # new=新建公司, merge=合并到已有
          "merge_company_id": 5,               # 仅 merge 时
          "contact_action": "create" | "skip", # 创建联系人或跳过
          "skip": false                         # true=整条跳过
        }
      ]
    }
    """
    import re, random, string

    def _gen_company_code():
        while True:
            code = 'C' + ''.join(random.choices(string.digits, k=6))
            if not Company.query.filter_by(company_code=code).first():
                return code

    prospect = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    if prospect.claimed_by_id != current_user.id and not is_admin_or_ceo():
        return jsonify({'success': False, 'message': '只有申领人才能导入'}), 403

    items = request.json.get('items', [])
    summary = {'created_companies': 0, 'merged_companies': 0, 'created_contacts': 0, 'skipped': 0}

    for item in items:
        if item.get('skip'):
            summary['skipped'] += 1
            continue

        s = ProspectStakeholder.query.filter_by(id=item['stakeholder_id'], prospect_id=id).first()
        if not s:
            continue

        # ── 公司 ──────────────────────────────────────
        action = item.get('company_action', 'new')
        if action == 'merge':
            company = Company.query.get(item['merge_company_id'])
            summary['merged_companies'] += 1
        else:
            # map stakeholder_type → company_type
            type_map = {
                'owner': '用户', 'design': '设计院及顾问',
                'epc': '总承包单位', 'construction': '总承包单位', 'other': '用户'
            }
            company = Company(
                company_code=_gen_company_code(),
                company_name=s.company_name,
                address=s.address,
                industry=prospect.industry,
                company_type=type_map.get(s.stakeholder_type, '用户'),
                source='销售线索',
                owner_id=current_user.id,
            )
            db.session.add(company)
            db.session.flush()
            summary['created_companies'] += 1

        # ── 联系人 ──────────────────────────────────
        if s.contact_person and item.get('contact_action') == 'create':
            contact = Contact(
                company_id=company.id,
                name=s.contact_person,
                department=s.department,
                phone=s.phone,
            )
            db.session.add(contact)
            summary['created_contacts'] += 1

    db.session.commit()
    return jsonify({'success': True, 'summary': summary})


# ─── 管理员 CRUD ──────────────────────────────────────────────

@prospect_bp.route('/admin/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_new():
    if request.method == 'POST':
        return _save_prospect(None)
    industry_options = _industry_options()
    return render_template('prospect/admin_form.html',
                           prospect=None,
                           stage_options=PROSPECT_STAGES,
                           stakeholder_types=STAKEHOLDER_TYPES,
                           industry_options=industry_options)


@prospect_bp.route('/admin/<int:prospect_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit(prospect_id):
    prospect = ProspectProject.query.filter_by(id=prospect_id, is_deleted=False).first_or_404()
    if request.method == 'POST':
        return _save_prospect(prospect)
    industry_options = _industry_options()
    return render_template('prospect/admin_form.html',
                           prospect=prospect,
                           stakeholders=prospect.stakeholders.all(),
                           stage_options=PROSPECT_STAGES,
                           stakeholder_types=STAKEHOLDER_TYPES,
                           industry_options=industry_options)


@prospect_bp.route('/admin/<int:prospect_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete(prospect_id):
    prospect = ProspectProject.query.filter_by(id=prospect_id, is_deleted=False).first_or_404()
    prospect.is_deleted = True
    db.session.commit()
    flash(_('潜在项目已删除'), 'success')
    return redirect(url_for('prospect.list_view'))


@prospect_bp.route('/admin/<int:prospect_id>/stakeholder/add', methods=['POST'])
@login_required
@admin_required
def admin_add_stakeholder(prospect_id):
    prospect = ProspectProject.query.filter_by(id=prospect_id, is_deleted=False).first_or_404()
    data = request.json
    s = ProspectStakeholder(
        prospect_id=prospect_id,
        stakeholder_type=data.get('stakeholder_type', 'other'),
        company_name=data.get('company_name', ''),
        department=data.get('department', ''),
        address=data.get('address', ''),
        phone=data.get('phone', ''),
        contact_person=data.get('contact_person', ''),
        notes=data.get('notes', ''),
    )
    db.session.add(s)
    prospect.info_updated_at = datetime.utcnow()
    prospect.info_updated_by = '人工更新'
    db.session.commit()
    return jsonify({'success': True, 'id': s.id})


@prospect_bp.route('/admin/stakeholder/<int:stakeholder_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_stakeholder(stakeholder_id):
    s = ProspectStakeholder.query.get_or_404(stakeholder_id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})


def _save_prospect(prospect):
    """新建或更新潜在项目（POST 处理）"""
    data = request.form
    is_new = prospect is None
    if is_new:
        prospect = ProspectProject()

    prospect.project_name = data.get('project_name', '').strip()
    prospect.industry = data.get('industry', '') or None
    prospect.region = data.get('region', '').strip() or None
    prospect.city = data.get('city', '').strip() or None
    prospect.stage = data.get('stage', 'planning')
    prospect.total_investment = data.get('total_investment', '').strip() or None
    prospect.description = data.get('description', '').strip() or None
    prospect.source = data.get('source', '') or None
    prospect.info_updated_at = datetime.utcnow()
    prospect.info_updated_by = '人工更新'

    keywords_raw = data.get('keywords', '').strip()
    prospect.keywords = [k.strip() for k in keywords_raw.split(',') if k.strip()] if keywords_raw else []

    if is_new:
        db.session.add(prospect)

    db.session.commit()
    flash(_('保存成功'), 'success')
    return redirect(url_for('prospect.admin_edit', prospect_id=prospect.id))


def _industry_options():
    return [
        ('manufacturing', '制造业'), ('healthcare', '医疗健康'), ('education', '教育'),
        ('finance', '金融'), ('real_estate', '房地产'), ('retail', '零售'),
        ('transportation', '交通运输'), ('energy', '能源'), ('technology', '科技'),
        ('government', '政府'), ('hospitality', '酒店服务'), ('agriculture', '农业'),
    ]
```

**Step 2: 注册 Blueprint — 修改 `app/__init__.py`**

找到其他 blueprint 的 import 区域，添加：
```python
from app.views.prospect import prospect_bp
```

找到 `app.register_blueprint(expense, ...)` 附近，添加：
```python
app.register_blueprint(prospect_bp, url_prefix='/prospect')
```

**Step 3: 验证路由注册**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 -c "
from app import create_app
app = create_app()
with app.app_context():
    rules = [r.rule for r in app.url_map.iter_rules() if 'prospect' in r.rule]
    print('\n'.join(rules))
"
```
Expected: 列出 `/prospect/`, `/prospect/<id>`, `/prospect/admin/new` 等路由。

**Step 4: Commit**

```bash
git add app/views/prospect.py app/__init__.py
git commit -m "feat(prospect): add prospect blueprint with all routes"
```

---

## Task 4: 列表页模板

**Files:**
- Create: `app/templates/prospect/tw_list.html`

**Step 1: 创建目录和模板**

```bash
mkdir -p app/templates/prospect
```

模板结构参考 `app/templates/pricing_order/tw_list.html`，关键区别：

- 筛选栏：行业下拉 + 地区输入 + 阶段下拉 + 关键词搜索
- 数据展示：卡片网格（非表格），每张卡片含：
  - 项目名称（大）+ 阶段徽章 + 投资规模
  - 城市/省份
  - 申领状态（未申领 / @张三 跟进中 / 已转化为项目）
  - 信息更新时间（灰色小字）
- 管理员专属：右上角"+ 新增"按钮

**阶段徽章颜色对应：**

| 阶段 | 颜色 |
|------|------|
| 规划中 | 蓝色 `bg-blue-100 text-blue-700` |
| 设计中 | 黄色 `bg-yellow-100 text-yellow-700` |
| 在建 | 橙色 `bg-orange-100 text-orange-700` |
| 竣工 | 绿色 `bg-green-100 text-green-700` |

**关键代码片段（卡片部分）：**

```jinja2
{% for p in prospects %}
<tr onclick="openProspectDetail({{ p.id }})"
   class="block bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow">
  <div class="flex items-start justify-between gap-2">
    <h3 class="font-semibold text-gray-900 dark:text-white text-sm leading-tight">{{ p.project_name }}</h3>
    <span class="shrink-0 text-xs px-2 py-0.5 rounded-full
      {% if p.stage == 'planning' %}bg-blue-100 text-blue-700
      {% elif p.stage == 'designing' %}bg-yellow-100 text-yellow-700
      {% elif p.stage == 'construction' %}bg-orange-100 text-orange-700
      {% else %}bg-green-100 text-green-700{% endif %}">
      {{ p.stage_label }}
    </span>
  </div>
  <div class="mt-1 text-xs text-gray-500">
    {{ p.city or p.region or '—' }}
    {% if p.total_investment %} · {{ p.total_investment }}{% endif %}
  </div>
  <div class="mt-2 flex items-center justify-between">
    <span class="text-xs {% if p.is_converted %}text-green-600{% elif p.is_claimed %}text-primary{% else %}text-gray-400{% endif %}">
      {% if p.is_converted %}✓ 已转化为项目
      {% elif p.is_claimed %}● {{ p.claimed_by.real_name or p.claimed_by.username }} 跟进中
      {% else %}未申领{% endif %}
    </span>
    {% if p.info_updated_at %}
    <span class="text-xs text-gray-400">更新 {{ p.info_updated_at | timeago }}</span>
    {% endif %}
  </div>
</a>
{% endfor %}
```

**Step 2: 测试列表页可访问**

启动服务后访问 `http://localhost:5000/prospect/`，确认页面加载、筛选栏渲染正常。

**Step 3: Commit**

```bash
git add app/templates/prospect/tw_list.html
git commit -m "feat(prospect): add prospect list page with filter bar"
```

---

## Task 5: 详情页模板

**Files:**
- Create: `app/templates/prospect/tw_detail.html`

**布局：两栏**
- 左侧（60%）：项目基本信息卡片
- 右侧（40%）：关联方列表

**项目基本信息包含：**
- 项目名称、阶段、行业、地区/城市
- 投资规模、情报来源、描述
- 关键词标签
- 信息更新时间 + 更新来源

**关联方卡片（每个 stakeholder 一张）：**

```jinja2
{% for s in stakeholders %}
<div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
  <div class="flex items-center justify-between">
    <span class="text-xs font-medium px-2 py-0.5 rounded bg-primary/10 text-primary">
      {{ s.type_label }}
    </span>
    {% if is_admin %}
    <button onclick="deleteStakeholder({{ s.id }})"
            class="text-gray-400 hover:text-red-500 text-xs">删除</button>
    {% endif %}
  </div>
  <div class="mt-2 font-semibold text-sm text-gray-900 dark:text-white">{{ s.company_name }}</div>
  {% if s.department %}<div class="text-xs text-gray-500">{{ s.department }}</div>{% endif %}
  {% if s.address %}<div class="text-xs text-gray-500 mt-1">📍 {{ s.address }}</div>{% endif %}
  {% if s.phone %}<div class="text-xs text-gray-500">📞 {{ s.phone }}</div>{% endif %}
  {% if s.contact_person %}<div class="text-xs text-gray-500">👤 {{ s.contact_person }}</div>{% endif %}
  {% if s.notes %}<div class="text-xs text-gray-400 mt-1 italic">{{ s.notes }}</div>{% endif %}
</div>
{% endfor %}
```

**申领区域（页面底部固定栏）：**

```jinja2
<div class="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 p-4">
  {% if prospect.is_converted %}
    <div class="text-green-600 font-medium">✓ 已转化为项目</div>
  {% elif prospect.is_claimed %}
    {% if prospect.claimed_by_id == current_user.id %}
      <!-- 申领人看到：导入客户 + 新建项目 -->
      <button onclick="openImportModal()" class="btn-primary">导入关联方为客户</button>
      <a href="{{ url_for('project.add') }}?from_prospect={{ prospect.id }}"
         class="btn-secondary ml-2">新建项目</a>
    {% else %}
      <div class="text-gray-500">由 <strong>{{ prospect.claimed_by.real_name }}</strong> 跟进中</div>
    {% endif %}
  {% else %}
    <button onclick="claimProject()" class="btn-primary">申领此项目</button>
  {% endif %}
</div>
```

**Step 2: 测试详情页**

访问 `http://localhost:5000/prospect/1`（需先有测试数据），确认两栏布局、关联方卡片、申领按钮渲染正确。

**Step 3: Commit**

```bash
git add app/templates/prospect/tw_detail.html
git commit -m "feat(prospect): add prospect detail page with stakeholder cards"
```

---

## Task 6: 申领 + 导入的前端 JS

**Files:**
- Create: `app/static/js/prospect.js`

```javascript
// app/static/js/prospect.js

const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

async function claimProject(prospectId) {
    const res = await fetch(`/prospect/${prospectId}/claim`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' }
    });
    const data = await res.json();
    if (data.success) {
        showToast(`已申领，由 ${data.claimed_by} 跟进`, 'success');
        setTimeout(() => location.reload(), 800);
    } else {
        showToast(data.message, 'error');
    }
}

async function importStakeholders(prospectId, selectedIds) {
    const res = await fetch(`/prospect/${prospectId}/import-stakeholders`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ stakeholder_ids: selectedIds })
    });
    const data = await res.json();
    if (data.success) {
        const newCount = data.companies.filter(c => !c.existing).length;
        const existCount = data.companies.filter(c => c.existing).length;
        showToast(`已导入 ${newCount} 家新客户，${existCount} 家已存在`, 'success');
        return data.companies;
    } else {
        showToast(data.message, 'error');
        return [];
    }
}

function showToast(message, type = 'info') {
    // 复用现有 toast 机制（参考其他 tw_ 页面的 showToast 实现）
    const event = new CustomEvent('show-toast', { detail: { message, type } });
    document.dispatchEvent(event);
}
```

**详情页导入弹窗（Modal）结构：**

```jinja2
<!-- 导入关联方 Modal（放在 tw_detail.html 底部）-->
<div id="importModal" class="hidden fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
  <div class="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
    <h3 class="text-lg font-semibold mb-4">选择要导入的关联方</h3>
    {% for s in stakeholders %}
    <label class="flex items-center gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer">
      <input type="checkbox" name="stakeholder" value="{{ s.id }}" class="rounded">
      <div>
        <div class="text-sm font-medium">{{ s.company_name }}</div>
        <div class="text-xs text-gray-500">{{ s.type_label }}{% if s.department %} · {{ s.department }}{% endif %}</div>
      </div>
    </label>
    {% endfor %}
    <div class="mt-4 flex justify-end gap-2">
      <button onclick="closeImportModal()" class="btn-secondary">取消</button>
      <button onclick="confirmImport({{ prospect.id }})" class="btn-primary">确认导入</button>
    </div>
  </div>
</div>
```

**Step 2: Commit**

```bash
git add app/static/js/prospect.js
git commit -m "feat(prospect): add prospect JS for claim and import stakeholders"
```

---

## Task 7: 新建项目预填集成

**Files:**
- Modify: `app/views/project.py` — `add` 路由读取 `from_prospect` 参数
- Modify: `app/templates/project/add.html` — 预填字段

**Step 1: 修改 project add 路由**

在 `app/views/project.py` 的 `add` 路由中，读取可选的 `from_prospect` 参数：

```python
@project_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # 从潜在项目预填数据
    prospect_prefill = {}
    from_prospect_id = request.args.get('from_prospect', type=int)
    if from_prospect_id:
        from app.models.prospect_project import ProspectProject
        p = ProspectProject.query.filter_by(id=from_prospect_id, is_deleted=False).first()
        if p:
            prospect_prefill = {
                'project_name': p.project_name,
                'industry': p.industry,
                'region': p.region,
                'city': p.city,
                'end_user': next(
                    (s.company_name for s in p.stakeholders if s.stakeholder_type == 'owner'),
                    ''
                ),
                'design_issues': next(
                    (s.company_name for s in p.stakeholders if s.stakeholder_type == 'design'),
                    ''
                ),
            }
    # ... 现有 add 路由逻辑
    return render_template('project/add.html', ..., prospect_prefill=prospect_prefill,
                           from_prospect_id=from_prospect_id)
```

**Step 2: 在 add.html 中使用预填值**

找到各输入字段，添加 `value` 属性：

```jinja2
<input name="project_name"
       value="{{ prospect_prefill.get('project_name', '') or '' }}" ...>
```

对 `industry`、`region`、`city`、`end_user`、`design_issues` 同理处理。

**Step 3: 项目创建成功后标记 prospect 已转化**

在 `add` 路由的 POST 成功后，检查 `from_prospect_id`：

```python
if from_prospect_id:
    from app.models.prospect_project import ProspectProject
    p = ProspectProject.query.get(from_prospect_id)
    if p:
        p.converted_project_id = new_project.id
        db.session.commit()
```

**Step 4: Commit**

```bash
git add app/views/project.py app/templates/project/add.html
git commit -m "feat(prospect): prefill project form from prospect and mark converted"
```

---

## Task 8: 管理员表单模板

**Files:**
- Create: `app/templates/prospect/admin_form.html`

**表单字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| project_name | text | 必填 |
| industry | select | 现有行业选项 |
| region | text | 省份 |
| city | text | 城市 |
| stage | select | 4个阶段 |
| total_investment | text | 如"300亿" |
| source | select | 情报来源 |
| description | textarea | |
| keywords | text | 逗号分隔 |

**关联方管理（内嵌在同一页面）：**
- 已有关联方列表（可删除）
- "添加关联方"表单（AJAX提交）
- 字段：类型 / 公司名 / 部门 / 地址 / 电话 / 联系人 / 备注

**Step 2: Commit**

```bash
git add app/templates/prospect/admin_form.html
git commit -m "feat(prospect): add admin form for creating/editing prospect projects"
```

---

## Task 9: 项目列表页添加入口按钮

**Files:**
- Modify: `app/templates/project/tw_list.html`

**Step 1: 找到页面顶部操作按钮区域**

搜索 `tw_list.html` 中含"新建项目"的按钮位置，在其旁边添加：

```jinja2
<a href="{{ url_for('prospect.list_view') }}"
   class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium
          text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800
          border border-gray-300 dark:border-gray-600 rounded-lg
          hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
  <span class="material-symbols-outlined text-base">radar</span>
  市场情报库
</a>
```

**Step 2: 验证**

访问项目列表页，确认"市场情报库"按钮出现在操作栏，点击后跳转到 `/prospect/`。

**Step 3: Commit**

```bash
git add app/templates/project/tw_list.html
git commit -m "feat(prospect): add market intelligence entry button to project list"
```

---

## Task 10: 端到端验证

**Step 1: 创建测试数据（管理员操作）**

访问 `/prospect/admin/new`，录入茂名石化项目：
- 项目名：茂名石化炼油转型升级及乙烯提质改造项目
- 行业：能源
- 地区：广东 / 茂名
- 阶段：在建
- 投资规模：300.74亿

添加关联方：
- 建设单位：中石化茂名分公司 / 广东省茂名市双山四路9号大院 / 0668-2264248
- 设计院（电气电信室）：茂名瑞派石化工程有限公司 / 电气电信室 / 0668-2234148

**Step 2: 验证完整流程**

1. 访问 `/prospect/` → 能看到卡片，筛选"能源"/"广东"正常
2. 点击卡片 → 详情页，关联方卡片展示正确
3. 点击"申领" → 申领成功，显示当前用户名
4. 点击"导入关联方为客户" → 勾选两家，确认 → 在客户列表能找到新建的公司
5. 点击"新建项目" → 跳转 add.html，项目名/行业/地区/建设单位已预填
6. 提交新建项目 → 返回详情页显示"已转化为项目"

**Step 3: 最终 Commit**

```bash
git add .
git commit -m "feat(prospect): complete market intelligence module with claim and import flow"
```

---

## 总结

| Task | 内容 | 关键文件 |
|------|------|---------|
| 1 | 数据模型 | `app/models/prospect_project.py` |
| 2 | 数据库迁移 | `migrations/versions/` |
| 3 | Blueprint 路由 | `app/views/prospect.py` + `app/__init__.py` |
| 4 | 列表页 | `app/templates/prospect/tw_list.html` |
| 5 | 详情页 | `app/templates/prospect/tw_detail.html` |
| 6 | 前端 JS | `app/static/js/prospect.js` |
| 7 | 新建项目预填 | `app/views/project.py` + `app/templates/project/add.html` |
| 8 | 管理员表单 | `app/templates/prospect/admin_form.html` |
| 9 | 导航入口 | `app/templates/project/tw_list.html` |
| 10 | 端到端验证 | — |
