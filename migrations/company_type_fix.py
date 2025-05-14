#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
企业类型字段值迁移脚本
将 Company 表中的 company_type 字段从中文值迁移为标准英文 key
"""

from app import create_app, db
from app.models.customer import Company
from sqlalchemy import text

# 映射关系: 中文值对应标准英文key
TYPE_MAPPING = {
    '用户': 'user',
    '经销商': 'dealer',
    '系统集成商': 'integrator',
    '设计院及顾问': 'designer',
    '总承包单位': 'contractor'
}

def migrate_company_types():
    """将公司类型从中文值更新为标准英文key"""
    print("开始迁移企业类型字段...")
    
    app = create_app()
    with app.app_context():
        # 获取所有企业记录
        companies = Company.query.all()
        updated_count = 0
        
        for company in companies:
            old_type = company.company_type
            if old_type in TYPE_MAPPING:
                company.company_type = TYPE_MAPPING[old_type]
                updated_count += 1
        
        if updated_count > 0:
            print(f"共有 {updated_count} 条记录需要更新，提交到数据库中...")
            db.session.commit()
            print("迁移完成!")
        else:
            print("没有需要更新的记录，企业类型已经是标准格式。")

        # 打印报告
        print("\n统计报告:")
        for old_type, new_type in TYPE_MAPPING.items():
            count = Company.query.filter_by(company_type=new_type).count()
            print(f"  {old_type} -> {new_type}: {count} 条记录")

if __name__ == '__main__':
    migrate_company_types() 