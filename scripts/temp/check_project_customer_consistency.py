#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查项目表旧字段与ProjectCustomerAssociation新关联表的数据一致性"""
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
from app.models.project import Project
from app.models.project_customer_association import ProjectCustomerAssociation
from app.models.customer import Company

def main():
    app = create_app()
    with app.app_context():
        projects = Project.query.all()

        total_projects = len(projects)
        inconsistent_count = 0

        stats = {
            'old_missing_in_new': 0,
            'new_missing_in_old': 0,
            'old_invalid_id': 0,
            'old_whitespace': 0
        }

        details = []

        for project in projects:
            project_issues = []

            old_fields = {
                'end_user': project.end_user,
                'design_issues': project.design_issues,
                'dealer': project.dealer,
                'contractor': project.contractor,
                'system_integrator': project.system_integrator
            }

            associations = ProjectCustomerAssociation.query.filter_by(
                project_id=project.id
            ).all()

            new_associations = {}
            for assoc in associations:
                company = Company.query.get(assoc.company_id)
                if company:
                    if assoc.customer_type not in new_associations:
                        new_associations[assoc.customer_type] = []
                    new_associations[assoc.customer_type].append(company.company_name)

            for field_name, old_value in old_fields.items():
                if old_value:
                    old_value_clean = old_value.strip()
                    new_values = new_associations.get(field_name, [])

                    if old_value_clean.isdigit():
                        # 如果是ID，检查是否已通过ID转换找到公司并创建了关联
                        if not new_values:  # 只有新关联没有数据时才报告问题
                            stats['old_invalid_id'] += 1
                            project_issues.append({
                                'field': field_name,
                                'type': 'old_invalid_id',
                                'old_value': old_value,
                                'new_values': new_values
                            })
                    elif old_value != old_value_clean:
                        # 如果有空白字符，检查清理后的值是否在新关联中
                        if old_value_clean not in new_values:  # 清理后的值不在新关联中才报告问题
                            stats['old_whitespace'] += 1
                            project_issues.append({
                                'field': field_name,
                                'type': 'old_whitespace',
                                'old_value': old_value,
                                'new_values': new_values
                            })
                    elif old_value not in new_values:
                        stats['old_missing_in_new'] += 1
                        project_issues.append({
                            'field': field_name,
                            'type': 'old_missing_in_new',
                            'old_value': old_value,
                            'new_values': new_values
                        })

            for customer_type, company_names in new_associations.items():
                old_value = old_fields.get(customer_type)
                if company_names and not old_value:
                    stats['new_missing_in_old'] += 1
                    project_issues.append({
                        'field': customer_type,
                        'type': 'new_missing_in_old',
                        'old_value': old_value,
                        'new_values': company_names
                    })

            if project_issues:
                inconsistent_count += 1
                details.append({
                    'id': project.id,
                    'name': project.project_name,
                    'issues': project_issues
                })

        # 输出统计结果
        print(f'总项目数: {total_projects}')
        print(f'不一致项目数: {inconsistent_count}')
        print(f'一致性比例: {(total_projects - inconsistent_count) / total_projects * 100:.1f}%')
        print('\n问题类型统计:')
        print(f'  - 旧字段有值但新关联没有: {stats["old_missing_in_new"]} 个字段')
        print(f'  - 新关联有值但旧字段为空: {stats["new_missing_in_old"]} 个字段')
        print(f'  - 旧字段存储ID而非名称: {stats["old_invalid_id"]} 个字段')
        print(f'  - 旧字段包含空白字符: {stats["old_whitespace"]} 个字段')

        # 显示详细案例
        print('\n不一致详细案例（前10个）:')
        print('=' * 80)
        for detail in details[:10]:
            print(f'\n项目ID: {detail["id"]}')
            print(f'项目名称: {detail["name"]}')
            print('问题列表:')
            for issue in detail['issues']:
                print(f'  - 字段: {issue["field"]}')
                print(f'    类型: {issue["type"]}')
                print(f'    旧值: "{issue["old_value"]}"')
                print(f'    新关联: {issue["new_values"]}')

        if len(details) > 10:
            print(f'\n... 还有 {len(details) - 10} 个项目存在不一致')

if __name__ == '__main__':
    main()
