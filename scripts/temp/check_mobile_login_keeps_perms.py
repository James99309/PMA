#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证:移动端登录不再冲掉用户权限。

背景:app/api/v1/auth.py 原先在"用户没有个人权限行"时调用
assign_user_default_permissions(),而个人权限为空恰恰是管理员点「重置为角色默认」
之后的正常状态。该函数按一张不认识 sales_manager/Treasurer/finace_director 的
旧角色表重建成只读 → 李华伟等人反复丢失新建客户/项目权限。

用一个**临时创建的** sales_manager 用户走真实 HTTP 登录,断言:
  1. 登录成功
  2. 登录后个人权限行仍为 0 条(没被塞进去)
  3. 该用户仍能按角色权限创建客户/项目(role sales_manager 是全开的)
跑完删除临时用户,不留痕。

运行:export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && \
      python3 scripts/temp/check_mobile_login_keeps_perms.py
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

from config import LocalConfig                   # noqa: E402
from app import create_app, db                   # noqa: E402
from app.models.user import User, Permission     # noqa: E402

app = create_app(LocalConfig)

TEST_USERNAME = '_perm_drift_probe'
TEST_PASSWORD = 'Probe!2026#drift'
TEST_ROLE = 'sales_manager'          # 正是受害者李华伟的角色,不在旧角色表里


def create_probe():
    with app.app_context():
        User.query.filter_by(username=TEST_USERNAME).delete()
        db.session.commit()
        u = User(username=TEST_USERNAME, real_name='权限漂移探针',
                 email=f'{TEST_USERNAME}@example.invalid', role=TEST_ROLE,
                 is_active=True, company_name='和源通信（上海）股份有限公司')
        u.set_password(TEST_PASSWORD)
        u.last_login = 1700000000.0          # 非首次登录,避开 first_login 分支
        db.session.add(u)
        db.session.commit()
        # 确保没有任何个人权限行 —— 复刻「重置为角色默认」之后的状态
        Permission.query.filter_by(user_id=u.id).delete()
        db.session.commit()
        return u.id


def drop_probe(uid):
    with app.app_context():
        Permission.query.filter_by(user_id=uid).delete()
        User.query.filter_by(id=uid).delete()
        db.session.commit()


def perm_count(uid):
    with app.app_context():
        return Permission.query.filter_by(user_id=uid).count()


def can(uid, module, action):
    with app.app_context():
        return User.query.get(uid).has_permission(module, action)


uid = create_probe()
results = []
try:
    before = perm_count(uid)
    results.append(('登录前个人权限行数 == 0', before == 0, before))

    client = app.test_client()
    resp = client.post('/api/v1/auth/login',
                       json={'username': TEST_USERNAME, 'password': TEST_PASSWORD})
    ok_login = resp.status_code == 200 and (resp.get_json() or {}).get('success') is True
    results.append(('移动端登录成功', ok_login, resp.status_code))

    after = perm_count(uid)
    results.append(('登录后个人权限行数仍为 0(没被重建)', after == 0, after))

    for module in ('customer', 'project'):
        v = can(uid, module, 'create')
        results.append((f'登录后仍可创建 {module}(跟随 sales_manager 角色)', v is True, v))
finally:
    drop_probe(uid)

for label, ok, detail in results:
    print(f'{"PASS" if ok else "FAIL"}  {label}  → {detail}')

print()
if not all(ok for _, ok, _ in results):
    print(f'✗ 失败 {sum(1 for _, ok, _ in results if not ok)}/{len(results)} 项')
    sys.exit(1)
print(f'✓ 全部通过 ({len(results)} 项)')
