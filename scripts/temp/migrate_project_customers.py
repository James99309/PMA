#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目客户关联数据迁移修复脚本

功能：
1. 将项目表旧字段（end_user, design_issues等）中的数据迁移到ProjectCustomerAssociation新关联表
2. 清理旧字段中的脏数据（空白字符、ID值等）
3. 生成详细的修复日志和报告

使用方法：
    # 预览模式（不实际修改数据）
    python3 scripts/temp/migrate_project_customers.py --dry-run

    # 执行修复
    python3 scripts/temp/migrate_project_customers.py

    # 仅修复特定项目
    python3 scripts/temp/migrate_project_customers.py --project-id 629
"""

import sys
import os
import argparse
from datetime import datetime

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
from sqlalchemy import or_

class ProjectCustomerMigrator:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.stats = {
            'total_projects': 0,
            'processed_projects': 0,
            'fixed_fields': 0,
            'cleaned_whitespace': 0,
            'cleared_invalid_ids': 0,
            'created_associations': 0,
            'unmatched_companies': []
        }

    def log(self, message, level='INFO'):
        """输出日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = '[DRY-RUN] ' if self.dry_run else ''
        print(f'{timestamp} [{level}] {prefix}{message}')

    def clean_whitespace(self, value):
        """清理字符串中的空白字符"""
        if not value:
            return None
        cleaned = value.strip()
        if cleaned != value:
            self.stats['cleaned_whitespace'] += 1
            self.log(f'清理空白字符: "{value}" -> "{cleaned}"', 'DEBUG')
        return cleaned if cleaned else None

    def find_company(self, company_name):
        """查找公司，支持精确匹配和模糊匹配"""
        if not company_name:
            return None

        # 清理公司名称
        company_name = self.clean_whitespace(company_name)
        if not company_name:
            return None

        # 如果是纯数字ID，尝试通过ID查找
        if company_name.isdigit():
            company = Company.query.filter_by(id=int(company_name)).first()
            if company:
                self.log(f'通过ID匹配到公司: ID={company_name} -> {company.company_name}', 'DEBUG')
                return company
            else:
                self.log(f'无法通过ID找到公司: {company_name}', 'WARNING')
                self.stats['cleared_invalid_ids'] += 1
                return None

        # 精确匹配
        company = Company.query.filter_by(company_name=company_name, is_deleted=False).first()
        if company:
            return company

        # 模糊匹配
        company = Company.query.filter(
            Company.company_name.ilike(f'%{company_name}%'),
            Company.is_deleted == False
        ).first()

        if company:
            self.log(f'模糊匹配到公司: "{company_name}" -> {company.company_name}', 'DEBUG')
            return company

        # 未找到
        self.log(f'未找到匹配的公司: "{company_name}"', 'WARNING')
        self.stats['unmatched_companies'].append(company_name)
        return None

    def association_exists(self, project_id, company_id, customer_type):
        """检查关联是否已存在"""
        return ProjectCustomerAssociation.query.filter_by(
            project_id=project_id,
            company_id=company_id,
            customer_type=customer_type
        ).first() is not None

    def create_association(self, project_id, company_id, customer_type, created_by):
        """创建项目客户关联"""
        if self.association_exists(project_id, company_id, customer_type):
            self.log(f'关联已存在: project_id={project_id}, company_id={company_id}, type={customer_type}', 'DEBUG')
            return False

        if self.dry_run:
            self.log(f'[预览] 将创建关联: project_id={project_id}, company_id={company_id}, type={customer_type}')
            self.stats['created_associations'] += 1
            return True

        try:
            association = ProjectCustomerAssociation(
                project_id=project_id,
                company_id=company_id,
                customer_type=customer_type,
                created_by=created_by
            )
            db.session.add(association)
            self.stats['created_associations'] += 1
            self.log(f'创建关联成功: project_id={project_id}, company_id={company_id}, type={customer_type}')
            return True
        except Exception as e:
            self.log(f'创建关联失败: {e}', 'ERROR')
            return False

    def process_project(self, project):
        """处理单个项目"""
        self.log(f'处理项目 ID={project.id}: {project.project_name}')

        project_fixed = False
        old_fields = {
            'end_user': project.end_user,
            'design_issues': project.design_issues,
            'dealer': project.dealer,
            'contractor': project.contractor,
            'system_integrator': project.system_integrator
        }

        for field_name, old_value in old_fields.items():
            if not old_value:
                continue

            # 清理并查找公司
            company = self.find_company(old_value)
            if company:
                # 创建关联
                if self.create_association(
                    project_id=project.id,
                    company_id=company.id,
                    customer_type=field_name,
                    created_by=project.created_by
                ):
                    self.stats['fixed_fields'] += 1
                    project_fixed = True
            else:
                # 如果是无效ID，清空该字段
                if old_value.strip().isdigit():
                    self.log(f'清空无效ID字段: {field_name}="{old_value}"')
                    if not self.dry_run:
                        setattr(project, field_name, None)
                    project_fixed = True

        if project_fixed:
            self.stats['processed_projects'] += 1

        return project_fixed

    def run(self, project_id=None):
        """执行迁移"""
        self.log('=' * 80)
        self.log('开始项目客户关联数据迁移')
        self.log('=' * 80)

        if self.dry_run:
            self.log('⚠️  预览模式：不会实际修改数据库')

        try:
            # 查询需要处理的项目
            if project_id:
                projects = [Project.query.get(project_id)]
                if not projects[0]:
                    self.log(f'未找到项目ID: {project_id}', 'ERROR')
                    return False
            else:
                projects = Project.query.all()

            self.stats['total_projects'] = len(projects)
            self.log(f'共找到 {len(projects)} 个项目需要检查')

            # 开始事务
            for project in projects:
                self.process_project(project)

            # 提交或回滚
            if not self.dry_run:
                db.session.commit()
                self.log('✅ 数据库事务已提交')
            else:
                db.session.rollback()
                self.log('⚠️  预览模式：事务已回滚')

            # 输出统计报告
            self.print_report()

            return True

        except Exception as e:
            db.session.rollback()
            self.log(f'❌ 迁移失败，事务已回滚: {e}', 'ERROR')
            import traceback
            traceback.print_exc()
            return False

    def print_report(self):
        """输出迁移报告"""
        self.log('=' * 80)
        self.log('迁移报告')
        self.log('=' * 80)
        self.log(f'总项目数: {self.stats["total_projects"]}')
        self.log(f'已处理项目数: {self.stats["processed_projects"]}')
        self.log(f'修复字段数: {self.stats["fixed_fields"]}')
        self.log(f'清理空白字符: {self.stats["cleaned_whitespace"]}')
        self.log(f'清空无效ID: {self.stats["cleared_invalid_ids"]}')
        self.log(f'创建关联记录: {self.stats["created_associations"]}')

        if self.stats['unmatched_companies']:
            self.log('')
            self.log(f'⚠️  未匹配的公司名称 ({len(self.stats["unmatched_companies"])} 个):')
            for name in sorted(set(self.stats['unmatched_companies'])):
                self.log(f'  - "{name}"')
            self.log('')
            self.log('建议：请手动检查这些公司名称，可能需要：')
            self.log('  1. 在客户管理中创建对应的公司')
            self.log('  2. 或在项目详情页手动添加参与单位')

        self.log('=' * 80)

def main():
    parser = argparse.ArgumentParser(description='项目客户关联数据迁移修复脚本')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改数据')
    parser.add_argument('--project-id', type=int, help='仅处理指定项目ID')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        migrator = ProjectCustomerMigrator(dry_run=args.dry_run)
        success = migrator.run(project_id=args.project_id)

        if success:
            if args.dry_run:
                print('\n✅ 预览完成。如需执行修复，请移除 --dry-run 参数')
            else:
                print('\n✅ 迁移完成')
            sys.exit(0)
        else:
            print('\n❌ 迁移失败')
            sys.exit(1)

if __name__ == '__main__':
    main()
