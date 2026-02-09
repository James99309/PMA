#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
刘威历史数据回溯脚本

查询 user_id=12 (刘威) 的所有 WorkItem 和 Action 关联的 project_id，
为每个项目创建 ProjectMember(role='solution_engineer', source='retroactive') 记录。

使用方法:
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
  python3 scripts/temp/retroactive_project_members.py
"""
import sys
import os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models.relation import ProjectMember
from app.models.worklog import WorkItem
from app.models.action import Action
from sqlalchemy import func

TARGET_USER_ID = 12  # 刘威

def main():
    app = create_app()
    with app.app_context():
        # 查询所有 WorkItem 关联的 project_id
        wi_projects = db.session.query(WorkItem.project_id).filter(
            WorkItem.owner_id == TARGET_USER_ID,
            WorkItem.project_id.isnot(None)
        ).distinct().all()
        wi_project_ids = {r[0] for r in wi_projects}

        # 查询所有 Action 关联的 project_id
        act_projects = db.session.query(Action.project_id).filter(
            Action.owner_id == TARGET_USER_ID,
            Action.project_id.isnot(None)
        ).distinct().all()
        act_project_ids = {r[0] for r in act_projects}

        all_project_ids = wi_project_ids | act_project_ids
        print(f"发现 {len(all_project_ids)} 个关联项目: {sorted(all_project_ids)}")

        created = 0
        skipped = 0
        for pid in sorted(all_project_ids):
            # 检查是否已存在
            existing = ProjectMember.query.filter_by(
                project_id=pid, user_id=TARGET_USER_ID, role='solution_engineer'
            ).first()
            if existing:
                print(f"  项目 {pid}: 已存在，跳过")
                skipped += 1
                continue

            # 获取最早的 WorkItem 日期
            earliest_wi = db.session.query(func.min(WorkItem.planned_date)).filter(
                WorkItem.owner_id == TARGET_USER_ID,
                WorkItem.project_id == pid
            ).scalar()

            earliest_act = db.session.query(func.min(Action.date)).filter(
                Action.owner_id == TARGET_USER_ID,
                Action.project_id == pid
            ).scalar()

            dates = [d for d in [earliest_wi, earliest_act] if d is not None]
            first_date = min(dates) if dates else None

            # 查找最早的 WorkItem ID 作为 source_workitem_id
            source_wi = WorkItem.query.filter(
                WorkItem.owner_id == TARGET_USER_ID,
                WorkItem.project_id == pid
            ).order_by(WorkItem.planned_date).first()

            from datetime import datetime
            member = ProjectMember(
                project_id=pid,
                user_id=TARGET_USER_ID,
                role='solution_engineer',
                source='retroactive',
                source_workitem_id=source_wi.id if source_wi else None,
                first_associated_at=datetime.combine(first_date, datetime.min.time()) if first_date else None
            )
            db.session.add(member)
            created += 1
            print(f"  项目 {pid}: 创建成功 (首次关联: {first_date})")

        db.session.commit()
        print(f"\n完成: 创建 {created} 条, 跳过 {skipped} 条")

        # 验证
        total = ProjectMember.query.filter_by(user_id=TARGET_USER_ID).count()
        print(f"验证: 刘威总 ProjectMember 记录数 = {total}")

if __name__ == '__main__':
    main()
