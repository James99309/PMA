#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务模块

提供客户活跃度自动修正等定时任务功能。
默认每日凌晨1点执行客户活跃度批量更新。
"""

import os
import schedule
import time
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 全局调度器状态
_scheduler_running = False
_scheduler_thread = None


def run_activity_correction():
    """
    执行客户活跃度修正任务

    从Flask应用上下文中执行批量更新所有客户的活跃度状态。
    此函数会在定时任务触发时被调用。
    """
    from flask import current_app
    from app import create_app, db
    from app.utils.activity_tracker import batch_update_all_company_activity

    logger.info(f"[{datetime.now()}] 开始执行客户活跃度定时修正...")

    try:
        # 检查是否在应用上下文中
        try:
            # 尝试访问current_app
            app = current_app._get_current_object()
        except RuntimeError:
            # 不在应用上下文中，创建新的应用
            app = create_app()

        with app.app_context():
            updated, total = batch_update_all_company_activity()
            logger.info(f"[{datetime.now()}] 客户活跃度修正完成: 更新 {updated}/{total} 条记录")

    except Exception as e:
        logger.error(f"[{datetime.now()}] 客户活跃度修正失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def run_project_activity_correction():
    """
    执行项目活跃度修正任务

    从Flask应用上下文中执行批量更新所有项目的活跃度状态。
    此函数会在定时任务触发时被调用。
    """
    from flask import current_app
    from app import create_app, db
    from app.utils.activity_tracker import batch_update_all_project_activity

    logger.info(f"[{datetime.now()}] 开始执行项目活跃度定时修正...")

    try:
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            app = create_app()

        with app.app_context():
            updated, total = batch_update_all_project_activity()
            logger.info(f"[{datetime.now()}] 项目活跃度修正完成: 更新 {updated}/{total} 条记录")

    except Exception as e:
        logger.error(f"[{datetime.now()}] 项目活跃度修正失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def run_monthly_activity_snapshot():
    """
    为所有活跃用户生成当月活跃度快照

    在每日 02:00 执行，冻结当月活跃度数据。
    时序：01:00 公司活跃度更新 → 01:30 项目活跃度更新 → 02:00 快照冻结
    """
    from flask import current_app
    from app import create_app, db
    from app.models.user import User
    from app.services.performance_dashboard_service import PerformanceDashboardService

    logger.info(f"[{datetime.now()}] 开始执行月度活跃度快照任务...")

    try:
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            app = create_app()

        with app.app_context():
            now = datetime.now()
            current_year = now.year
            current_month = now.month

            # 查询所有活跃用户
            active_users = User.query.filter_by(is_active=True).all()
            success_count = 0
            fail_count = 0

            for user in active_users:
                try:
                    PerformanceDashboardService.create_monthly_activity_snapshot(
                        user.id, current_year, current_month
                    )
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    logger.warning(f"用户 {user.id} 快照生成失败: {e}")

            logger.info(f"[{datetime.now()}] 月度活跃度快照完成: 成功 {success_count}, 失败 {fail_count}, 总计 {len(active_users)}")

    except Exception as e:
        logger.error(f"[{datetime.now()}] 月度活跃度快照任务失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def run_daily_backup():
    """
    执行每日数据库备份

    在每日 03:00 执行自动备份。
    仅在失败时推送内部消息通知管理员，成功时静默。
    """
    from flask import current_app
    from app import create_app

    logger.info(f"[{datetime.now()}] 开始执行每日数据库备份...")

    try:
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            app = create_app()

        with app.app_context():
            from app.services.supabase_backup_service import get_backup_service

            backup_service = get_backup_service()
            results = backup_service.create_backup()

            if results:
                logger.info(f"[{datetime.now()}] 每日备份完成: {results[0]['filename']} ({results[0]['size'] / 1024 / 1024:.1f} MB)")
            else:
                raise Exception("备份未生成文件")

    except Exception as e:
        logger.error(f"[{datetime.now()}] 每日备份失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        # 失败时推送通知
        try:
            try:
                app = current_app._get_current_object()
            except RuntimeError:
                app = create_app()

            with app.app_context():
                from app.services.supabase_backup_service import get_backup_service
                get_backup_service()._send_backup_notification(False, error_message=str(e))
        except Exception as notify_err:
            logger.warning(f"发送备份失败通知也失败: {notify_err}")


def run_weekly_backup_cleanup():
    """
    每周日 04:00 清理超期备份文件
    """
    from flask import current_app
    from app import create_app

    logger.info(f"[{datetime.now()}] 开始执行每周备份清理...")

    try:
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            app = create_app()

        with app.app_context():
            from app.services.supabase_backup_service import get_backup_service

            backup_service = get_backup_service()
            deleted_count = backup_service.cleanup_old_backups()
            logger.info(f"[{datetime.now()}] 每周备份清理完成: 删除了 {deleted_count} 个过期备份")

    except Exception as e:
        logger.error(f"[{datetime.now()}] 每周备份清理失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def _run_schedule():
    """
    调度器主循环

    在后台线程中持续运行，每分钟检查一次待执行的任务。
    """
    global _scheduler_running

    while _scheduler_running:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"调度器执行出错: {str(e)}")
        time.sleep(60)  # 每分钟检查一次


def run_ai_research_batch():
    """
    每日批量处理未调研/调研失败的客户

    在每日 06:00 执行，批量处理 status=none/error 的公司。
    每批最多 50 个，每个间隔 10 秒避免 API 限流。
    """
    from flask import current_app
    from app import create_app

    logger.info(f"[{datetime.now()}] 开始执行 AI 调研批量任务...")

    try:
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            app = create_app()

        from app.services.ai_research_service import AIResearchService
        count = AIResearchService.batch_research_pending(app=app, limit=50, interval=10)
        logger.info(f"[{datetime.now()}] AI 调研批量任务完成: 处理 {count} 个客户")

        # 项目 AI 调研批量处理
        project_count = AIResearchService.batch_project_research_pending(app=app, limit=50, interval=10)
        logger.info(f"[{datetime.now()}] 项目 AI 调研批量任务完成: 处理 {project_count} 个项目")

    except Exception as e:
        logger.error(f"[{datetime.now()}] AI 调研批量任务失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def run_weekly_citation_coefficient_update():
    """每周更新产品引用频次系数"""
    from flask import current_app
    from app import create_app

    logger.info(f"[{datetime.now()}] 开始执行每周引用系数更新...")

    try:
        try:
            app = current_app._get_current_object()
        except RuntimeError:
            app = create_app()

        with app.app_context():
            from app.helpers.product_points import batch_update_citation_coefficients
            updated, total = batch_update_citation_coefficients()
            logger.info(f"[{datetime.now()}] 引用系数更新完成: {updated}/{total} 产品")

    except Exception as e:
        logger.error(f"[{datetime.now()}] 引用系数更新失败: {str(e)}")


def cleanup_old_worklog_notifications():
    """
    清理超过1天的 worklog_submitted 通知消息。
    这类通知量大且无人阅读，定时标为已读防止堆积。
    """
    try:
        from app import create_app, db
        from app.models.message import Message
        from datetime import timedelta

        app = create_app()
        with app.app_context():
            cutoff = datetime.now() - timedelta(days=1)
            result = db.session.execute(
                db.text(
                    "UPDATE messages SET is_read = true, read_at = NOW() "
                    "WHERE message_type = 'worklog_submitted' AND is_read = false "
                    "AND created_at < :cutoff"
                ),
                {'cutoff': cutoff}
            )
            db.session.commit()
            count = result.rowcount
            if count > 0:
                logger.info(f"[{datetime.now()}] 已清理 {count} 条过期工作日志通知")
    except Exception as e:
        logger.error(f"[{datetime.now()}] 工作日志通知清理失败: {str(e)}")


def start_scheduler(run_time="01:00"):
    """
    启动定时任务调度器

    Args:
        run_time: 每日执行时间，格式为 "HH:MM"，默认凌晨1点

    时间表:
        01:00 → 客户活跃度修正
        01:30 → 项目活跃度修正
        02:00 → 月度活跃度快照
        03:00 → 每日数据库备份 (新增)
        04:00 → 每周备份清理 (新增, 仅周日)

    调度器会在后台线程中运行，不阻塞主程序。
    """
    global _scheduler_running, _scheduler_thread

    if _scheduler_running:
        logger.warning("调度器已在运行中，跳过重复启动")
        return

    # 活跃度相关任务
    schedule.every().day.at(run_time).do(run_activity_correction)
    schedule.every().day.at("01:30").do(run_project_activity_correction)
    schedule.every().day.at("02:00").do(run_monthly_activity_snapshot)

    # AI 调研批量任务
    schedule.every().day.at("06:00").do(run_ai_research_batch)
    logger.info("AI 调研批量任务已注册: 每日 06:00")

    # 引用系数每周更新
    schedule.every().monday.at("05:00").do(run_weekly_citation_coefficient_update)
    logger.info("引用系数更新任务已注册: 每周一 05:00")

    # 工作日志通知清理（每天凌晨 00:30 清理超过1天的 worklog_submitted）
    schedule.every().day.at("00:30").do(cleanup_old_worklog_notifications)
    logger.info("工作日志通知清理任务已注册: 每日 00:30")

    # 备份相关任务
    backup_time = os.getenv('BACKUP_AUTO_TIME', '03:00')
    if os.getenv('BACKUP_AUTO_ENABLED', 'true').lower() == 'true':
        schedule.every().day.at(backup_time).do(run_daily_backup)
        schedule.every().sunday.at("04:00").do(run_weekly_backup_cleanup)
        logger.info(f"备份任务已注册: 每日 {backup_time} 自动备份, 每周日 04:00 清理")

    _scheduler_running = True

    # 在后台线程运行调度器
    _scheduler_thread = threading.Thread(target=_run_schedule, daemon=True)
    _scheduler_thread.start()

    logger.info(f"定时任务调度器已启动: {run_time} 客户活跃度, 01:30 项目活跃度, 02:00 快照, {backup_time} 备份, 06:00 AI调研")


def stop_scheduler():
    """
    停止定时任务调度器
    """
    global _scheduler_running, _scheduler_thread

    if not _scheduler_running:
        logger.warning("调度器未在运行")
        return

    _scheduler_running = False

    if _scheduler_thread and _scheduler_thread.is_alive():
        _scheduler_thread.join(timeout=5)

    schedule.clear()
    logger.info("定时任务调度器已停止")


def run_activity_correction_now():
    """
    立即执行一次客户活跃度修正

    用于手动触发或测试目的。
    """
    logger.info("手动触发客户活跃度修正...")
    run_activity_correction()


def get_scheduler_status():
    """
    获取调度器状态信息

    Returns:
        dict: 包含调度器运行状态和下次执行时间的字典
    """
    global _scheduler_running

    status = {
        'running': _scheduler_running,
        'jobs': []
    }

    for job in schedule.get_jobs():
        status['jobs'].append({
            'interval': str(job.interval),
            'unit': job.unit,
            'at_time': str(job.at_time) if job.at_time else None,
            'next_run': str(job.next_run) if job.next_run else None
        })

    return status
