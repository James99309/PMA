#!/usr/bin/env python3
"""
快速项目评分更新脚本
简化版本，直接执行评分更新而无需交互
"""

import os
import sys
from datetime import datetime

# 设置环境
os.environ['FLASK_ENV'] = 'development'

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.project import Project
from app.models.project_scoring import ProjectScoringEngine, ProjectTotalScore

def quick_update_all_scores():
    """快速更新所有项目评分"""
    print("=" * 50)
    print("PMA项目评分快速更新")
    print("=" * 50)
    
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        try:
            start_time = datetime.now()
            print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 获取项目总数
            total_projects = Project.query.count()
            print(f"项目总数: {total_projects}")
            
            updated_count = 0
            failed_count = 0
            
            # 分批处理
            batch_size = 100
            for offset in range(0, total_projects, batch_size):
                projects = Project.query.offset(offset).limit(batch_size).all()
                print(f"处理第 {offset//batch_size + 1} 批: {len(projects)} 个项目")
                
                for project in projects:
                    try:
                        # 计算评分
                        result = ProjectScoringEngine.calculate_project_score(project.id, commit=False)
                        if result:
                            updated_count += 1
                        else:
                            failed_count += 1
                            print(f"  失败: 项目 [{project.id}] {project.project_name}")
                    except Exception as e:
                        failed_count += 1
                        print(f"  错误: 项目 [{project.id}] {project.project_name} - {str(e)}")
                        db.session.rollback()
                
                # 批量提交
                try:
                    db.session.commit()
                    print(f"  批次完成，已提交")
                except Exception as e:
                    print(f"  批次提交失败: {str(e)}")
                    db.session.rollback()
            
            # 统计结果
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "=" * 50)
            print("更新完成")
            print("=" * 50)
            print(f"处理时间: {duration}")
            print(f"总计项目: {total_projects}")
            print(f"成功更新: {updated_count}")
            print(f"更新失败: {failed_count}")
            
            if failed_count > 0:
                print(f"⚠️  有 {failed_count} 个项目更新失败")
            else:
                print("✅ 所有项目评分更新成功!")
            
            # 显示更新后的统计
            print("\n当前评分分布:")
            score_stats = db.session.query(
                ProjectTotalScore.star_rating,
                db.func.count(ProjectTotalScore.id).label('count')
            ).group_by(ProjectTotalScore.star_rating).order_by(ProjectTotalScore.star_rating).all()
            
            for rating, count in score_stats:
                print(f"  {rating}星: {count} 个项目")
            
            return failed_count == 0
            
        except Exception as e:
            print(f"脚本执行失败: {str(e)}")
            return False

if __name__ == "__main__":
    success = quick_update_all_scores()
    sys.exit(0 if success else 1) 