"""
APNs Push Notification Service.

依赖 env(全部缺则 send_push 静默返回 0, 不影响其他功能):
- APNS_BUNDLE_ID:        com.evertacsolutions.pma.mobile  (apns-topic)
- APNS_TEAM_ID:          N2L8SYV8GY  (Apple Developer Team ID)
- APNS_KEY_ID:           10 位字符串(Apple Developer → Keys 页面)
- APNS_AUTH_KEY_PATH:    .p8 文件绝对路径(从 Apple 下载, 仅 1 次)
- APNS_USE_SANDBOX:      "true"=sandbox(Xcode run 调试用); 默认 false=生产(TestFlight/AppStore)

Apple APNs HTTP/2 endpoint:
  https://api.push.apple.com/3/device/{device_token}            ← 生产
  https://api.sandbox.push.apple.com/3/device/{device_token}    ← sandbox

JWT 鉴权 (ES256), Apple 限定 token ≤ 1h, 我们 50min refresh 一次。
"""
import os
import time
import logging
import threading
import jwt
import httpx
from typing import Optional, Iterable

logger = logging.getLogger(__name__)

_jwt_lock = threading.Lock()
_jwt_cache = {'token': None, 'expires_at': 0}


def _is_configured() -> bool:
    return all([
        os.environ.get('APNS_BUNDLE_ID'),
        os.environ.get('APNS_TEAM_ID'),
        os.environ.get('APNS_KEY_ID'),
        os.environ.get('APNS_AUTH_KEY_PATH'),
    ])


def _get_jwt() -> Optional[str]:
    """生成或复用 APNs JWT (ES256). 50 分钟 refresh 一次, 留 buffer 不撞 Apple 60min 上限."""
    with _jwt_lock:
        now = time.time()
        if _jwt_cache['token'] and _jwt_cache['expires_at'] - now > 60:
            return _jwt_cache['token']
        key_path = os.environ.get('APNS_AUTH_KEY_PATH')
        if not key_path or not os.path.exists(key_path):
            logger.error(f"APNs key path 不存在: {key_path}")
            return None
        try:
            with open(key_path, 'r') as f:
                secret = f.read()
            team_id = os.environ['APNS_TEAM_ID']
            key_id = os.environ['APNS_KEY_ID']
            token = jwt.encode(
                payload={'iss': team_id, 'iat': int(now)},
                key=secret,
                algorithm='ES256',
                headers={'kid': key_id, 'alg': 'ES256'},
            )
            _jwt_cache['token'] = token
            _jwt_cache['expires_at'] = now + 50 * 60
            return token
        except Exception as e:
            logger.error(f'APNs JWT 生成失败: {e}')
            return None


def _send_one(token: str, payload: dict, push_type: str = 'alert') -> bool:
    """同步发送 1 条 push. 返回 True=Apple 接受了."""
    jwt_token = _get_jwt()
    if not jwt_token:
        return False
    bundle_id = os.environ['APNS_BUNDLE_ID']
    use_sandbox = os.environ.get('APNS_USE_SANDBOX', '').lower() == 'true'
    host = 'api.sandbox.push.apple.com' if use_sandbox else 'api.push.apple.com'
    url = f'https://{host}/3/device/{token}'
    headers = {
        'authorization': f'bearer {jwt_token}',
        'apns-topic': bundle_id,
        'apns-push-type': push_type,
        'apns-priority': '10' if push_type == 'alert' else '5',
    }
    try:
        with httpx.Client(http2=True, timeout=10) as client:
            resp = client.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            return True
        print(f'[APNS] FAILED: status={resp.status_code} body={resp.text[:160]} token={token[:10]}', flush=True)
        logger.warning(f'APNs send failed: status={resp.status_code} body={resp.text[:200]} token={token[:10]}...')
        # 410 Gone: token 永久失效 (用户删 App / 长期未用), 清除我们这边的记录
        if resp.status_code == 410:
            try:
                from app.models.user import User
                from app import db
                User.query.filter_by(push_token=token).update({'push_token': None, 'push_platform': None})
                db.session.commit()
                logger.info(f'清除失效 push_token: {token[:10]}...')
            except Exception as ce:
                logger.warning(f'清除失效 token 失败: {ce}')
        return False
    except Exception as e:
        print(f'[APNS] EXCEPTION: {e}', flush=True)
        logger.error(f'APNs send exception: {e}')
        return False


def send_push(user_ids: Iterable[int], title: str, body: str,
              badge: Optional[int] = None, data: Optional[dict] = None) -> int:
    """给一组 user 发 push。自动跳过没注册 token 的用户和非 iOS 用户。

    Args:
        user_ids: 收件用户 id 集合
        title:    通知标题 (锁屏粗体那行)
        body:     通知正文
        badge:    App 图标右上角红点数字, None=不更新, 0=清除
        data:     附加 payload, App 收到推送时会拿到, 用于跳转

    Returns:
        实际发送成功的条数(被 Apple 接受 200 OK)。
    """
    if not _is_configured():
        logger.debug('APNs 未配置, 跳过 send_push')
        return 0
    try:
        from app.models.user import User
        users = User.query.filter(
            User.id.in_(list(user_ids)),
            User.push_token.isnot(None),
            User.push_platform == 'ios',
        ).all()
    except Exception as e:
        logger.error(f'查询 push 用户失败: {e}')
        return 0
    if not users:
        return 0

    aps = {'alert': {'title': title, 'body': body}, 'sound': 'default'}
    if badge is not None:
        aps['badge'] = max(0, int(badge))
    payload = {'aps': aps}
    if data:
        # 自定义 key 跟 aps 同级
        payload.update(data)

    success = 0
    for u in users:
        if _send_one(u.push_token, payload):
            success += 1
    # 用 print 保证可见(flask.log 没接 app logger)
    print(f'[APNS] send_push: {success}/{len(users)} ok, title="{title}"', flush=True)
    return success


def send_silent_push(user_ids: Iterable[int], data: dict) -> int:
    """静默 push - 不显示通知, 仅触发 App 后台拉数据 (常用于 badge 更新).

    需要 App 处理 background push delivery, 否则 iOS 可能 throttle。
    """
    if not _is_configured():
        return 0
    try:
        from app.models.user import User
        users = User.query.filter(
            User.id.in_(list(user_ids)),
            User.push_token.isnot(None),
            User.push_platform == 'ios',
        ).all()
    except Exception as e:
        logger.error(f'查询 push 用户失败: {e}')
        return 0
    payload = {'aps': {'content-available': 1}, **data}
    success = 0
    for u in users:
        if _send_one(u.push_token, payload, push_type='background'):
            success += 1
    return success
