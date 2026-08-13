#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证:补完门禁后,"能看不能建"的角色看不到创建入口;有权限的角色仍看得到。

两个方向都要测 —— 只测"藏起来"会漏掉把入口对有权限的人也藏掉的过度修复。

场景来自 CN 生产权限表的真实夹缝:
  quotation.create 缺口 → finance_supervisor(李芸) / hr_manager / product_manager

运行:export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
      python3 scripts/temp/check_entry_gate_visibility.py
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
from app.models.customer import Company                 # noqa: E402
from app.models.project import Project                  # noqa: E402

app = create_app(LocalConfig)
MARKER = '/quotation/at_new'          # 创建报价入口的 URL 特征


def lookup(real_name):
    with app.app_context():
        u = User.query.filter_by(real_name=real_name).first()
        return (u.id, u.role) if u else None


def targets(uid):
    """取一条该用户**数据权限范围内**的客户/项目 —— 随便挑会撞 403(看不见那条数据),
    那是数据权限不是门禁问题,会污染本次验证。"""
    with app.app_context():
        from app.utils.access_control import get_viewable_data
        u = User.query.get(uid)
        c = get_viewable_data(Company, u, [Company.is_deleted == False]).first()
        p = get_viewable_data(Project, u, [Project.is_deleted == False]).first()
        return (c.id if c else None), (p.id if p else None)


def set_quotation_create(uid, role, can_create):
    with app.app_context():
        snap = []
        rows = (RolePermission.query.filter_by(role=role, module='quotation').all()
                + Permission.query.filter_by(user_id=uid, module='quotation').all())
        for r in rows:
            snap.append((type(r).__name__, r.id, r.can_view, r.can_create))
            r.can_view, r.can_create = True, can_create
        db.session.commit()
        return snap


def restore(snap):
    with app.app_context():
        for cls_name, rid, view, create in snap:
            cls = RolePermission if cls_name == 'RolePermission' else Permission
            row = cls.query.get(rid)
            row.can_view, row.can_create = view, create
        db.session.commit()


def fetch(uid, role, path):
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(uid)
        sess['_fresh'] = True
        sess['role'] = role
    r = client.get(path, follow_redirects=False)
    return r.status_code, r.get_data(as_text=True)


def pick_user():
    """优先用真实受害者李芸;她在本地库若无可见客户/项目,则换一个非 admin
    且**有**可见客户+项目的用户 —— admin 不能用,它在 has_permission 里直接短路返回 True,
    没法模拟"无 create 权限"这一侧。"""
    first = lookup('李芸')
    if first and all(targets(first[0])):
        return first + ('李芸',)
    with app.app_context():
        # 必须 is_active —— 停用账号会被 before_request 强制登出,请求全变 302
        candidates = [(u.id, u.role, u.real_name or u.username)
                      for u in User.query.filter(User.role != 'admin').limit(120).all()
                      if u.is_active]
    for uid_, role_, name_ in candidates:
        if all(targets(uid_)):
            return uid_, role_, name_
    return (first + ('李芸',)) if first else None


picked = pick_user()
if not picked:
    print('本地库找不到可用于验证的用户')
    sys.exit(1)
uid, role, uname = picked
cid, pid = targets(uid)
print(f'验证用户:{uname} ({role})  客户#{cid} 项目#{pid}\n')

PAGES = [('报价列表', '/quotation/at_list')]
if cid:
    PAGES.append(('客户详情-关联报价', f'/customer/{cid}/at_view'))
if pid:
    PAGES.append(('项目详情-关联报价', f'/project/{pid}/at_view'))

results = []
# can_create=False → 入口应消失;can_create=True → 入口应仍在
for can_create, expect_marker in [(False, False), (True, True)]:
    snap = set_quotation_create(uid, role, can_create)
    try:
        for label, path in PAGES:
            code, body = fetch(uid, role, path)
            has = MARKER in body
            ok = (code == 200) and (has == expect_marker)
            results.append(ok)
            print(f'{"PASS" if ok else "FAIL"}  quotation.create={str(can_create):5s} '
                  f'{label:22s} {path:34s} → {code}, 入口{"在" if has else "无"} '
                  f'(期望{"在" if expect_marker else "无"})')
    finally:
        restore(snap)

print()
if not all(results):
    print(f'✗ 失败 {results.count(False)}/{len(results)} 项')
    sys.exit(1)
print(f'✓ 全部通过 ({len(results)} 项)')
