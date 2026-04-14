"""钉钉日程 → PMA WorkItem 单向拉取。

- 每小时由 scheduled_tasks 触发。
- 对每个有映射的用户，拉取 [过去30天, 未来90天] 窗口内的日程。
- upsert 到 WorkItem：sync_source='dingtalk'，用 dingtalk_event_id 匹配。
- 窗口内 PMA 有、钉钉没的条目 → 软删除（is_deleted=True）。

设计要点：
1. 不创建/更新/删除钉钉侧数据，纯读取。
2. WorkItem.sync_source='dingtalk' 标识拉取来源，前端据此设为只读。
3. 钉钉时间直接转 Asia/Shanghai 的 naive datetime（与项目惯例一致）。
"""
import logging
from datetime import datetime, date, time as _time, timedelta
from typing import Dict, List, Optional, Set, Tuple
from zoneinfo import ZoneInfo

from app.services.dingtalk.client import DingTalkError, get_client
from app.services.dingtalk.config import is_dingtalk_enabled

logger = logging.getLogger(__name__)

TIMEZONE = 'Asia/Shanghai'
DEFAULT_CALENDAR_ID = 'primary'
WINDOW_PAST_DAYS = 30
WINDOW_FUTURE_DAYS = 90
PAGE_SIZE = 50


def _now() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)


def _iso_with_tz(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(TIMEZONE))
    return dt.isoformat(timespec='seconds')


def fetch_events(userid: str, time_min: datetime, time_max: datetime,
                 calendar_id: str = DEFAULT_CALENDAR_ID, client=None) -> List[dict]:
    """拉取一个用户在 [time_min, time_max) 窗口内的全部事件（自动翻页）。"""
    cli = client or get_client()
    path = f'/v1.0/calendar/users/{userid}/calendars/{calendar_id}/events'
    all_events: List[dict] = []
    next_token: Optional[str] = None
    while True:
        params = {
            'timeMin': _iso_with_tz(time_min),
            'timeMax': _iso_with_tz(time_max),
            'maxResults': PAGE_SIZE,
        }
        if next_token:
            params['nextToken'] = next_token
        data = cli.request_new('GET', path, params=params)
        events = data.get('events', []) or []
        all_events.extend(events)
        next_token = data.get('nextToken')
        if not next_token:
            break
    return all_events


def _parse_event_time(t: dict) -> Tuple[Optional[date], Optional[_time], bool]:
    """解析钉钉时间字段 → (date, time_or_none, is_allday_hint)。

    钉钉返回形式:
      - 全天: {"date": "2026-04-14"}
      - 带时间: {"dateTime": "2026-04-14T10:00:00+08:00", "timeZone": "Asia/Shanghai"}
    """
    if not t:
        return None, None, False
    if 'date' in t and t['date']:
        return date.fromisoformat(t['date']), None, True
    if 'dateTime' in t and t['dateTime']:
        dt = datetime.fromisoformat(t['dateTime'])
        if dt.tzinfo is not None:
            dt = dt.astimezone(ZoneInfo(TIMEZONE)).replace(tzinfo=None)
        return dt.date(), dt.time().replace(microsecond=0), False
    return None, None, False


def _event_to_workitem_fields(evt: dict, owner_id: int) -> Optional[dict]:
    """将钉钉事件字典映射到 WorkItem 字段字典。不匹配/无效时返回 None。"""
    start = evt.get('start') or {}
    end = evt.get('end') or {}
    start_date, start_time, start_allday = _parse_event_time(start)
    if not start_date:
        return None
    end_date, end_time, _ = _parse_event_time(end)
    is_all_day = bool(evt.get('isAllDay')) or start_allday

    # 钉钉全天事件 end 是 exclusive，我们内部 end_date 是 inclusive
    if is_all_day and end_date and end_date > start_date:
        end_date = end_date - timedelta(days=1)
    if end_date is None:
        end_date = start_date

    return {
        'title': (evt.get('summary') or '(无标题)')[:200],
        'description': evt.get('description') or '',
        'planned_date': start_date,
        'end_date': end_date if end_date != start_date else None,
        'start_time': None if is_all_day else start_time,
        'end_time': None if is_all_day else end_time,
        'is_all_day': is_all_day,
        'owner_id': owner_id,
        'work_type': 'other',
        'status': 'planned',
        'sync_source': 'dingtalk',
        'dingtalk_event_id': evt.get('id'),
    }


def _ensure_unionid(mapping, client) -> Optional[str]:
    """保证 mapping.dingtalk_unionid 有值，必要时通过旧 API 回填。"""
    from app import db
    if mapping.dingtalk_unionid:
        return mapping.dingtalk_unionid
    try:
        data = client.request_old(
            'POST', '/topapi/v2/user/get',
            json_body={'userid': mapping.dingtalk_userid},
        )
        result = data.get('result') or {}
        unionid = result.get('unionid')
        if unionid:
            mapping.dingtalk_unionid = unionid
            db.session.commit()
            return unionid
    except DingTalkError as e:
        logger.warning('回填 unionid 失败 userid=%s err=%s', mapping.dingtalk_userid, e)
    return None


def pull_user_events(mapping, time_min: datetime, time_max: datetime, client=None) -> Dict[str, int]:
    """拉取单个用户的日程并 upsert。返回统计。"""
    from app import db
    from app.models.worklog import WorkItem

    stats = {'created': 0, 'updated': 0, 'soft_deleted': 0, 'skipped': 0}
    cli = client or get_client()
    unionid = _ensure_unionid(mapping, cli)
    if not unionid:
        logger.warning('跳过拉取：无 unionid userid=%s', mapping.dingtalk_userid)
        return stats
    try:
        events = fetch_events(unionid, time_min, time_max, client=cli)
    except DingTalkError as e:
        logger.warning('拉取钉钉日程失败 userid=%s err=%s', mapping.dingtalk_userid, e)
        return stats

    fetched_event_ids: Set[str] = set()
    for evt in events:
        if evt.get('status') == 'cancelled':
            continue
        fields = _event_to_workitem_fields(evt, mapping.pma_user_id)
        if not fields or not fields.get('dingtalk_event_id'):
            stats['skipped'] += 1
            continue
        fetched_event_ids.add(fields['dingtalk_event_id'])

        wi = WorkItem.query.filter_by(dingtalk_event_id=fields['dingtalk_event_id']).first()
        if wi:
            changed = False
            for k, v in fields.items():
                if getattr(wi, k) != v:
                    setattr(wi, k, v)
                    changed = True
            # 重新出现在钉钉 → 取消软删除
            if wi.is_deleted:
                wi.is_deleted = False
                changed = True
            if changed:
                wi.dingtalk_synced_at = _now()
                stats['updated'] += 1
        else:
            wi = WorkItem(**fields)
            wi.dingtalk_synced_at = _now()
            db.session.add(wi)
            stats['created'] += 1

    # 软删除：窗口内 PMA 有、本次拉取没有的钉钉来源条目
    window_min_date = time_min.date()
    window_max_date = time_max.date()
    orphans = WorkItem.query.filter(
        WorkItem.owner_id == mapping.pma_user_id,
        WorkItem.sync_source == 'dingtalk',
        WorkItem.is_deleted == False,
        WorkItem.planned_date >= window_min_date,
        WorkItem.planned_date < window_max_date,
    ).all()
    for wi in orphans:
        if wi.dingtalk_event_id and wi.dingtalk_event_id not in fetched_event_ids:
            wi.is_deleted = True
            wi.dingtalk_synced_at = _now()
            stats['soft_deleted'] += 1

    db.session.commit()
    return stats


def pull_all_users(app=None) -> Dict[str, int]:
    """遍历所有活跃映射的用户，拉取日程。主入口。"""
    from app.models.dingtalk import DingtalkUserMapping

    total = {'users': 0, 'created': 0, 'updated': 0, 'soft_deleted': 0, 'skipped': 0, 'failed': 0}
    if not is_dingtalk_enabled():
        logger.info('钉钉未启用，跳过拉取')
        return total

    client = get_client()
    now = _now()
    time_min = now - timedelta(days=WINDOW_PAST_DAYS)
    time_max = now + timedelta(days=WINDOW_FUTURE_DAYS)

    mappings = DingtalkUserMapping.query.filter_by(is_active=True).all()
    for m in mappings:
        total['users'] += 1
        try:
            s = pull_user_events(m, time_min, time_max, client=client)
            for k in ('created', 'updated', 'soft_deleted', 'skipped'):
                total[k] += s.get(k, 0)
        except Exception as e:
            logger.error('拉取用户 %s 日程异常: %s', m.dingtalk_userid, e, exc_info=True)
            total['failed'] += 1
    logger.info('钉钉日程拉取完成: %s', total)
    return total
