#!/usr/bin/env python3
"""
项目评分系统更新脚本
重新计算本地数据库中所有项目的评分，确保评分结果符合最新的评分逻辑
"""

import os
import sys
from datetime import datetime
import logging

# 设置环境
os.environ['FLASK_ENV'] = 'development'

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.project import Project
from app.models.project_scoring import ProjectScoringEngine, ProjectTotalScore, ProjectScoringRecord, ProjectScoringConfig
from app.models.quotation import Quotation

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_scoring_update.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_scoring_config():
    """验证评分配置是否完整"""
    logger.info("=== 验证评分配置 ===")
    
    configs = ProjectScoringConfig.query.filter_by(is_active=True).all()
    
    # 按类别分组
    config_by_category = {}
    for config in configs:
        if config.category not in config_by_category:
            config_by_category[config.category] = []
        config_by_category[config.category].append(config)
    
    logger.info(f"找到 {len(configs)} 个活跃的评分配置项:")
    
    for category, items in config_by_category.items():
        logger.info(f"  {category}: {len(items)} 项")
        for item in items:
            logger.info(f"    - {item.field_name}: {item.score_value}分 ({item.field_label})")
    
    # 检查必要的配置
    required_configs = [
        ('information', ['project_stage', 'project_category', 'design_consultant', 'user_info', 'general_contractor', 'system_integrator']),
        ('quotation', ['approved_quotation']),
        ('stage', ['tender', 'awarded', 'final_pricing']),
        ('manual', ['supervisor_award'])
    ]
    
    missing_configs = []
    for category, fields in required_configs:
        if category not in config_by_category:
            missing_configs.append(f"缺少整个类别: {category}")
            continue
        
        existing_fields = [item.field_name for item in config_by_category[category]]
        for field in fields:
            if field not in existing_fields:
                missing_configs.append(f"缺少配置: {category}.{field}")
    
    if missing_configs:
        logger.warning("发现缺失的配置项:")
        for missing in missing_configs:
            logger.warning(f"  - {missing}")
    else:
        logger.info("✓ 所有必要的评分配置都已存在")
    
    return len(missing_configs) == 0

def get_project_statistics():
    """获取项目统计信息"""
    logger.info("=== 项目统计信息 ===")
    
    # 项目总数
    total_projects = Project.query.count()
    logger.info(f"项目总数: {total_projects}")
    
    # 按阶段分组
    stage_stats = db.session.query(
        Project.current_stage,
        db.func.count(Project.id).label('count')
    ).group_by(Project.current_stage).all()
    
    logger.info("按阶段分布:")
    for stage, count in stage_stats:
        stage_name = stage or "未设置"
        logger.info(f"  {stage_name}: {count} 个项目")
    
    # 已有评分的项目
    scored_projects = ProjectTotalScore.query.count()
    logger.info(f"已有评分记录的项目: {scored_projects}")
    
    # 报价统计
    projects_with_quotations = db.session.query(Project.id).join(Quotation).distinct().count()
    logger.info(f"有报价单的项目: {projects_with_quotations}")
    
    return {
        'total_projects': total_projects,
        'scored_projects': scored_projects,
        'projects_with_quotations': projects_with_quotations
    }

def recalculate_all_scores(batch_size=50, dry_run=False):
    """重新计算所有项目的评分
    
    Args:
        batch_size: 批处理大小
        dry_run: 是否为试运行模式（不实际保存）
    """
    logger.info("=== 开始重新计算项目评分 ===")
    
    if dry_run:
        logger.info("⚠️ 试运行模式 - 不会保存任何更改")
    
    # 获取所有项目
    total_projects = Project.query.count()
    logger.info(f"待处理项目总数: {total_projects}")
    
    successful_count = 0
    failed_count = 0
    updated_count = 0
    unchanged_count = 0
    
    # 分批处理
    for offset in range(0, total_projects, batch_size):
        projects = Project.query.offset(offset).limit(batch_size).all()
        logger.info(f"处理批次 {offset//batch_size + 1}/{(total_projects-1)//batch_size + 1}: {len(projects)} 个项目")
        
        for project in projects:
            try:
                # 获取当前评分
                current_score = ProjectTotalScore.query.filter_by(project_id=project.id).first()
                old_total = float(current_score.total_score) if current_score else 0.0
                old_rating = float(current_score.star_rating) if current_score else 0.0
                
                # 计算新评分（不提交数据库）
                result = ProjectScoringEngine.calculate_project_score(project.id, commit=False)
                
                if result:
                    new_total = result['total_score']
                    new_rating = result['star_rating']
                    
                    # 检查是否有变化
                    if abs(new_total - old_total) > 0.01 or abs(new_rating - old_rating) > 0.1:
                        updated_count += 1
                        logger.info(f"  ✓ 项目 [{project.id}] {project.project_name[:30]}...")
                        logger.info(f"    评分变化: {old_total:.2f}→{new_total:.2f}, 星级: {old_rating}→{new_rating}")
                        logger.info(f"    详细得分: 信息({result['information_score']:.2f}) + 报价({result['quotation_score']:.2f}) + 阶段({result['stage_score']:.2f}) + 手动({result['manual_score']:.2f})")
                    else:
                        unchanged_count += 1
                        logger.debug(f"  - 项目 [{project.id}] {project.project_name[:30]}... (无变化)")
                    
                    successful_count += 1
                    
                    # 如果不是试运行，提交更改
                    if not dry_run:
                        db.session.commit()
                    else:
                        db.session.rollback()
                        
                else:
                    failed_count += 1
                    logger.error(f"  ✗ 项目 [{project.id}] {project.project_name} 评分计算失败")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"  ✗ 项目 [{project.id}] {project.project_name} 处理异常: {str(e)}")
                db.session.rollback()
        
        # 批次完成提示
        logger.info(f"批次完成: 成功 {successful_count}, 失败 {failed_count}")
    
    # 最终统计
    logger.info("=== 评分更新完成 ===")
    logger.info(f"总计处理: {total_projects} 个项目")
    logger.info(f"成功计算: {successful_count} 个")
    logger.info(f"评分更新: {updated_count} 个")
    logger.info(f"评分未变: {unchanged_count} 个")
    logger.info(f"计算失败: {failed_count} 个")
    
    if failed_count > 0:
        logger.warning(f"⚠️ 有 {failed_count} 个项目评分计算失败，请检查日志")
    
    return {
        'total': total_projects,
        'successful': successful_count,
        'updated': updated_count,
        'unchanged': unchanged_count,
        'failed': failed_count
    }

def validate_results():
    """验证评分结果"""
    logger.info("=== 验证评分结果 ===")
    
    # 统计评分分布
    score_ranges = [
        (0.0, 0.5, "0-0.5分"),
        (0.5, 1.0, "0.5-1.0分"),
        (1.0, 1.5, "1.0-1.5分"),
        (1.5, 2.0, "1.5-2.0分"),
        (2.0, 2.5, "2.0-2.5分"),
        (2.5, 3.0, "2.5-3.0分"),
        (3.0, 3.5, "3.0-3.5分"),
        (3.5, 4.0, "3.5-4.0分"),
        (4.0, 4.5, "4.0-4.5分"),
        (4.5, 5.0, "4.5-5.0分"),
    ]
    
    logger.info("评分分布:")
    for min_score, max_score, label in score_ranges:
        count = ProjectTotalScore.query.filter(
            ProjectTotalScore.total_score >= min_score,
            ProjectTotalScore.total_score < max_score
        ).count()
        if count > 0:
            logger.info(f"  {label}: {count} 个项目")
    
    # 统计星级分布
    star_stats = db.session.query(
        ProjectTotalScore.star_rating,
        db.func.count(ProjectTotalScore.id).label('count')
    ).group_by(ProjectTotalScore.star_rating).order_by(ProjectTotalScore.star_rating).all()
    
    logger.info("星级分布:")
    for rating, count in star_stats:
        logger.info(f"  {rating}星: {count} 个项目")
    
    # 检查异常情况
    logger.info("异常检查:")
    
    # 评分为0的项目
    zero_score_count = ProjectTotalScore.query.filter_by(total_score=0.0).count()
    logger.info(f"  0分项目: {zero_score_count} 个")
    
    # 评分与星级不匹配的项目
    mismatched = ProjectTotalScore.query.filter(
        db.or_(
            db.and_(ProjectTotalScore.total_score > 0, ProjectTotalScore.star_rating == 0),
            db.and_(ProjectTotalScore.total_score == 0, ProjectTotalScore.star_rating > 0)
        )
    ).count()
    logger.info(f"  评分与星级不匹配: {mismatched} 个")
    
    # 项目表rating字段与评分记录不一致
    inconsistent_rating = db.session.query(Project).join(ProjectTotalScore).filter(
        Project.rating != ProjectTotalScore.star_rating
    ).count()
    logger.info(f"  项目rating字段不一致: {inconsistent_rating} 个")

def show_sample_projects(limit=10):
    """显示示例项目的评分详情"""
    logger.info(f"=== 示例项目评分详情 (前{limit}个) ===")
    
    projects = db.session.query(Project).join(ProjectTotalScore).order_by(ProjectTotalScore.total_score.desc()).limit(limit).all()
    
    for project in projects:
        total_score = project.total_score
        logger.info(f"项目: {project.project_name}")
        logger.info(f"  总分: {total_score.total_score} ({total_score.star_rating}星)")
        logger.info(f"  详细: 信息({total_score.information_score}) + 报价({total_score.quotation_score}) + 阶段({total_score.stage_score}) + 手动({total_score.manual_score})")
        logger.info(f"  阶段: {project.current_stage or '未设置'}")
        logger.info(f"  类型: {project.project_type or '未设置'}")
        
        # 显示报价信息
        quotation_count = Quotation.query.filter_by(project_id=project.id).count()
        logger.info(f"  报价单: {quotation_count} 个")
        logger.info("")

def main():
    """主函数"""
    print("=" * 60)
    print("PMA项目评分系统更新脚本")
    print("=" * 60)
    
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        try:
            logger.info(f"脚本开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 1. 验证评分配置
            if not validate_scoring_config():
                logger.error("评分配置不完整，请先检查配置")
                return 1
            
            # 2. 显示项目统计
            stats = get_project_statistics()
            
            # 3. 询问用户操作模式
            print("\n请选择操作模式:")
            print("1. 试运行模式 (只计算不保存)")
            print("2. 正式更新模式 (计算并保存)")
            print("3. 仅查看统计信息")
            
            choice = input("\n请输入选择 (1/2/3): ").strip()
            
            if choice == "1":
                logger.info("选择: 试运行模式")
                result = recalculate_all_scores(dry_run=True)
                
            elif choice == "2":
                logger.info("选择: 正式更新模式")
                confirm = input("⚠️ 此操作将修改数据库中的项目评分，是否确认? (y/N): ").strip().lower()
                if confirm == 'y':
                    result = recalculate_all_scores(dry_run=False)
                    validate_results()
                    show_sample_projects()
                else:
                    logger.info("操作已取消")
                    return 0
                    
            elif choice == "3":
                logger.info("选择: 仅查看统计信息")
                if stats['scored_projects'] > 0:
                    validate_results()
                    show_sample_projects()
                else:
                    logger.info("暂无评分数据")
                return 0
                
            else:
                logger.error("无效选择")
                return 1
            
            logger.info(f"脚本完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("项目评分更新脚本执行完成!")
            
            return 0
            
        except Exception as e:
            logger.error(f"脚本执行失败: {str(e)}")
            return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 