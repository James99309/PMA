#!/usr/bin/env python3
"""
验证项目评分修正效果
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.project_scoring import ProjectTotalScore
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_scoring_fixes():
    """验证评分修正效果"""
    app = create_app()
    
    with app.app_context():
        logger.info("=== 验证评分修正效果 ===")
        
        # 检查是否有非0.5步进的评分
        non_standard_scores = ProjectTotalScore.query.filter(
            db.and_(
                ProjectTotalScore.total_score > 0,
                db.text("MOD(total_score * 2, 1) != 0")  # 检查是否不是0.5的倍数
            )
        ).all()
        
        logger.info(f"非标准评分项目数量: {len(non_standard_scores)}")
        if non_standard_scores:
            logger.warning("发现非标准评分项目:")
            for score in non_standard_scores[:5]:  # 只显示前5个
                logger.warning(f"  项目ID {score.project_id}: 总分 {score.total_score}, 星级 {score.star_rating}")
        
        # 检查星级与总分是否一致
        mismatched_ratings = ProjectTotalScore.query.filter(
            ProjectTotalScore.total_score != ProjectTotalScore.star_rating
        ).all()
        
        logger.info(f"星级与总分不一致的项目数量: {len(mismatched_ratings)}")
        if mismatched_ratings:
            logger.warning("发现星级与总分不一致的项目:")
            for score in mismatched_ratings[:5]:  # 只显示前5个
                logger.warning(f"  项目ID {score.project_id}: 总分 {score.total_score}, 星级 {score.star_rating}")
        
        # 统计评分分布
        score_distribution = {}
        all_scores = ProjectTotalScore.query.all()
        
        for score in all_scores:
            total = float(score.total_score)
            score_distribution[total] = score_distribution.get(total, 0) + 1
        
        logger.info("评分分布统计:")
        for score in sorted(score_distribution.keys()):
            logger.info(f"  {score}分: {score_distribution[score]} 个项目")
        
        # 检查特定的示例项目（上海空铁联运）
        example_project = ProjectTotalScore.query.join(
            ProjectTotalScore.project
        ).filter(
            db.text("projects.project_name LIKE '%空铁联运%'")
        ).first()
        
        if example_project:
            logger.info(f"示例项目（空铁联运）评分:")
            logger.info(f"  信息完整性: {example_project.information_score}")
            logger.info(f"  报价完整性: {example_project.quotation_score}")
            logger.info(f"  阶段得分: {example_project.stage_score}")
            logger.info(f"  手动奖励: {example_project.manual_score}")
            logger.info(f"  总分: {example_project.total_score}")
            logger.info(f"  星级: {example_project.star_rating}")

if __name__ == '__main__':
    verify_scoring_fixes() 