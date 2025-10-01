#!/usr/bin/env python3
"""
修正项目评分计算问题
- 修正星级计算逻辑
- 修正信息完整性评分逻辑
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models.project_scoring import ProjectScoringEngine, ProjectTotalScore
from app.models.project import Project
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def recalculate_project_scores():
    """重新计算所有项目评分"""
    app = create_app()
    
    with app.app_context():
        logger.info("开始重新计算项目评分...")
        
        # 获取所有项目
        projects = Project.query.all()
        logger.info(f"找到 {len(projects)} 个项目")
        
        updated_count = 0
        failed_count = 0
        
        for project in projects:
            try:
                # 获取当前评分
                current_score = ProjectTotalScore.query.filter_by(project_id=project.id).first()
                old_total = float(current_score.total_score) if current_score else 0.0
                old_rating = float(current_score.star_rating) if current_score else 0.0
                
                # 重新计算评分
                result = ProjectScoringEngine.calculate_project_score(project.id, commit=True)
                
                if result:
                    new_total = result['total_score']
                    new_rating = result['star_rating']
                    
                    # 检查是否有变化
                    if abs(new_total - old_total) > 0.01 or abs(new_rating - old_rating) > 0.1:
                        updated_count += 1
                        logger.info(f"✓ [{project.id}] {project.project_name[:40]}...")
                        logger.info(f"  评分: {old_total:.2f}→{new_total:.2f}, 星级: {old_rating}→{new_rating}")
                        logger.info(f"  详细: 信息({result['information_score']:.2f}) + 报价({result['quotation_score']:.2f}) + 阶段({result['stage_score']:.2f}) + 手动({result['manual_score']:.2f})")
                    else:
                        logger.debug(f"- [{project.id}] {project.project_name[:40]}... (无变化)")
                else:
                    failed_count += 1
                    logger.error(f"✗ [{project.id}] {project.project_name} 评分计算失败")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"✗ [{project.id}] {project.project_name} 评分计算出错: {str(e)}")
        
        logger.info(f"评分计算完成:")
        logger.info(f"  更新项目: {updated_count}")
        logger.info(f"  失败项目: {failed_count}")
        logger.info(f"  总项目数: {len(projects)}")

if __name__ == '__main__':
    recalculate_project_scores() 