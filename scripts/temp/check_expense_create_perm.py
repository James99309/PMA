#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证:财务角色(Treasurer/finance_supervisor)能否进新建报销页 /expense/at_new。

背景:该路由原挂 @permission_required('expense','create'),而 CN 生产库 role_permissions 里
Treasurer/finance_supervisor 的 expense.can_create=false → 403 白页(沈燕、李芸)。
修复后门槛改为 'view',与同模块 edit/delete/submit"自己的单子自己处理"的设计一致。

本地 pma_local 的权限数据与 CN 生产不同(create 是 true),所以脚本在事务里**临时改写**
被测用户的 expense 权限来复刻生产条件,跑完 finally 恢复原值。

两个场景:
  A 复刻生产:view=True, create=False  → 期望 200(旧代码必然 403)
  B 越权护栏:view=False, create=False → 期望 403(证明没放宽过头)

注意:请求必须发在 app_context 之外 —— flask-login 把 current_user 缓存在 g 上,
而 g 是 app-context 级的;若把所有请求包在同一个长生命周期 app_context 里,
第一个用户会泄漏到后续请求(表现为莫名 302 /auth/login)。

运行:export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
      python3 scripts/temp/check_expense_create_perm.py
"""
import os
import sys

PROJECT_ROOT = '/Users/nijie/Documents/PMA'
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv          # noqa: E402
load_dotenv(os.path.join(PROJECT_ROOT, '.env.nas'), override=True)
os.environ['DATABASE_URL'] = 'postgresql://nijie@localhost:5432/pma_local'
os.environ['PMA_DB_TYPE'] = 'sp8d'
os.environ['FORCE_LOCAL_STORAGE'] = 'true'

from config import LocalConfig                          # noqa: E402
from app import create_app, db                          # noqa: E402
from app.models.user import User, Permission            # noqa: E402
from app.models.role_permissions import RolePermission  # noqa: E402

TARGETS = ['沈燕', '李芸']
SCENARIOS = [
    ('A 复刻生产 view=T create=F', True,  200),
    ('B 越权护栏 view=F create=F', False, 403),
]

app = create_app(LocalConfig)


def lookup(real_name):
    """→ (id, role) 或 None"""
    with app.app_context():
        u = User.query.filter_by(real_name=real_name).first()
        return (u.id, u.role) if u else None


def _rows(uid, role):
    return (RolePermission.query.filter_by(role=role, module='expense').all()
            + Permission.query.filter_by(user_id=uid, module='expense').all())


def set_perms(uid, role, can_view):
    """把该用户 expense 的角色权限+个人权限一起钉成 (can_view, create=False),返回原值快照。"""
    with app.app_context():
        snapshot = []
        for r in _rows(uid, role):
            snapshot.append((type(r).__name__, r.id, r.can_view, r.can_create))
            r.can_view, r.can_create = can_view, False
        db.session.commit()
        return snapshot


def restore(snapshot):
    with app.app_context():
        for cls_name, rid, view, create in snapshot:
            cls = RolePermission if cls_name == 'RolePermission' else Permission
            row = cls.query.get(rid)
            row.can_view, row.can_create = view, create
        db.session.commit()


def request_at_new(uid, role):
    """在 app_context 之外发请求,避免 flask-login 的 g 级用户缓存跨请求泄漏。"""
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(uid)
        sess['_fresh'] = True
        sess['role'] = role          # 绕过 before_request 的角色一致性强制登出
    resp = client.get('/expense/at_new', follow_redirects=False)
    return resp.status_code, resp.headers.get('Location')


results = []
for name in TARGETS:
    found = lookup(name)
    if not found:
        print(f'跳过 {name}:本地库无此用户')
        continue
    uid, role = found

    for label, can_view, expected in SCENARIOS:
        snapshot = set_perms(uid, role, can_view)
        try:
            code, loc = request_at_new(uid, role)
        finally:
            restore(snapshot)

        ok = (code == expected)
        results.append(ok)
        print(f'{"PASS" if ok else "FAIL"}  {name}({role:20s}) {label} '
              f'→ GET /expense/at_new = {code} (期望 {expected})'
              + (f'  redirect→{loc}' if loc else ''))


# ── 新建链路上其余端点:在复刻生产的条件下不得再 403(400/415 等都算通过) ──
print()
found = lookup(TARGETS[0])
if found:
    uid, role = found
    snapshot = set_perms(uid, role, True)          # view=True, create=False
    try:
        client = app.test_client()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(uid)
            sess['_fresh'] = True
            sess['role'] = role
        for method, path in [('GET',  '/expense/'),
                             ('GET',  '/expense/at_list'),
                             ('GET',  '/expense/create'),
                             ('POST', '/expense/api/ocr-invoice'),
                             ('POST', '/expense/api/invoices/group'),
                             ('POST', '/expense/api/upload_invoice_temp')]:
            code = client.open(path, method=method).status_code
            ok = code != 403
            results.append(ok)
            print(f'{"PASS" if ok else "FAIL"}  {TARGETS[0]}({role}) {method:4s} {path:38s} '
                  f'→ {code} (只要不是 403)')
    finally:
        restore(snapshot)

print()
if not results:
    print('✗ 没有跑到任何用例')
    sys.exit(1)
if not all(results):
    print(f'✗ 失败 {results.count(False)}/{len(results)} 项')
    sys.exit(1)
print(f'✓ 全部通过 ({len(results)} 项)')
