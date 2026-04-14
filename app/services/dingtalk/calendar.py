"""钉钉日程 CRUD 封装 — WorkItem ↔ 钉钉日程的字段映射也在这里。"""
import logging
from datetime import datetime, date, time as _time, timedelta
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from app.services.dingtalk.client import DingTalkClient, DingTalkError, get_client

logger = logging.getLogger(__name__)

TIMEZONE = 'Asia/Shanghai'
DEFAULT_CALENDAR_ID = 'primary'


def build_event_payload(work_item) -> Dict[str, Any]:
    """WorkItem → 钉钉日程 JSON。

    全天事件: start/end 用 date；带时间: start/end 用 dateTime + timeZone。
    钉钉全天事件 end 是 exclusive（FullCalendar 同语义）。
    """
    title = work_item.title or '(无标题)'
    description = work_item.description or ''
    if work_item.is_business_trip:
        description = f'[出差] {description}'.strip()

    payload: Dict[str, Any] = {
        'summary': title,
        'description': description,
        'isAllDay': bool(work_item.is_all_day),
    }

    start_date = work_item.planned_date
    end_date = work_item.end_date or start_date

    if work_item.is_all_day or not work_item.start_time:
        payload['start'] = {'date': start_date.isoformat()}
        payload['end'] = {'date': (end_date + timedelta(days=1)).isoformat()}
    else:
        start_dt = datetime.combine(start_date, work_item.start_time)
        end_dt = datetime.combine(end_date, work_item.end_time or _time(hour=23, minute=59))
        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(hours=1)
        payload['start'] = {'dateTime': _to_iso(start_dt), 'timeZone': TIMEZONE}
        payload['end'] = {'dateTime': _to_iso(end_dt), 'timeZone': TIMEZONE}

    extras = []
    if work_item.get_type_label():
        extras.append(f'类型: {work_item.get_type_label()}')
    if work_item.project and getattr(work_item.project, 'project_name', None):
        extras.append(f'项目: {work_item.project.project_name}')
    if work_item.customer and getattr(work_item.customer, 'company_name', None):
        extras.append(f'客户: {work_item.customer.company_name}')
    if extras:
        payload['description'] = ('\n'.join(extras) + '\n\n' + (payload['description'] or '')).strip()

    return payload


def create_event(userid: str, work_item, client: Optional[DingTalkClient] = None,
                 calendar_id: str = DEFAULT_CALENDAR_ID) -> str:
    """在指定用户的日历下创建事件，返回钉钉 event_id。"""
    cli = client or get_client()
    path = f'/v1.0/calendar/users/{userid}/calendars/{calendar_id}/events'
    payload = build_event_payload(work_item)
    data = cli.request_new('POST', path, json_body=payload)
    event_id = data.get('id')
    if not event_id:
        raise DingTalkError(f'钉钉未返回 event_id: {data}', payload=data)
    logger.info('钉钉日程创建成功 work_item=%s event=%s', work_item.id, event_id)
    return event_id


def update_event(userid: str, dingtalk_event_id: str, work_item,
                 client: Optional[DingTalkClient] = None,
                 calendar_id: str = DEFAULT_CALENDAR_ID) -> None:
    cli = client or get_client()
    path = f'/v1.0/calendar/users/{userid}/calendars/{calendar_id}/events/{dingtalk_event_id}'
    payload = build_event_payload(work_item)
    cli.request_new('PUT', path, json_body=payload)
    logger.info('钉钉日程更新成功 work_item=%s event=%s', work_item.id, dingtalk_event_id)


def delete_event(userid: str, dingtalk_event_id: str,
                 client: Optional[DingTalkClient] = None,
                 calendar_id: str = DEFAULT_CALENDAR_ID) -> None:
    cli = client or get_client()
    path = f'/v1.0/calendar/users/{userid}/calendars/{calendar_id}/events/{dingtalk_event_id}'
    try:
        cli.request_new('DELETE', path)
    except DingTalkError as e:
        if e.errcode == 404:
            logger.info('钉钉事件已不存在，视为删除成功 event=%s', dingtalk_event_id)
            return
        raise
    logger.info('钉钉日程删除成功 event=%s', dingtalk_event_id)


def _to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(TIMEZONE))
    return dt.isoformat(timespec='seconds')
