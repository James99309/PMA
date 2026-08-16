#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证任务类下钻的三组结构(已通过/待审核/进行中)。

本地库这三类任务几乎没有数据,合计一致性测不到这些分支。用事务插入临时任务、
断言结构、最后 rollback —— 不留任何脏数据。
"""
import sys, os
from datetime import datetime, timedelta

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())
DB = os.environ.get('PM_CHECK_DB', 'postgresql://nijie@localhost/pma_local')
os.environ['DATABASE_URL'] = DB
os.environ['SQLALCHEMY_DATABASE_URI'] = DB

from app import create_app, db  # noqa: E402
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = DB

S, E = datetime(2026, 4, 1), datetime(2026, 7, 1)

with app.app_context():
    from app.models.user import User
    from app.models.task import Task
    from app.services import kpi_actual_service as K

    u = User.query.filter_by(username='suwen').first()
    assert u, "找不到测试用户 suwen"
    print(f"测试用户: {u.real_name} (id={u.id})")

    made = [
        Task(title='[临时]研发-超出预期', creator_id=u.id, assignee_id=u.id,
             status='completed', priority='normal', task_type='pm_rd',
             review_status='approved', review_score=1.5,
             completed_at=datetime(2026, 5, 10), created_at=datetime(2026, 4, 2),
             reviewer_id=u.id, is_deleted=False),
        Task(title='[临时]研发-低于预期', creator_id=u.id, assignee_id=u.id,
             status='completed', priority='normal', task_type='pm_rd',
             review_status='approved', review_score=0.5,
             completed_at=datetime(2026, 5, 20), created_at=datetime(2026, 4, 2),
             is_deleted=False),
        Task(title='[临时]研发-旧数据无评价', creator_id=u.id, assignee_id=u.id,
             status='completed', priority='normal', task_type='pm_rd',
             review_status='approved', review_score=None,
             completed_at=datetime(2026, 6, 1), created_at=datetime(2026, 4, 2),
             is_deleted=False),
        Task(title='[临时]研发-完成待审核', creator_id=u.id, assignee_id=u.id,
             status='completed', priority='normal', task_type='pm_rd',
             review_status='pending_review',
             completed_at=datetime(2026, 6, 5), created_at=datetime(2026, 4, 2),
             is_deleted=False),
        Task(title='[临时]研发-进行中已逾期', creator_id=u.id, assignee_id=u.id,
             status='in_progress', priority='normal', task_type='pm_rd',
             due_date=datetime(2026, 6, 20), created_at=datetime(2026, 4, 3),
             is_deleted=False),
        Task(title='[临时]研发-软删除(应被忽略)', creator_id=u.id, assignee_id=u.id,
             status='completed', priority='normal', task_type='pm_rd',
             review_status='approved', review_score=1.0,
             completed_at=datetime(2026, 5, 15), created_at=datetime(2026, 4, 2),
             is_deleted=True),
    ]
    db.session.add_all(made)
    db.session.flush()          # 只进事务,不提交

    actual = K._KPI_ACTUAL_FNS['pm_dev_rate'](u, S, E)
    d = K.get_actual_detail(u, 'pm_dev_rate', S, E)

    print(f"\n采集器实际值 = {actual}   (期望 3.0 = 1.5+0.5+1.0兜底,软删除不计)")
    print(f"明细合计     = {d['total']}")
    print(f"meta  : {d['meta']}")
    print(f"basis : {d['basis']}")
    print(f"mismatch: {d.get('mismatch')}")
    print("\n分组结构:")
    for g in d['groups']:
        print(f"  [{g['label']}]  {g['value_display']}  tone={g.get('tone')}")
        for r in g['rows']:
            print(f"      {r['name']:<24} {r['sub']}   {r['value_display']}")

    errs = []
    if abs(actual - 3.0) > 1e-6:
        errs.append(f"采集器={actual},期望 3.0")
    if abs(d['total'] - actual) > 1e-6:
        errs.append(f"明细合计={d['total']} != 采集器={actual}")
    if len(d['groups']) != 3:
        errs.append(f"应有 3 组,实得 {len(d['groups'])}")
    if any('软删除' in r['name'] for g in d['groups'] for r in g['rows']):
        errs.append("软删除任务被列出")
    if d['groups'][1].get('tone') != 'warn' or d['groups'][2].get('tone') != 'warn':
        errs.append("后两组未标警示色")

    db.session.rollback()
    print("\n已 rollback,数据库无残留。")
    remain = Task.query.filter(Task.title.like('[临时]%')).count()
    print(f"残留临时任务数 = {remain}(应为 0)")
    if remain:
        errs.append("rollback 后仍有残留")

    if errs:
        print("\n❌ 失败:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print("\n✅ 三组结构 / 加权求和 / 软删除排除 / 兜底1.0 全部正确")
