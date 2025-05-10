#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建样本账户数据用于测试
为阶段历史记录表中的记录随机分配账户ID
"""

from app import create_app, db
from app.models.projectpm_stage_history import ProjectStageHistory
from app.models.user import User
import logging
import random

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_data():
    """创建样本账户数据"""
    app = create_app()
    
    with app.app_context():
        try:
            # 获取系统中的用户列表
            users = User.query.filter(User.is_active == True).all()
            
            if not users:
                logger.error("没有找到活跃用户，尝试获取所有用户")
                users = User.query.all()
                
            if not users:
                logger.error("系统中没有用户，无法创建样本数据")
                return False
                
            user_ids = [user.id for user in users]
            logger.info(f"找到 {len(user_ids)} 个用户")
            
            # 获取所有历史记录
            records = ProjectStageHistory.query.all()
            
            if not records:
                logger.info("没有找到历史记录，无需创建样本数据")
                return False
                
            logger.info(f"找到 {len(records)} 条阶段历史记录")
            
            # 随机分配账户ID
            updated = 0
            for record in records:
                # 随机选择一个用户ID作为账户ID
                record.account_id = random.choice(user_ids)
                updated += 1
                
                # 每1000条提交一次
                if updated % 1000 == 0:
                    db.session.commit()
                    logger.info(f"已更新 {updated} 条记录")
            
            # 提交剩余更改
            db.session.commit()
            logger.info(f"成功更新 {updated} 条记录的账户信息")
            
            # 统计每个账户的记录数
            for user_id in user_ids:
                count = ProjectStageHistory.query.filter_by(account_id=user_id).count()
                user = User.query.get(user_id)
                username = user.name if user else f"用户 {user_id}"
                logger.info(f"账户 {username}(ID:{user_id}) 有 {count} 条历史记录")
            
            return True
        except Exception as e:
            logger.error(f"创建样本数据失败: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    import sys
    
    logger.info("开始创建样本账户数据...")
    success = create_sample_data()
    
    if success:
        logger.info("样本账户数据创建成功")
        sys.exit(0)
    else:
        logger.error("样本账户数据创建失败")
        sys.exit(1) 