"""Claude AI 代理服务

负责：
- 启用/禁用用户的 Claude AI 代理权限
- 生成 token + 发送通知邮件
- 与 Mac mini admin_server 双向同步（推送白名单 / 拉取用量）

Mac mini 端配置：
- 公网代理 URL: https://mac-proxy.jamesgpone.win
- admin_server: http://100.110.41.83:8318/  （Tailscale 内）
- 共享密钥：通过 X-API-Key header（PMA .env 配 CLAUDE_AI_PROXY_SHARED_KEY）

依赖环境变量：
- CLAUDE_AI_PROXY_ADMIN_URL  (默认 http://100.110.41.83:8318)
- CLAUDE_AI_PROXY_PUBLIC_URL (默认 https://mac-proxy.jamesgpone.win)
- CLAUDE_AI_PROXY_SHARED_KEY (必需，与 Mac mini 共享)
- CLAUDE_AI_DEFAULT_QUOTA    (默认 50000000)
"""
import os
import logging
import requests
from datetime import datetime, date, timedelta
from flask import current_app
from app import db
from app.models.user import User
from app.models.ai_proxy_usage import AIProxyUsage

logger = logging.getLogger(__name__)


# ── 配置 ──────────────────────────────────────────────────────────────────────

def _admin_url():
    return os.environ.get('CLAUDE_AI_PROXY_ADMIN_URL') or current_app.config.get(
        'CLAUDE_AI_PROXY_ADMIN_URL', 'http://100.110.41.83:8318'
    )


def _public_url():
    return os.environ.get('CLAUDE_AI_PROXY_PUBLIC_URL') or current_app.config.get(
        'CLAUDE_AI_PROXY_PUBLIC_URL', 'https://mac-proxy.jamesgpone.win'
    )


def _shared_key():
    return os.environ.get('CLAUDE_AI_PROXY_SHARED_KEY') or current_app.config.get(
        'CLAUDE_AI_PROXY_SHARED_KEY', ''
    )


def default_quota():
    """全局默认月度配额（tokens）"""
    val = os.environ.get('CLAUDE_AI_DEFAULT_QUOTA') or current_app.config.get(
        'CLAUDE_AI_DEFAULT_QUOTA', 50_000_000
    )
    try:
        return int(val)
    except (TypeError, ValueError):
        return 50_000_000


# ── Mac mini 同步：推送白名单 ───────────────────────────────────────────────

def _build_sync_payload():
    """生成 Mac mini 需要的全量白名单 payload"""
    import os
    db_type = os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE', 'sp8d')
    source = db_type  # sp8d → cf-tunnel-sp8d, ovs → cf-tunnel-ovs

    users = User.query.filter(User.claude_ai_token.isnot(None)).all()
    items = []
    for u in users:
        items.append({
            'token': u.claude_ai_token,
            'name': (u.real_name or u.username or '').strip() or f'user-{u.id}',
            'enabled': bool(u.claude_ai_enabled and u.is_active),
            'quota': int(u.claude_ai_quota_tokens or default_quota()),
            'user_id': u.id,
            'email': u.email or '',
        })
    return {'items': items, 'source': source, 'as_of': datetime.utcnow().isoformat(timespec='seconds')}


def push_to_macmini(timeout=10):
    """全量推送白名单到 Mac mini admin_server。
    返回 (ok, message)。失败不抛异常，让调用方决定降级（依赖 30 分钟兜底任务）。
    """
    url = _admin_url().rstrip('/') + '/api/sync'
    key = _shared_key()
    if not key:
        logger.warning('CLAUDE_AI_PROXY_SHARED_KEY 未配置，跳过推送')
        return False, 'missing shared key'
    try:
        payload = _build_sync_payload()
        resp = requests.post(
            url,
            json=payload,
            headers={'X-API-Key': key, 'Content-Type': 'application/json'},
            timeout=timeout,
        )
        if resp.status_code == 200:
            logger.info(f'Claude 代理白名单已推送到 Mac mini，共 {len(payload["items"])} 条')
            return True, 'ok'
        return False, f'http {resp.status_code}: {resp.text[:200]}'
    except Exception as e:
        logger.warning(f'推送 Claude 代理白名单到 Mac mini 失败: {e}')
        return False, str(e)


# ── Mac mini 同步：拉取用量 ────────────────────────────────────────────────

def pull_usage_from_macmini(timeout=15):
    """从 Mac mini admin_server 拉取所有用户的 token 用量，写入 ai_proxy_usage 表。
    返回 (ok, count) 或 (False, error_msg)。
    """
    url = _admin_url().rstrip('/') + '/api/devices'
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return False, f'http {resp.status_code}'
        data = resp.json()
    except Exception as e:
        return False, str(e)

    devices = data.get('devices', [])
    # token → user_id 映射
    tokens = [d.get('ip', '') for d in devices if d.get('ip', '').startswith('cp-')]
    if not tokens:
        return True, 0
    users_by_token = {u.claude_ai_token: u for u in User.query.filter(User.claude_ai_token.in_(tokens)).all()}

    today = date.today()
    updated = 0
    for d in devices:
        token = d.get('ip', '')
        if not token.startswith('cp-'):
            continue
        user = users_by_token.get(token)
        if not user:
            continue

        # 同步当日用量；月维度仍由 Mac mini usage.json 累计
        # 这里只更新 today 一行（Mac mini 是真实数据源，PMA 只缓存）
        in_tokens = int(d.get('tokens_month_in', 0) or 0)  # 用月输入估今日（粗略）
        out_tokens = int(d.get('tokens_month_out', 0) or 0)
        req_count = int(d.get('requests_today', 0) or 0)
        last_seen = d.get('last_seen')

        # 更精细的做法是按日抽取，但当前 admin API 只给月度聚合 + today 请求数。
        # 这里用 today 做为一个 row，input/output 写月聚合（覆盖之前的）。
        # 实际真正按日查询会从 Mac mini admin_server 的 /api/usage?ip=xxx 拉。
        # 为简单起见此版本只缓存 today 总览供排行榜用。
        rec = AIProxyUsage.query.filter_by(user_id=user.id, provider='claude', date=today).first()
        if not rec:
            rec = AIProxyUsage(user_id=user.id, provider='claude', date=today)
            db.session.add(rec)
        # 这里写"月累计"到 today 行的 input/output 是错的——下面改成只更新 request_count，
        # input/output 由更细粒度的 _pull_user_daily_usage 单独刷
        rec.request_count = req_count
        if last_seen:
            try:
                rec.last_seen_at = datetime.fromisoformat(last_seen)
            except Exception:
                pass
        updated += 1

    db.session.commit()

    # 更细粒度地拉每个用户的 14 天历史用量
    for token, user in users_by_token.items():
        _pull_user_daily_usage(user, token, days=14)

    return True, updated


def _pull_user_daily_usage(user, token, days=14):
    """从 Mac mini /api/usage?ip=<token>&days=N 拉取指定用户的每日用量并落库。"""
    url = _admin_url().rstrip('/') + '/api/usage'
    try:
        resp = requests.get(url, params={'ip': token, 'days': days}, timeout=10)
        if resp.status_code != 200:
            return
        d = resp.json()
    except Exception as e:
        logger.debug(f'拉用户日用量失败 user={user.id}: {e}')
        return

    labels = d.get('labels', [])  # MM-DD
    inputs = d.get('input', [])
    outputs = d.get('output', [])
    reqs = d.get('requests', [])

    today = date.today()
    for i, mmdd in enumerate(labels):
        try:
            month, day = mmdd.split('-')
            target = date(today.year, int(month), int(day))
            # 跨年处理：如果目标月>当前月超过6，认为是去年
            if target > today + timedelta(days=1):
                target = date(today.year - 1, int(month), int(day))
        except Exception:
            continue

        in_t = int(inputs[i] or 0) if i < len(inputs) else 0
        out_t = int(outputs[i] or 0) if i < len(outputs) else 0
        req_c = int(reqs[i] or 0) if i < len(reqs) else 0

        if in_t == 0 and out_t == 0 and req_c == 0:
            continue

        rec = AIProxyUsage.query.filter_by(user_id=user.id, provider='claude', date=target).first()
        if not rec:
            rec = AIProxyUsage(user_id=user.id, provider='claude', date=target)
            db.session.add(rec)
        rec.input_tokens = in_t
        rec.output_tokens = out_t
        rec.request_count = req_c

    db.session.commit()


# ── 用量统计查询（给后台 UI 用）────────────────────────────────────────────

def get_user_usage_summary(user_id):
    """返回某用户的 1天 / 7天 / 30天 / 本月 用量汇总"""
    today = date.today()
    week_start = today - timedelta(days=6)
    month_start = today.replace(day=1)
    last30_start = today - timedelta(days=29)

    q = AIProxyUsage.query.filter_by(user_id=user_id, provider='claude')

    def _sum(start_date):
        rows = q.filter(AIProxyUsage.date >= start_date).all()
        return {
            'input': sum(r.input_tokens or 0 for r in rows),
            'output': sum(r.output_tokens or 0 for r in rows),
            'total': sum((r.input_tokens or 0) + (r.output_tokens or 0) for r in rows),
            'requests': sum(r.request_count or 0 for r in rows),
        }

    return {
        'today': _sum(today),
        'last_7_days': _sum(week_start),
        'last_30_days': _sum(last30_start),
        'this_month': _sum(month_start),
    }


# ── 启用/禁用用户（核心 API）─────────────────────────────────────────────

def enable_user(user, quota_tokens=None, send_email=True):
    """启用某用户的 Claude AI 代理。
    返回 dict {token, is_new_token, email_sent, push_ok, push_msg}

    邮件触发逻辑：只要本次操作让 enabled 从 False → True（或首次生成 token），就发邮件。
    单纯改配额而 enabled 一直是 True 的不算（quota 路由单独处理）。
    """
    if not user.is_active:
        raise ValueError('用户未激活，不能开通 Claude AI 代理')
    if not user.email:
        raise ValueError('用户未绑定邮箱，无法发送 token')

    was_enabled = bool(user.claude_ai_enabled)
    token, is_new = user.enable_claude_ai(quota_tokens=quota_tokens)
    db.session.commit()

    email_sent = False
    should_email = send_email and (is_new or not was_enabled)  # 新 token 或刚被开启都发
    if should_email:
        try:
            from app.utils.email import send_claude_ai_token_email
            email_sent = send_claude_ai_token_email(user, token)
        except Exception as e:
            logger.warning(f'发送 Claude AI 邮件失败 user={user.id}: {e}')

    push_ok, push_msg = push_to_macmini()

    return {
        'token': token,
        'is_new_token': is_new,
        'email_sent': email_sent,
        'push_ok': push_ok,
        'push_msg': push_msg,
    }


def disable_user(user):
    """禁用某用户的 Claude AI 代理。"""
    user.disable_claude_ai()
    db.session.commit()
    return push_to_macmini()


def reset_user_token(user, send_email=True):
    """重置 token；返回 (new_token, email_sent, push_ok)"""
    if not user.claude_ai_enabled:
        raise ValueError('用户未启用 Claude AI 代理，无需重置')
    new_token = user.reset_claude_ai_token()
    db.session.commit()

    email_sent = False
    if send_email:
        try:
            from app.utils.email import send_claude_ai_token_email
            email_sent = send_claude_ai_token_email(user, new_token, is_reset=True)
        except Exception as e:
            logger.warning(f'发送 Claude AI 重置邮件失败 user={user.id}: {e}')

    push_ok, _ = push_to_macmini()
    return new_token, email_sent, push_ok


def update_user_quota(user, quota_tokens):
    """单独修改某用户的月度配额（不重发邮件）。"""
    user.claude_ai_quota_tokens = int(quota_tokens or 0)
    db.session.commit()
    return push_to_macmini()


# ── 设备锁定 ───────────────────────────────────────────────────────────────

def get_device_lock_status(token, timeout=3):
    """返回某 token 的设备锁定 ID，获取失败返回 None。"""
    url = _admin_url().rstrip('/') + '/api/device-lock'
    try:
        resp = requests.get(url, params={'token': token}, timeout=timeout)
        if resp.status_code == 200:
            return resp.json().get('locked_device_id')
    except Exception as e:
        logger.debug(f'获取设备锁定状态失败 token={token[:14]}…: {e}')
    return None


def clear_device_lock(token, timeout=5):
    """清除某 token 的设备锁定。返回 (ok, msg)。"""
    url = _admin_url().rstrip('/') + '/api/device-lock'
    key = _shared_key()
    if not key:
        return False, 'missing shared key'
    try:
        resp = requests.delete(
            url,
            json={'token': token},
            headers={'X-API-Key': key, 'Content-Type': 'application/json'},
            timeout=timeout,
        )
        if resp.status_code == 200:
            return True, 'ok'
        return False, f'http {resp.status_code}: {resp.text[:100]}'
    except Exception as e:
        logger.warning(f'清除设备锁定失败 token={token[:14]}…: {e}')
        return False, str(e)
