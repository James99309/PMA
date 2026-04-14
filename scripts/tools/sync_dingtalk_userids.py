#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量匹配 PMA 用户与钉钉 userid。

策略:
  1. 先拉取钉钉全量通讯录（部门递归 → 用户列表），建本地缓存
  2. 对每个 PMA 用户按 邮箱 > 手机 > 姓名 优先级在缓存里查找
  3. 找到则建/更新 DingtalkUserMapping

优势:
  - 邮箱比手机号更稳定（员工换号但邮箱不变）
  - 一次性拉取，避免 N 次 API 调用
  - 三层兜底，覆盖率最大化

用法:
    python scripts/tools/sync_dingtalk_userids.py            # 仅未映射的活跃用户
    python scripts/tools/sync_dingtalk_userids.py --all      # 全量刷新
    python scripts/tools/sync_dingtalk_userids.py --user 12  # 单用户
    python scripts/tools/sync_dingtalk_userids.py --dump     # 仅打印钉钉缓存内容（调试用）

权限要求:
    qyapi_get_department_list    部门列表
    qyapi_get_user                用户详情（含手机/邮箱/姓名）
    fieldMobile / fieldEmail      用户详情里返回手机/邮箱
"""
import argparse
import os
import re
import sys


def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError('无法找到项目根目录')


sys.path.insert(0, get_project_root())

from app import create_app, db  # noqa: E402
from app.models import User, DingtalkUserMapping  # noqa: E402
from app.services.dingtalk import DingTalkError, get_client, is_dingtalk_enabled  # noqa: E402


MOBILE_RE = re.compile(r'(1\d{10})')


def normalize_mobile(phone):
    if not phone:
        return None
    cleaned = phone.replace(' ', '').replace('-', '').replace('+', '')
    if cleaned.startswith('086'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('86') and len(cleaned) == 13:
        cleaned = cleaned[2:]
    m = MOBILE_RE.search(cleaned)
    return m.group(1) if m else None


def normalize_email(email):
    return email.strip().lower() if email else None


def normalize_name(name):
    return name.strip() if name else None


def fetch_all_dept_ids(client):
    """递归遍历所有部门 id，返回 set。根部门 id=1。"""
    all_ids = {1}
    queue = [1]
    while queue:
        parent = queue.pop()
        try:
            data = client.request_old('POST', '/topapi/v2/department/listsubid',
                                      json_body={'dept_id': parent})
            children = (data.get('result') or {}).get('dept_id_list') or []
            for cid in children:
                if cid not in all_ids:
                    all_ids.add(cid)
                    queue.append(cid)
        except DingTalkError as e:
            print(f'  ⚠ 部门 {parent} 子部门拉取失败: {e}')
    return all_ids


def fetch_dept_users(client, dept_id):
    """分页拉取部门下用户详情。返回 list[dict]。"""
    users = []
    cursor = 0
    while True:
        try:
            data = client.request_old('POST', '/topapi/v2/user/list', json_body={
                'dept_id': dept_id,
                'cursor': cursor,
                'size': 100,
                'order_field': 'modify_desc',
                'contain_access_limit': False,
                'language': 'zh_CN',
            })
            result = data.get('result') or {}
            users.extend(result.get('list') or [])
            if not result.get('has_more'):
                break
            cursor = result.get('next_cursor') or 0
        except DingTalkError as e:
            print(f'  ⚠ 部门 {dept_id} 用户拉取失败: {e}')
            break
    return users


def build_cache(client):
    """全量拉取钉钉通讯录，返回 {by_email, by_mobile, by_name, all_users}。"""
    print('📥 拉取钉钉部门列表...')
    dept_ids = fetch_all_dept_ids(client)
    print(f'   共 {len(dept_ids)} 个部门')

    print('📥 拉取部门下用户...')
    seen_uids = set()
    all_users = []
    for did in dept_ids:
        for u in fetch_dept_users(client, did):
            uid = u.get('userid')
            if uid and uid not in seen_uids:
                seen_uids.add(uid)
                all_users.append(u)

    cache = {'by_email': {}, 'by_mobile': {}, 'by_name': {}}
    for u in all_users:
        uid = u['userid']
        em = normalize_email(u.get('email') or u.get('org_email'))
        mb = normalize_mobile(u.get('mobile'))
        nm = normalize_name(u.get('name'))
        if em:
            cache['by_email'].setdefault(em, uid)
        if mb:
            cache['by_mobile'].setdefault(mb, uid)
        if nm:
            cache['by_name'].setdefault(nm, uid)

    print(f'   共 {len(all_users)} 个用户 (邮箱 {len(cache["by_email"])}, 手机 {len(cache["by_mobile"])}, 姓名 {len(cache["by_name"])})')
    cache['all_users'] = all_users
    return cache


def match_user(cache, user):
    """按 邮箱 > 手机 > 姓名 优先级匹配。返回 (userid, matched_by) 或 (None, None)。"""
    em = normalize_email(user.email)
    if em and em in cache['by_email']:
        return cache['by_email'][em], 'email'

    mb = normalize_mobile(user.phone)
    if mb and mb in cache['by_mobile']:
        return cache['by_mobile'][mb], 'mobile'

    nm = normalize_name(user.real_name)
    if nm and nm in cache['by_name']:
        return cache['by_name'][nm], 'name'

    return None, None


def sync_user(cache, user, force=False):
    existing = DingtalkUserMapping.query.filter_by(pma_user_id=user.id).first()
    if existing and not force:
        return 'skipped (已映射)'

    userid, matched_by = match_user(cache, user)
    if not userid:
        return 'failed (邮箱/手机/姓名都未匹配)'

    if existing:
        existing.dingtalk_userid = userid
        existing.matched_by = matched_by
    else:
        db.session.add(DingtalkUserMapping(
            pma_user_id=user.id,
            dingtalk_userid=userid,
            matched_by=matched_by,
        ))
    db.session.commit()
    return f'✅ {userid} (by {matched_by})'


def main():
    parser = argparse.ArgumentParser(description='钉钉 userid 映射同步')
    parser.add_argument('--all', action='store_true', help='包括已映射的用户')
    parser.add_argument('--user', type=int, help='仅同步指定用户')
    parser.add_argument('--dump', action='store_true', help='仅打印钉钉缓存内容')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if not is_dingtalk_enabled():
            print('❌ 钉钉集成未启用，请检查 DINGTALK_ENABLED / PMA_DB_TYPE / 凭证')
            sys.exit(1)

        client = get_client()
        cache = build_cache(client)

        if args.dump:
            print('\n=== 钉钉用户列表 ===')
            for u in cache['all_users']:
                print(f"  {u.get('userid'):<24} {u.get('name','--'):<10} "
                      f"{u.get('mobile','--'):<14} {u.get('email') or u.get('org_email') or '--'}")
            return

        query = User.query.filter(User._is_active == True)  # noqa: E712
        if args.user:
            query = query.filter(User.id == args.user)
        elif not args.all:
            mapped_ids = db.session.query(DingtalkUserMapping.pma_user_id).subquery()
            query = query.filter(~User.id.in_(db.select(mapped_ids)))

        users = query.all()
        print(f'\n📋 准备处理 {len(users)} 个 PMA 用户')
        success = 0
        for u in users:
            try:
                result = sync_user(cache, u, force=args.all)
            except Exception as e:
                result = f'ERROR: {e}'
            if result.startswith('✅'):
                success += 1
            print(f'  [{u.id:>3}] {(u.real_name or u.username):<10} '
                  f'{(u.email or "--"):<32} → {result}')
        print(f'\n✅ 完成: {success}/{len(users)} 匹配成功')


if __name__ == '__main__':
    main()
