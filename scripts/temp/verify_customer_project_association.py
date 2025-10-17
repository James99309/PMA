#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证客户-项目关联关系的双向一致性"""
import sys
import os

# 路径修正 - 支持从任何位置运行
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
from app.models.customer import Company
from app.models.project import Project
from app.models.project_customer_association import ProjectCustomerAssociation

def verify_bidirectional_consistency():
    """验证双向关联关系的一致性"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("客户-项目关联关系双向一致性验证")
        print("=" * 80)

        # 统计总数
        total_companies = Company.query.filter_by(is_deleted=False).count()
        total_projects = Project.query.count()
        total_associations = ProjectCustomerAssociation.query.count()

        print(f"\n📊 数据统计:")
        print(f"  - 客户总数: {total_companies}")
        print(f"  - 项目总数: {total_projects}")
        print(f"  - 关联关系总数: {total_associations}")

        # 测试1: 从项目查客户
        print("\n" + "=" * 80)
        print("测试1: 从项目查询关联客户（使用关系表）")
        print("=" * 80)

        # 随机选择3个有关联的项目
        projects_with_associations = db.session.query(Project).join(
            ProjectCustomerAssociation,
            Project.id == ProjectCustomerAssociation.project_id
        ).limit(3).all()

        for project in projects_with_associations:
            associations = ProjectCustomerAssociation.query.filter_by(
                project_id=project.id
            ).all()

            print(f"\n项目: {project.project_name} (ID: {project.id})")
            print(f"  关联客户数: {len(associations)}")
            for assoc in associations:
                if assoc.company:
                    print(f"    - {assoc.company.company_name} ({assoc.customer_type_label})")

        # 测试2: 从客户查项目
        print("\n" + "=" * 80)
        print("测试2: 从客户查询关联项目（使用关系表）")
        print("=" * 80)

        # 随机选择3个有关联的客户
        companies_with_associations = db.session.query(Company).join(
            ProjectCustomerAssociation,
            Company.id == ProjectCustomerAssociation.company_id
        ).filter(Company.is_deleted == False).limit(3).all()

        for company in companies_with_associations:
            associations = ProjectCustomerAssociation.query.filter_by(
                company_id=company.id
            ).all()

            print(f"\n客户: {company.company_name} (ID: {company.id})")
            print(f"  关联项目数: {len(associations)}")
            for assoc in associations:
                if assoc.project:
                    print(f"    - {assoc.project.project_name} (类型: {assoc.customer_type_label})")

        # 测试3: 验证双向一致性
        print("\n" + "=" * 80)
        print("测试3: 验证双向关系一致性")
        print("=" * 80)

        inconsistencies = []

        # 从项目角度检查
        all_associations = ProjectCustomerAssociation.query.all()
        for assoc in all_associations:
            # 检查项目是否存在
            if not assoc.project:
                inconsistencies.append(f"关联ID {assoc.id}: 项目ID {assoc.project_id} 不存在")
                continue

            # 检查客户是否存在
            if not assoc.company:
                inconsistencies.append(f"关联ID {assoc.id}: 客户ID {assoc.company_id} 不存在")
                continue

            # 检查客户是否已删除
            if assoc.company.is_deleted:
                inconsistencies.append(f"关联ID {assoc.id}: 客户 {assoc.company.company_name} 已被标记删除")

        if inconsistencies:
            print(f"\n⚠️ 发现 {len(inconsistencies)} 个数据不一致问题:")
            for issue in inconsistencies[:10]:  # 只显示前10个
                print(f"  - {issue}")
            if len(inconsistencies) > 10:
                print(f"  ... 还有 {len(inconsistencies) - 10} 个问题")
        else:
            print("\n✅ 所有关联关系数据一致性良好！")

        # 测试4: 检查是否有孤立的旧式关联
        print("\n" + "=" * 80)
        print("测试4: 检查是否存在旧式字符串匹配的项目")
        print("=" * 80)

        # 获取所有客户名称
        company_names = {c.company_name for c in Company.query.filter_by(is_deleted=False).all()}

        # 检查项目中是否有客户名称字段但没有关联表记录的情况
        orphan_count = 0
        sample_orphans = []

        for project in Project.query.limit(100).all():  # 检查前100个项目
            # 检查项目的字符串字段中是否包含客户名称
            fields_with_values = []
            if project.end_user and project.end_user in company_names:
                fields_with_values.append(('end_user', project.end_user))
            if project.dealer and project.dealer in company_names:
                fields_with_values.append(('dealer', project.dealer))
            if project.contractor and project.contractor in company_names:
                fields_with_values.append(('contractor', project.contractor))
            if project.system_integrator and project.system_integrator in company_names:
                fields_with_values.append(('system_integrator', project.system_integrator))

            # 检查是否有对应的关联表记录
            if fields_with_values:
                for field_name, company_name in fields_with_values:
                    company = Company.query.filter_by(company_name=company_name, is_deleted=False).first()
                    if company:
                        assoc = ProjectCustomerAssociation.query.filter_by(
                            project_id=project.id,
                            company_id=company.id
                        ).first()

                        if not assoc:
                            orphan_count += 1
                            if len(sample_orphans) < 5:
                                sample_orphans.append({
                                    'project': project.project_name,
                                    'field': field_name,
                                    'company': company_name
                                })

        if orphan_count > 0:
            print(f"\n⚠️ 发现 {orphan_count} 个项目有客户字段但缺少关联表记录")
            print("示例:")
            for orphan in sample_orphans:
                print(f"  - 项目: {orphan['project']}")
                print(f"    字段: {orphan['field']} = {orphan['company']}")
                print(f"    建议: 创建关联表记录")
        else:
            print("\n✅ 未发现旧式字符串关联（前100个项目检查）")

        print("\n" + "=" * 80)
        print("验证完成")
        print("=" * 80)

if __name__ == '__main__':
    verify_bidirectional_consistency()
