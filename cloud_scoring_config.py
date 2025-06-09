#!/usr/bin/env python3
"""
云端评分配置数据初始化脚本
在云端执行此脚本来初始化评分配置数据
"""

from app import create_app, db
from app.models.project_scoring import ProjectScoringConfig
from datetime import datetime

def init_scoring_configs():
    """初始化评分配置数据"""
    app = create_app()
    
    with app.app_context():
        # 清空现有配置
        ProjectScoringConfig.query.delete()
        
        # 配置数据
        configs_data = [
            {
                'category': 'information',
                'field_name': 'design_consultant',
                'field_label': '设计顾问',
                'score_value': 0.10,
                'prerequisite': "法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分",
                'is_active': True
            },
            {
                'category': 'information',
                'field_name': 'general_contractor',
                'field_label': '总承包',
                'score_value': 0.10,
                'prerequisite': "法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分",
                'is_active': True
            },
            {
                'category': 'information',
                'field_name': 'project_category',
                'field_label': '项目分类',
                'score_value': 0.10,
                'prerequisite': "法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分",
                'is_active': True
            },
            {
                'category': 'information',
                'field_name': 'project_stage',
                'field_label': '项目阶段',
                'score_value': 0.10,
                'prerequisite': "法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分",
                'is_active': True
            },
            {
                'category': 'information',
                'field_name': 'system_integrator',
                'field_label': '集成商',
                'score_value': 0.10,
                'prerequisite': "法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分",
                'is_active': True
            },
            {
                'category': 'information',
                'field_name': 'user_info',
                'field_label': '用户信息',
                'score_value': 0.10,
                'prerequisite': "法制逻辑：阈值制评分
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用"要么得分(0.5)，要么不得分(0.0)"的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分",
                'is_active': True
            },
            {
                'category': 'manual',
                'field_name': 'supervisor_award',
                'field_label': '上级奖励',
                'score_value': 0.50,
                'prerequisite': "手动评分",
                'is_active': True
            },
            {
                'category': 'quotation',
                'field_name': 'approved_quotation',
                'field_label': '审核通过的报价单',
                'score_value': 0.50,
                'prerequisite': "必须经由解决方案经理审批流程通过",
                'is_active': True
            },
            {
                'category': 'stage',
                'field_name': 'awarded',
                'field_label': '中标',
                'score_value': 1.00,
                'prerequisite': "无",
                'is_active': True
            },
            {
                'category': 'stage',
                'field_name': 'final_pricing',
                'field_label': '批价',
                'score_value': 1.50,
                'prerequisite': "无",
                'is_active': True
            },
            {
                'category': 'stage',
                'field_name': 'tender',
                'field_label': '招投标',
                'score_value': 0.50,
                'prerequisite': "无",
                'is_active': True
            },
        ]
        
        # 插入配置数据
        for config_data in configs_data:
            config = ProjectScoringConfig(
                category=config_data['category'],
                field_name=config_data['field_name'],
                field_label=config_data['field_label'],
                score_value=config_data['score_value'],
                prerequisite=config_data['prerequisite'],
                is_active=config_data['is_active']
            )
            db.session.add(config)
        
        db.session.commit()
        
        print(f"✅ 成功初始化 {len(configs_data)} 条评分配置")
        
        # 验证数据
        total_configs = ProjectScoringConfig.query.count()
        print(f"✅ 数据库中共有 {total_configs} 条评分配置")
        
        # 按类别统计
        categories = db.session.query(ProjectScoringConfig.category, db.func.count(ProjectScoringConfig.id)).group_by(ProjectScoringConfig.category).all()
        print("\n各类别配置数量:")
        for category, count in categories:
            print(f"  {category}: {count}条")

if __name__ == '__main__':
    init_scoring_configs()
