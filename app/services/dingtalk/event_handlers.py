"""钉钉企业事件回调处理器。

支持的事件:
- check_url      : 首次配置回调时验证（直接返回 success）
- user_add_org   : 新员工入职 → 触发匹配建 mapping
- user_modify_org: 员工信息变更 → 忽略（手机/姓名变了 userid 没变，不需处理）
- user_leave_org : 离职 → 标记 mapping 失活
- 其他事件       : 忽略并记录
"""
import json
import logging
from typing import List

from app.services.dingtalk.user_matcher import deactivate_mapping, match_and_bind

logger = logging.getLogger(__name__)


def handle_event(event_type: str, payload: dict) -> None:
    """事件总入口。在后台线程调用，外层已保证 app_context。"""
    if event_type == 'check_url':
        logger.info('钉钉回调验证事件 check_url')
        return

    if event_type == 'user_add_org':
        userids = _extract_userids(payload)
        logger.info('user_add_org 收到 %d 个新用户: %s', len(userids), userids)
        for uid in userids:
            try:
                mapping, status = match_and_bind(uid)
                logger.info('  [%s] %s', uid, status)
            except Exception as e:
                logger.error('  [%s] 匹配失败: %s', uid, e)
        return

    if event_type == 'user_leave_org':
        userids = _extract_userids(payload)
        logger.info('user_leave_org 收到 %d 个离职用户: %s', len(userids), userids)
        for uid in userids:
            try:
                deactivate_mapping(uid)
            except Exception as e:
                logger.error('  [%s] 停用失败: %s', uid, e)
        return

    if event_type == 'user_modify_org':
        logger.debug('忽略 user_modify_org（userid 不变，不需同步）payload=%s', payload)
        return

    logger.info('收到未处理的钉钉事件 type=%s payload=%s', event_type, payload)


def _extract_userids(payload: dict) -> List[str]:
    """钉钉事件 payload 里 userid 字段可能是 'UserId' / 'userid'，且通常是字符串数组或逗号分隔字符串。"""
    raw = payload.get('UserId') or payload.get('userid') or payload.get('userId') or []
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
        return [s.strip() for s in raw.split(',') if s.strip()]
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return []
