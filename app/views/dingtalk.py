# -*- coding: utf-8 -*-
"""钉钉集成 - 同步队列管理页 + 事件回调入口。"""
import json
import logging
import threading
from datetime import datetime

from flask import Blueprint, current_app, render_template, request, jsonify, abort
from flask_login import login_required

from app import db
from app.decorators import admin_required
from app.models.dingtalk import DingtalkSyncQueue, DingtalkUserMapping
from app.models.worklog import WorkItem
from app.services.dingtalk.config import DingTalkConfig, is_dingtalk_enabled

logger = logging.getLogger(__name__)

dingtalk_bp = Blueprint('dingtalk', __name__, url_prefix='/admin/dingtalk')

# 公开回调蓝图（钉钉服务器调用，无认证、CSRF 豁免）
dingtalk_callback_bp = Blueprint('dingtalk_callback', __name__, url_prefix='/api/dingtalk')


@dingtalk_bp.route('/sync-queue')
@login_required
@admin_required
def sync_queue():
    status = request.args.get('status', 'all')
    q = DingtalkSyncQueue.query
    if status in ('pending', 'running', 'success', 'failed'):
        q = q.filter(DingtalkSyncQueue.status == status)
    items = q.order_by(DingtalkSyncQueue.created_at.desc()).limit(200).all()

    stats = dict(
        db.session.query(DingtalkSyncQueue.status, db.func.count(DingtalkSyncQueue.id))
        .group_by(DingtalkSyncQueue.status)
        .all()
    )
    mapping_count = DingtalkUserMapping.query.filter_by(is_active=True).count()

    return render_template(
        'dingtalk/tw_sync_queue.html',
        items=items,
        stats=stats,
        mapping_count=mapping_count,
        enabled=is_dingtalk_enabled(),
        current_status=status,
    )


@dingtalk_bp.route('/api/retry/<int:task_id>', methods=['POST'])
@login_required
@admin_required
def retry_task(task_id):
    task = DingtalkSyncQueue.query.get_or_404(task_id)
    task.status = 'pending'
    task.attempts = 0
    task.last_error = None
    task.next_retry_at = datetime.now()
    db.session.commit()
    return jsonify(ok=True)


@dingtalk_bp.route('/api/run-now', methods=['POST'])
@login_required
@admin_required
def run_now():
    """立即从钉钉拉取一次日程（手动触发，平时由每小时定时任务跑）。"""
    if not is_dingtalk_enabled():
        return jsonify(ok=False, error='钉钉集成未启用'), 400
    from app.services.dingtalk.calendar_pull import pull_all_users
    stats = pull_all_users()
    return jsonify(ok=True, stats=stats)


@dingtalk_callback_bp.route('/callback', methods=['POST', 'GET'])
def dingtalk_callback():
    """钉钉企业事件回调入口。

    钉钉首次配置时会推一个 check_url 事件验证；之后正常推 user_add_org/user_leave_org。
    必须 5 秒内返回加密 success，否则钉钉重试。
    """
    from app.services.dingtalk import callback_crypto

    cfg = DingTalkConfig.from_env()
    if not cfg.has_callback():
        return jsonify(error='钉钉回调未配置'), 503

    signature = request.args.get('msg_signature') or request.args.get('signature', '')
    timestamp = request.args.get('timestamp', '')
    nonce = request.args.get('nonce', '')

    try:
        body = request.get_json(silent=True) or {}
        encrypted = body.get('encrypt', '')
        if not encrypted:
            return jsonify(error='缺少 encrypt 字段'), 400

        # 新版事件订阅(自建应用)加密标识用 AppKey；旧版 Corp 回调用 corp_id
        # 解密时放宽不校验，写入日志即可；加密返回 success 时用 AppKey（新版规范）
        plaintext = callback_crypto.verify_and_decrypt(
            cfg.callback_token, cfg.callback_aes_key,
            signature, timestamp, nonce, encrypted,
            expected_app_key=None,
        )
        event = json.loads(plaintext)
        event_type = event.get('EventType') or event.get('eventType') or 'unknown'
        logger.info('钉钉事件 type=%s', event_type)

        # 异步处理，立即返回 success 给钉钉（5s 约束）
        if event_type != 'check_url':
            app = current_app._get_current_object()
            threading.Thread(
                target=_handle_event_in_background,
                args=(app, event_type, event),
                daemon=True,
                name=f'dingtalk-evt-{event_type}',
            ).start()

        resp = callback_crypto.build_success_response(
            cfg.callback_token, cfg.callback_aes_key, cfg.app_key, timestamp, nonce,
        )
        return jsonify(resp)
    except callback_crypto.DingTalkCryptoError as e:
        logger.warning('钉钉回调验签/解密失败: %s', e)
        return jsonify(error=str(e)), 400
    except Exception as e:
        logger.exception('钉钉回调处理异常')
        return jsonify(error=str(e)), 500


def _handle_event_in_background(app, event_type, payload):
    from app.services.dingtalk.event_handlers import handle_event
    with app.app_context():
        try:
            handle_event(event_type, payload)
        except Exception as e:
            logger.exception('钉钉事件后台处理失败 type=%s err=%s', event_type, e)


@dingtalk_bp.route('/api/mappings')
@login_required
@admin_required
def list_mappings():
    mappings = (
        db.session.query(DingtalkUserMapping)
        .order_by(DingtalkUserMapping.created_at.desc())
        .all()
    )
    return jsonify([
        {
            'id': m.id,
            'pma_user_id': m.pma_user_id,
            'pma_user_name': m.pma_user.real_name or m.pma_user.username if m.pma_user else None,
            'dingtalk_userid': m.dingtalk_userid,
            'matched_by': m.matched_by,
            'is_active': m.is_active,
            'created_at': m.created_at.isoformat() if m.created_at else None,
        }
        for m in mappings
    ])
