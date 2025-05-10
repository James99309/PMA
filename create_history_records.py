#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建项目阶段变更历史记录样本数据
"""

from app import create_app, db
from app.models.projectpm_stage_history import ProjectStageHistory
from app.models.project import Project
from app.models.user import User
import logging
import random
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 阶段定义
STAGES = ['发现', '品牌植入', '招标前', '投标中', '中标', '签约', '失败', '搁置']

def create_history_data():
    """创建历史记录样本数据"""
    app = create_app()
    
    with app.app_context():
        try:
            # 获取所有项目
            projects = Project.query.all()
            
            if not projects:
                logger.error("没有找到项目，无法创建历史记录")
                return False
                
            logger.info(f"找到 {len(projects)} 个项目")
            
            # 获取所有用户
            users = User.query.all()
            if not users:
                logger.error("没有找到用户，无法关联账户信息")
                return False
                
            user_ids = [user.id for user in users]
            logger.info(f"找到 {len(user_ids)} 个用户")
            
            # 清空现有历史记录
            try:
                num_deleted = db.session.query(ProjectStageHistory).delete()
                db.session.commit()
                logger.info(f"已清空 {num_deleted} 条现有历史记录")
            except Exception as e:
                logger.error(f"清空历史记录失败: {str(e)}")
                db.session.rollback()
            
            # 为每个项目创建多条历史记录
            current_date = datetime.now()
            records_created = 0
            
            for project in projects:
                # 每个项目创建2-5条记录
                num_records = random.randint(2, 5)
                
                # 设置起始阶段为"发现"
                from_stage = None
                to_stage = '发现'
                
                # 为每个项目创建阶段变更历史
                for i in range(num_records):
                    # 创建时间点：随机过去1-24个月的时间
                    months_ago = random.randint(1, 24)
                    record_date = current_date - timedelta(days=30*months_ago)
                    
                    # 随机分配账户ID
                    account_id = random.choice(user_ids)
                    
                    # 创建历史记录
                    record = ProjectStageHistory(
                        project_id=project.id,
                        from_stage=from_stage,
                        to_stage=to_stage,
                        change_date=record_date,
                        account_id=account_id,
                        remarks=f"样本数据: 项目 {project.id} 从 {from_stage or '初始'} 变更为 {to_stage}"
                    )
                    
                    # 更新年、月、周信息
                    record.change_year = record_date.year
                    record.change_month = int(f"{record_date.year}{record_date.month:02d}")
                    week = int(record_date.strftime('%W'))
                    record.change_week = int(f"{record_date.year}{week:02d}")
                    
                    db.session.add(record)
                    records_created += 1
                    
                    # 设置下一个阶段变更
                    from_stage = to_stage
                    
                    # 选择下一个阶段，通常是向前推进，但有小概率失败或搁置
                    if random.random() < 0.2:  # 20%概率失败或搁置
                        to_stage = random.choice(['失败', '搁置'])
                    else:
                        # 正常推进到下一阶段
                        current_index = STAGES.index(from_stage)
                        next_index = min(current_index + 1, len(STAGES) - 1)
                        to_stage = STAGES[next_index]
                
                # 每100个项目提交一次
                if records_created % 100 == 0:
                    db.session.commit()
                    logger.info(f"已创建 {records_created} 条历史记录...")
            
            # 提交剩余更改
            db.session.commit()
            logger.info(f"成功创建 {records_created} 条历史记录")
            
            # 统计不同阶段的记录数
            for stage in STAGES:
                count = ProjectStageHistory.query.filter_by(to_stage=stage).count()
                logger.info(f"阶段 '{stage}' 有 {count} 条历史记录")
            
            # 统计每个账户的记录数
            for user_id in user_ids:
                count = ProjectStageHistory.query.filter_by(account_id=user_id).count()
                user = User.query.get(user_id)
                username = user.name if user else f"用户 {user_id}"
                logger.info(f"账户 {username}(ID:{user_id}) 有 {count} 条历史记录")
            
            return True
        except Exception as e:
            logger.error(f"创建历史记录失败: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    import sys
    
    logger.info("开始创建项目阶段变更历史记录...")
    success = create_history_data()
    
    if success:
        logger.info("历史记录样本数据创建成功")
        sys.exit(0)
    else:
        logger.error("历史记录样本数据创建失败")
        sys.exit(1) 