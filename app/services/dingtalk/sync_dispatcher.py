"""WorkItem → 钉钉日程的异步同步派发器。

- SQLAlchemy 事件监听器：在 WorkItem 变更时向 dingtalk_sync_queue 入队（同事务）。
- 后台工作线程：定时从队列取任务，调用钉钉 API 执行，失败重试（指数退避）。

设计要点：
1. 监听器用 connection 直接 INSERT，保证和业务事务一致（业务回滚时队列也回滚）。
2. 监听器**不调用**钉钉 API（避免慢 HTTP 阻塞 Web 请求）。
3. 后台 worker 单例，每 30 秒扫描一次 pending + next_retry_at<=now 的任务。
4. 重试 3 次后 status=failed，不再自动重试（需要人工/管理页触发）。
"""
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import event

from app.services.dingtalk.config import is_dingtalk_enabled
from app.services.dingtalk.client import DingTalkError, get_client
from app.services.dingtalk import calendar as dt_calendar

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = [60, 300, 1800]   # 1min, 5min, 30min
POLL_INTERVAL_SECONDS = 30
BATCH_SIZE = 20


def _now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


# ============ 入队 ============

def _enqueue_via_connection(connection, work_item_id, action, dingtalk_event_id=None,
                            dingtalk_userid=None, payload_snapshot=None):
    from app.models.dingtalk import DingtalkSyncQueue
    now = _now()
    connection.execute(
        DingtalkSyncQueue.__table__.insert().values(
            work_item_id=work_item_id,
            action=action,
            dingtalk_event_id=dingtalk_event_id,
            dingtalk_userid=dingtalk_userid,
            payload_snapshot=payload_snapshot,
            status='pending',
            attempts=0,
            created_at=now,
            updated_at=now,
            next_retry_at=now,
        )
    )


def _lookup_userid(connection, pma_user_id) -> Optional[str]:
    from app.models.dingtalk import DingtalkUserMapping
    row = connection.execute(
        DingtalkUserMapping.__table__.select()
        .where(DingtalkUserMapping.__table__.c.pma_user_id == pma_user_id)
        .where(DingtalkUserMapping.__table__.c.is_active.is_(True))
    ).first()
    return row.dingtalk_userid if row else None


# ============ SQLAlchemy 监听器 ============

def _on_work_item_after_insert(mapper, connection, target):
    if not is_dingtalk_enabled():
        return
    if target.sync_source == 'dingtalk':
        return
    if target.is_deleted or target.is_invalidated:
        return
    userid = _lookup_userid(connection, target.owner_id)
    if not userid:
        logger.debug('跳过入队（用户未映射钉钉）work_item=%s owner=%s', target.id, target.owner_id)
        return
    _enqueue_via_connection(connection, target.id, 'create', dingtalk_userid=userid)


def _on_work_item_after_update(mapper, connection, target):
    if not is_dingtalk_enabled():
        return
    if target.sync_source == 'dingtalk':
        return
    userid = _lookup_userid(connection, target.owner_id)
    if not userid:
        return

    # 软删除/作废 → 如果之前推过钉钉，要删
    if (target.is_deleted or target.is_invalidated) and target.dingtalk_event_id:
        _enqueue_via_connection(connection, target.id, 'delete',
                                dingtalk_event_id=target.dingtalk_event_id,
                                dingtalk_userid=userid)
        return
    if target.is_deleted or target.is_invalidated:
        return

    # 正常更新：有 event_id 就 update，没有就 create（可能是首次映射成功后的老数据）
    action = 'update' if target.dingtalk_event_id else 'create'
    _enqueue_via_connection(connection, target.id, action,
                            dingtalk_event_id=target.dingtalk_event_id,
                            dingtalk_userid=userid)


def _on_work_item_after_delete(mapper, connection, target):
    if not is_dingtalk_enabled():
        return
    if target.sync_source == 'dingtalk':
        return
    if not target.dingtalk_event_id:
        return
    userid = _lookup_userid(connection, target.owner_id)
    if not userid:
        return
    _enqueue_via_connection(connection, None, 'delete',
                            dingtalk_event_id=target.dingtalk_event_id,
                            dingtalk_userid=userid,
                            payload_snapshot=json.dumps({'deleted_work_item_id': target.id}))


def register_model_listeners():
    """在 app 启动时调用一次。重复调用安全。"""
    from app.models.worklog import WorkItem
    if getattr(register_model_listeners, '_registered', False):
        return
    event.listen(WorkItem, 'after_insert', _on_work_item_after_insert)
    event.listen(WorkItem, 'after_update', _on_work_item_after_update)
    event.listen(WorkItem, 'after_delete', _on_work_item_after_delete)
    register_model_listeners._registered = True
    logger.info('钉钉同步监听器已注册到 WorkItem')


# ============ 后台 worker ============

def process_queue_once(app, limit: int = BATCH_SIZE) -> dict:
    """处理一批待同步任务，返回统计。通常由后台线程调用；也可手动调用用于单元测试。"""
    from app import db
    from app.models.dingtalk import DingtalkSyncQueue
    from app.models.worklog import WorkItem

    stats = {'success': 0, 'failed': 0, 'retry': 0, 'skipped': 0}

    with app.app_context():
        if not is_dingtalk_enabled():
            return stats

        now = _now()
        pending = (
            DingtalkSyncQueue.query
            .filter(DingtalkSyncQueue.status.in_(['pending', 'running']))
            .filter((DingtalkSyncQueue.next_retry_at == None) | (DingtalkSyncQueue.next_retry_at <= now))  # noqa: E711
            .order_by(DingtalkSyncQueue.created_at.asc())
            .limit(limit)
            .all()
        )
        if not pending:
            return stats

        client = get_client()

        for task in pending:
            task.status = 'running'
            task.attempts += 1
            task.updated_at = _now()
            db.session.commit()

            try:
                _execute_task(client, task)
                task.status = 'success'
                task.last_error = None
                task.updated_at = _now()
                db.session.commit()
                stats['success'] += 1
            except Exception as e:
                err_msg = f'{type(e).__name__}: {e}'
                logger.warning('钉钉同步任务失败 task=%s attempts=%s err=%s',
                               task.id, task.attempts, err_msg)
                task.last_error = err_msg
                task.updated_at = _now()
                if task.attempts >= MAX_ATTEMPTS:
                    task.status = 'failed'
                    stats['failed'] += 1
                else:
                    backoff = RETRY_BACKOFF_SECONDS[min(task.attempts - 1, len(RETRY_BACKOFF_SECONDS) - 1)]
                    task.status = 'pending'
                    task.next_retry_at = _now() + timedelta(seconds=backoff)
                    stats['retry'] += 1
                db.session.commit()

    return stats


def _execute_task(client, task):
    """执行单个同步任务，成功会回写 WorkItem 的 dingtalk_event_id。"""
    from app import db
    from app.models.worklog import WorkItem

    if task.action == 'delete':
        if not (task.dingtalk_event_id and task.dingtalk_userid):
            raise ValueError('delete 任务缺少 event_id/userid')
        dt_calendar.delete_event(task.dingtalk_userid, task.dingtalk_event_id, client=client)
        return

    # create / update 需要 WorkItem 存在且未删除
    if not task.work_item_id:
        raise ValueError(f'{task.action} 任务缺少 work_item_id')
    wi = WorkItem.query.get(task.work_item_id)
    if not wi or wi.is_deleted:
        raise ValueError('WorkItem 已删除或不存在')
    if not task.dingtalk_userid:
        raise ValueError('任务缺少 dingtalk_userid')

    if task.action == 'create' or not wi.dingtalk_event_id:
        event_id = dt_calendar.create_event(task.dingtalk_userid, wi, client=client)
        wi.dingtalk_event_id = event_id
        wi.dingtalk_synced_at = _now()
        wi.sync_source = wi.sync_source or 'pma'
        db.session.commit()
    elif task.action == 'update':
        dt_calendar.update_event(task.dingtalk_userid, wi.dingtalk_event_id, wi, client=client)
        wi.dingtalk_synced_at = _now()
        db.session.commit()


# ============ 后台线程 ============

_worker_running = False
_worker_thread: Optional[threading.Thread] = None
_stop_flag = threading.Event()


def start_background_worker(app):
    """启动后台工作线程。重复调用安全。"""
    global _worker_running, _worker_thread
    if _worker_running:
        return
    if not is_dingtalk_enabled():
        logger.info('钉钉集成未启用，跳过后台 worker')
        return

    _stop_flag.clear()
    _worker_running = True

    def _loop():
        logger.info('钉钉同步后台 worker 启动（间隔 %ss）', POLL_INTERVAL_SECONDS)
        while not _stop_flag.is_set():
            try:
                stats = process_queue_once(app)
                if any(stats.values()):
                    logger.info('钉钉同步批次: %s', stats)
            except Exception as e:
                logger.error('钉钉同步后台循环异常: %s', e, exc_info=True)
            _stop_flag.wait(POLL_INTERVAL_SECONDS)
        logger.info('钉钉同步后台 worker 退出')

    _worker_thread = threading.Thread(target=_loop, name='dingtalk-sync-worker', daemon=True)
    _worker_thread.start()


def stop_background_worker():
    global _worker_running
    _stop_flag.set()
    _worker_running = False
