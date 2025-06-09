#!/usr/bin/env python3
"""
云端评分配置数据初始化脚本（简化版）
在云端执行此脚本来初始化评分配置数据
"""

from app import create_app, db
from app.models.project_scoring import ProjectScoringConfig

def init_scoring_configs():
    """初始化评分配置数据"""
    app = create_app()
    
    with app.app_context():
        # 清空现有配置
        ProjectScoringConfig.query.delete()
        
        # 信息完整性配置 (6条)
        info_configs = [
            ('design_consultant', '设计顾问', 0.10),
            ('general_contractor', '总承包', 0.10),
            ('project_category', '项目分类', 0.10),
            ('project_stage', '项目阶段', 0.10),
            ('system_integrator', '集成商', 0.10),
            ('user_info', '用户信息', 0.10)
        ]
        
        info_prerequisite = """阈值制评分逻辑：
1. 个别分值：每项信息0.1分
2. 阈值要求：需要至少5项信息才能获得最终得分
3. 计算公式：累计得分 >= 0.5分（阈值）→ 最终得分0.5分，否则0分
4. 实施规则：采用全有或全无的二元制
5. 超额处理：累计得分超过0.5分仍只给0.5分"""
        
        for field_name, field_label, score_value in info_configs:
            config = ProjectScoringConfig(
                category='information',
                field_name=field_name,
                field_label=field_label,
                score_value=score_value,
                prerequisite=info_prerequisite,
                is_active=True
            )
            db.session.add(config)
        
        # 阶段评分配置 (3条)
        stage_configs = [
            ('tender', '招投标', 0.50),
            ('awarded', '中标', 1.00),
            ('final_pricing', '批价', 1.50)
        ]
        
        for field_name, field_label, score_value in stage_configs:
            config = ProjectScoringConfig(
                category='stage',
                field_name=field_name,
                field_label=field_label,
                score_value=score_value,
                prerequisite='无',
                is_active=True
            )
            db.session.add(config)
        
        # 报价完整性配置 (1条)
        config = ProjectScoringConfig(
            category='quotation',
            field_name='approved_quotation',
            field_label='审核通过的报价单',
            score_value=0.50,
            prerequisite='必须经由解决方案经理审批流程通过',
            is_active=True
        )
        db.session.add(config)
        
        # 手动奖励配置 (1条)
        config = ProjectScoringConfig(
            category='manual',
            field_name='supervisor_award',
            field_label='上级奖励',
            score_value=0.50,
            prerequisite='手动评分',
            is_active=True
        )
        db.session.add(config)
        
        # 提交更改
        db.session.commit()
        
        print("✅ 成功初始化评分配置数据")
        
        # 验证数据
        total_configs = ProjectScoringConfig.query.count()
        print(f"✅ 数据库中共有 {total_configs} 条评分配置")
        
        # 按类别统计
        categories = db.session.query(
            ProjectScoringConfig.category, 
            db.func.count(ProjectScoringConfig.id)
        ).group_by(ProjectScoringConfig.category).all()
        
        print("\n各类别配置数量:")
        for category, count in categories:
            print(f"  {category}: {count}条")
        
        print("\n详细配置列表:")
        configs = ProjectScoringConfig.query.order_by(
            ProjectScoringConfig.category, 
            ProjectScoringConfig.field_name
        ).all()
        
        for config in configs:
            print(f"  {config.category}.{config.field_name}: {config.field_label} ({config.score_value}分)")

if __name__ == '__main__':
    print("=== 云端评分配置初始化 ===")
    init_scoring_configs()
    print("\n=== 初始化完成 ===")
    print("\n下一步：")
    print("1. 访问 /admin/scoring-config 检查配置页面")
    print("2. 点击'重新计算所有项目'按钮测试功能") 