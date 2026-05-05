# -*- coding: utf-8 -*-
"""
跨系统用户镜像 outbound 客户端

CN admin 在用户管理里勾「海外支持」 → 调本模块 → HTTP 推送到 SG NAS 的
/cross-sync/mirror-user 端点（同代码库不同部署）。

环境变量:
  CROSS_TEAM_PEER_URL    对端 NAS 基础 URL, 如 'https://pma-sg.jamesgpone.win'
  CROSS_SYSTEM_API_KEY   与对端共享的 X-API-Key (复用 cross_sync 同款 env, 不另起)
  CROSS_TEAM_LOCAL_ID    本系统标识 'sp8d' / 'ovs'

如果未配置 → 函数静默返回 (本地修改成功，仅不推送)，便于 dev/单系统部署。
"""
import os
import logging
import time
import requests

logger = logging.getLogger(__name__)


def _peer():
    """取对端配置: (base_url, api_key, local_system_id)"""
    base = os.environ.get('CROSS_TEAM_PEER_URL', '').rstrip('/')
    key = os.environ.get('CROSS_SYSTEM_API_KEY', '')
    local = os.environ.get('CROSS_TEAM_LOCAL_ID', '')
    if not (base and key and local):
        return None, None, None
    return base, key, local


def _post(path: str, payload: dict, timeout: int = 8) -> tuple[bool, dict]:
    """POST 到对端，返回 (ok, json_or_err_dict)"""
    base, key, _ = _peer()
    if not base:
        return False, {'reason': 'CROSS_TEAM_PEER_URL not configured'}
    try:
        r = requests.post(
            f'{base}{path}',
            json=payload,
            headers={'X-API-Key': key, 'Content-Type': 'application/json'},
            timeout=timeout,
        )
        try:
            data = r.json()
        except Exception:
            data = {'raw': r.text[:300]}
        return (r.status_code < 300), data
    except Exception as e:
        logger.error(f'cross_team peer POST {path} failed: {e}')
        return False, {'error': str(e)}


def push_mirror(user) -> tuple[bool, dict]:
    """把本地 user 推送到对端，对端 upsert 一行 is_mirror=true。
    需保证 user.cross_team_visible=True 时调用本函数。
    """
    _, _, local_id = _peer()
    if not local_id:
        return False, {'reason': 'no peer config'}
    payload = {
        'source_system': local_id,
        'source_user_id': user.id,
        'username': user.username,
        'real_name': user.real_name or user.username,
        'email': user.email,
        'password_hash': user.password_hash,
        'is_active': bool(user._is_active),
        'cross_team_label': user.cross_team_label,
    }
    ok, data = _post('/api/v1/cross-sync/mirror-user', payload)
    if ok:
        try:
            user.mirrored_at = time.time()
        except Exception:
            pass
    else:
        logger.warning(f'push_mirror failed user#{user.id}: {data}')
    return ok, data


def push_password(user) -> tuple[bool, dict]:
    """密码变更同步到对端 mirror"""
    _, _, local_id = _peer()
    if not local_id:
        return False, {'reason': 'no peer config'}
    payload = {
        'source_system': local_id,
        'source_user_id': user.id,
        'password_hash': user.password_hash,
    }
    ok, data = _post('/api/v1/cross-sync/sync-password', payload)
    if not ok:
        logger.warning(f'push_password failed user#{user.id}: {data}')
    return ok, data


def push_disable(user) -> tuple[bool, dict]:
    """取消镜像 (勾选取消 / 用户禁用 / 删除)"""
    _, _, local_id = _peer()
    if not local_id:
        return False, {'reason': 'no peer config'}
    payload = {
        'source_system': local_id,
        'source_user_id': user.id,
    }
    ok, data = _post('/api/v1/cross-sync/disable-mirror', payload)
    if not ok:
        logger.warning(f'push_disable failed user#{user.id}: {data}')
    return ok, data


def search_remote_users(q: str, limit: int = 20) -> tuple[bool, list]:
    """对端聊天 @ 搜索 fan-out (GET 方式)
    返回 [{id, username, name, dept, email, label}, ...]; 失败返回空列表
    """
    base, key, _ = _peer()
    if not (base and key):
        return False, []
    try:
        r = requests.get(
            f'{base}/api/v1/cross-sync/users-search',
            params={'q': q, 'limit': limit},
            headers={'X-API-Key': key},
            timeout=6,
        )
        if r.status_code >= 300:
            return False, []
        data = r.json() or {}
        return bool(data.get('success')), data.get('data', []) or []
    except Exception as e:
        logger.warning(f'search_remote_users failed: {e}')
        return False, []


def push_promote(user, conflicting_local_id: int) -> tuple[bool, dict]:
    """SG 端已存在同名/同 email 账号 → 调用对端 promote_to_mirror 把它转为正式 mirror"""
    _, _, local_id = _peer()
    if not local_id:
        return False, {'reason': 'no peer config'}
    payload = {
        'source_system': local_id,
        'source_user_id': user.id,
        'local_user_id': conflicting_local_id,
        'username': user.username,
        'real_name': user.real_name or user.username,
        'email': user.email,
        'password_hash': user.password_hash,
        'cross_team_label': user.cross_team_label,
    }
    ok, data = _post('/api/v1/cross-sync/promote-to-mirror', payload)
    if ok:
        try:
            user.mirrored_at = time.time()
        except Exception:
            pass
    return ok, data
