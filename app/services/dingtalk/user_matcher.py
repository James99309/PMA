"""PMA 用户 ↔ 钉钉用户的多层匹配逻辑。

匹配优先级（精确匹配，不模糊）:
  Layer 1: 手机号
  Layer 2: 邮箱（PMA.email vs 钉钉 email/org_email 任一）
  Layer 3: 真实姓名（PMA.real_name vs 钉钉 name）

匹配不到 → 自动创建 PMA User（_is_active=False,等管理员手动激活并设权限）。
"""
import logging
import re
import secrets
from datetime import datetime
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

from app import db
from app.models.dingtalk import DingtalkUserMapping
from app.models.user import User
from app.services.dingtalk.client import DingTalkError, get_client

logger = logging.getLogger(__name__)

MOBILE_RE = re.compile(r'(\d{11})')


def _now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


def normalize_mobile(phone: str) -> Optional[str]:
    if not phone:
        return None
    m = MOBILE_RE.search(phone.replace(' ', '').replace('-', ''))
    return m.group(1) if m else None


def fetch_dingtalk_user(userid: str, client=None) -> Optional[dict]:
    """钉钉 /topapi/v2/user/get → 返回 result dict 或 None（用户不存在）。"""
    cli = client or get_client()
    try:
        data = cli.request_old('POST', '/topapi/v2/user/get', json_body={'userid': userid})
    except DingTalkError as e:
        if e.errcode in (60121, 60011):
            return None
        raise
    return data.get('result') or None


def lookup_userid_by_mobile(mobile: str, client=None) -> Optional[str]:
    cli = client or get_client()
    try:
        data = cli.request_old('POST', '/topapi/v2/user/getbymobile', json_body={'mobile': mobile})
    except DingTalkError as e:
        if e.errcode == 60121:
            return None
        raise
    return (data.get('result') or {}).get('userid')


def find_pma_user_for_dingtalk(dt_user: dict) -> Tuple[Optional[User], Optional[str]]:
    """根据钉钉用户信息找匹配的 PMA 用户。返回 (user, matched_by) 或 (None, None)。"""
    dt_mobile = normalize_mobile(dt_user.get('mobile'))
    dt_email = (dt_user.get('email') or dt_user.get('org_email') or '').strip().lower()
    dt_name = (dt_user.get('name') or '').strip()

    # Layer 1: 手机号
    if dt_mobile:
        for u in User.query.filter(User._is_active == True).all():  # noqa: E712
            if normalize_mobile(u.phone) == dt_mobile:
                return u, 'mobile'

    # Layer 2: 邮箱
    if dt_email:
        u = User.query.filter(
            User._is_active == True,  # noqa: E712
            db.func.lower(User.email) == dt_email,
        ).first()
        if u:
            return u, 'email'

    # Layer 3: 真实姓名精确
    if dt_name:
        u = User.query.filter(
            User._is_active == True,  # noqa: E712
            User.real_name == dt_name,
        ).first()
        if u:
            return u, 'name'

    return None, None


def upsert_mapping(pma_user_id: int, dingtalk_userid: str, matched_by: str,
                   dingtalk_unionid: str = None, note: str = None) -> DingtalkUserMapping:
    existing = DingtalkUserMapping.query.filter_by(pma_user_id=pma_user_id).first()
    now = _now()
    if existing:
        existing.dingtalk_userid = dingtalk_userid
        existing.matched_by = matched_by
        existing.is_active = True
        existing.last_verified_at = now
        if dingtalk_unionid:
            existing.dingtalk_unionid = dingtalk_unionid
        if note:
            existing.note = note
        db.session.commit()
        return existing
    m = DingtalkUserMapping(
        pma_user_id=pma_user_id,
        dingtalk_userid=dingtalk_userid,
        dingtalk_unionid=dingtalk_unionid,
        matched_by=matched_by,
        note=note,
        is_active=True,
        last_verified_at=now,
    )
    db.session.add(m)
    db.session.commit()
    return m


def _generate_unique_username(preferred: str) -> str:
    """基于首选用户名(邮箱前缀)生成唯一 username,冲突则追加数字后缀。"""
    base = (preferred or '').strip().lower()
    if not base:
        base = 'user'
    candidate = base
    i = 2
    while User.query.filter(db.func.lower(User.username) == candidate).first():
        candidate = f'{base}{i}'
        i += 1
        if i > 999:  # 兜底,避免死循环
            candidate = f'{base}{secrets.token_hex(3)}'
            break
    return candidate


def create_pma_user_from_dingtalk(dt_user: dict) -> Optional[User]:
    """根据钉钉用户信息创建 PMA User（_is_active=False,等管理员激活）。

    - username: 邮箱前缀(lihuawei),冲突加数字后缀
    - real_name / email / phone: 从钉钉取
    - department / role: 留默认,由管理员在 PMA 手动设置
    - password: 随机,用户首次登录前需要管理员重置或走邀请流程

    若没有邮箱(无法生成合理 username),返回 None。
    """
    dt_email = (dt_user.get('email') or dt_user.get('org_email') or '').strip()
    dt_name = (dt_user.get('name') or '').strip()
    dt_mobile = normalize_mobile(dt_user.get('mobile'))

    if not dt_email or '@' not in dt_email:
        logger.warning('无法创建 PMA User:钉钉用户无邮箱 userid=%s name=%s',
                       dt_user.get('userid'), dt_name)
        return None

    # 邮箱冲突(同邮箱的 PMA 用户已存在,理论上应该在 matcher 已经匹配到,走到这说明是 race)
    existing_email = User.query.filter(db.func.lower(User.email) == dt_email.lower()).first()
    if existing_email:
        logger.warning('无法创建 PMA User:邮箱已存在 email=%s pma_user_id=%s',
                       dt_email, existing_email.id)
        return None

    preferred_username = dt_email.split('@', 1)[0]
    username = _generate_unique_username(preferred_username)

    user = User(
        username=username,
        real_name=dt_name or None,
        email=dt_email,
        phone=dt_mobile,
        role='user',
        is_profile_complete=False,
    )
    user._is_active = False  # 等管理员配完权限再激活
    user.set_password(secrets.token_urlsafe(16))  # 随机密码,用户不应直接使用

    db.session.add(user)
    db.session.flush()  # 拿到 user.id,但不 commit(由 upsert_mapping commit)
    logger.info('已创建 PMA User(未激活) username=%s real_name=%s email=%s',
                username, dt_name, dt_email)
    return user


def match_and_bind(userid: str, client=None) -> Tuple[Optional[DingtalkUserMapping], str]:
    """根据钉钉 userid 拉取信息 → 匹配 PMA → 建/更新映射。

    匹配不到 → 自动创建 PMA User(未激活)+ 建 mapping。

    返回 (mapping, status) — status:
      'created'      / 'updated'  : 匹配到已有 PMA 用户并绑定
      'created_user' : 未匹配,自动创建了新 PMA 用户并绑定
      'no_match'     : 未匹配且无法自动创建(如钉钉用户无邮箱)
      'not_found'    : 钉钉侧查不到该 userid
    """
    dt_user = fetch_dingtalk_user(userid, client=client)
    if not dt_user:
        return None, 'not_found'

    pma_user, matched_by = find_pma_user_for_dingtalk(dt_user)
    if pma_user:
        existing = DingtalkUserMapping.query.filter_by(pma_user_id=pma_user.id).first()
        mapping = upsert_mapping(
            pma_user_id=pma_user.id,
            dingtalk_userid=userid,
            matched_by=matched_by,
            dingtalk_unionid=dt_user.get('unionid'),
        )
        return mapping, ('updated' if existing else 'created')

    # 未匹配:自动创建新 PMA User
    new_user = create_pma_user_from_dingtalk(dt_user)
    if not new_user:
        return None, 'no_match'

    mapping = upsert_mapping(
        pma_user_id=new_user.id,
        dingtalk_userid=userid,
        matched_by='auto_created',
        dingtalk_unionid=dt_user.get('unionid'),
        note='钉钉新员工自动创建,待管理员激活并配权限',
    )
    return mapping, 'created_user'


def deactivate_mapping(userid: str) -> bool:
    """钉钉用户离职 → 停用 mapping,同时把对应 PMA User 设为未激活(保留所有历史数据)。"""
    m = DingtalkUserMapping.query.filter_by(dingtalk_userid=userid).first()
    if not m:
        return False
    ts = _now().isoformat(timespec='seconds')
    m.is_active = False
    m.note = (m.note or '') + f' [{ts} 钉钉离职自动停用]'

    pma_user = User.query.get(m.pma_user_id) if m.pma_user_id else None
    if pma_user and pma_user._is_active:
        pma_user._is_active = False
        logger.info('已停用 PMA User username=%s (钉钉离职 userid=%s)',
                    pma_user.username, userid)

    db.session.commit()
    logger.info('已停用 mapping userid=%s pma_user_id=%s', userid, m.pma_user_id)
    return True
