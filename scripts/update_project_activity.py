#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目活跃度状态更新脚本

使用方法:
python scripts/update_project_activity.py [--days=7] [--project-id=123]

参数说明:
--days: 不活跃天数阈值，默认为系统设置中的值
--project-id: 指定检查特定项目ID，默认为全部项目
"""

import sys
import os
import argparse
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 确保可以导入app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, 'project_activity.log')
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)

# 添加控制台输出
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 配置根日志记录器
logger = logging.getLogger('')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(console)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='更新项目活跃度状态')
    parser.add_argument('--days', type=int, default=None,
                        help='不活跃天数阈值，默认为系统设置中的值')
    parser.add_argument('--project-id', type=int,
                        help='指定检查特定项目ID，默认为全部项目')
    return parser.parse_args()

def update_project_activity(project_id=None, days_threshold=None):
    """更新项目活跃度状态"""
    from app import db
    from app.utils.activity_tracker import check_project_activity
    from app.models.project import Project
    
    start_time = datetime.now()
    
    # 获取活跃和不活跃的项目列表
    active_projects, inactive_projects = check_project_activity(
        project_id=project_id,
        days_threshold=days_threshold
    )
    
    updated_count = 0
    active_updated = 0
    inactive_updated = 0
    
    # 更新活跃项目
    for project in active_projects:
        if not project.is_active:
            logger.info(f"项目 ID: {project.id}, 名称: {project.project_name} 状态从不活跃变更为活跃，最后活动时间: {project.last_activity_date}")
            project.is_active = True
            # 不设置last_activity_date，因为在check_project_activity函数中已经设置
            db.session.add(project)
            updated_count += 1
            active_updated += 1
    
    # 更新不活跃项目
    for project in inactive_projects:
        if project.is_active:
            logger.info(f"项目 ID: {project.id}, 名称: {project.project_name} 状态从活跃变更为不活跃，上次活动时间: {project.last_activity_date}")
            project.is_active = False
            # 保留last_activity_date，便于了解项目最后活动的时间
            db.session.add(project)
            updated_count += 1
            inactive_updated += 1
    
    # 提交更改
    if updated_count > 0:
        db.session.commit()
        logger.info(f"完成项目活跃度更新，共更新 {updated_count} 个项目状态，其中 {active_updated} 个变为活跃，{inactive_updated} 个变为不活跃")
    else:
        logger.info("完成项目活跃度更新，没有项目状态需要更新")
    
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"项目活跃度更新完成 - 总时间: {duration:.2f}秒, "
               f"活跃项目: {len(active_projects)}, 不活跃项目: {len(inactive_projects)}, 更新数量: {updated_count}")
    
    return updated_count, len(active_projects), len(inactive_projects)

def main():
    """主函数"""
    args = parse_args()
    
    # 创建应用上下文
    from app import create_app
    app = create_app()
    
    with app.app_context():
        try:
            updated_count, active_count, inactive_count = update_project_activity(
                project_id=args.project_id,
                days_threshold=args.days
            )
            logger.info(f"项目活跃度更新执行完成")
        except Exception as e:
            logger.exception(f"更新项目活跃度时发生错误: {str(e)}")
            sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main() 