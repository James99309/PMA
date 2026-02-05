#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务模块

提供客户活跃度自动修正等定时任务功能。
默认每日凌晨1点执行客户活跃度批量更新。
"""

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


def start_scheduler(run_time="01:00"):
    """
    启动定时任务调度器

    Args:
        run_time: 每日执行时间，格式为 "HH:MM"，默认凌晨1点

    调度器会在后台线程中运行，不阻塞主程序。
    """
    global _scheduler_running, _scheduler_thread

    if _scheduler_running:
        logger.warning("调度器已在运行中，跳过重复启动")
        return

    # 设置每日定时任务
    schedule.every().day.at(run_time).do(run_activity_correction)
    schedule.every().day.at("01:30").do(run_project_activity_correction)

    _scheduler_running = True

    # 在后台线程运行调度器
    _scheduler_thread = threading.Thread(target=_run_schedule, daemon=True)
    _scheduler_thread.start()

    logger.info(f"定时任务调度器已启动，每日 {run_time} 执行客户活跃度修正，01:30 执行项目活跃度修正")


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
