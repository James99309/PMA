#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
首次项目活跃度检查脚本

运行此脚本将检查所有项目的活跃度状态，并将结果写入数据库。
"""

import sys
import os

# 确保可以导入app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_first_activity_check():
    """执行首次项目活跃度检查"""
    from app import create_app, db
    from app.utils.activity_tracker import check_project_activity
    from datetime import datetime
    
    app = create_app()
    
    with app.app_context():
        start_time = datetime.now()
        print(f"开始项目活跃度检查: {start_time}")
        
        # 获取活跃和不活跃的项目列表
        active_projects, inactive_projects = check_project_activity()
        
        print(f"检查完成，活跃项目: {len(active_projects)}，不活跃项目: {len(inactive_projects)}")
        
        # 统计不同活跃原因的数量
        activity_reasons = {}
        
        # 更新活跃项目
        count = 0
        for project in active_projects:
            project.is_active = True
            # 不需要设置last_activity_date，因为在check_project_activity函数中已经设置
            
            # 统计活跃原因
            reason = getattr(project, 'activity_reason', '未知原因')
            activity_reasons[reason] = activity_reasons.get(reason, 0) + 1
            
            db.session.add(project)
            count += 1
            if count % 100 == 0:
                print(f"已处理 {count} 个活跃项目")
        
        print(f"已更新 {count} 个活跃项目")
        
        # 更新不活跃项目
        count = 0
        for project in inactive_projects:
            project.is_active = False
            # 使用updated_at作为最后活动时间
            if not project.last_activity_date and project.updated_at:
                project.last_activity_date = project.updated_at
            
            db.session.add(project)
            count += 1
            if count % 100 == 0:
                print(f"已处理 {count} 个不活跃项目")
        
        print(f"已更新 {count} 个不活跃项目")
        
        # 提交更改
        db.session.commit()
        
        # 打印活跃原因统计
        print("\n活跃原因统计:")
        for reason, count in activity_reasons.items():
            print(f"- {reason}: {count}个项目")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"项目活跃度检查完成: {end_time}")
        print(f"总耗时: {duration:.2f}秒")
        print(f"活跃项目: {len(active_projects)}, 不活跃项目: {len(inactive_projects)}")

if __name__ == '__main__':
    run_first_activity_check() 