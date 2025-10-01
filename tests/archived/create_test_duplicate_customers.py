#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建测试用的重复客户数据
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.customer import Company, Contact
from app.models.action import Action
from app.models.user import User
from datetime import datetime, date

def create_test_data():
    """创建测试用的重复客户数据"""
    
    app = create_app()
    with app.app_context():
        try:
            # 获取或创建一个测试用户
            test_user = User.query.filter_by(username='admin').first()
            if not test_user:
                print("未找到admin用户，请先创建管理员用户")
                return
            
            # 创建重复的客户数据组1：苹果公司
            companies_group1 = [
                {
                    'company_name': '苹果公司',
                    'company_code': 'APPLE001',
                    'country': 'US',
                    'region': 'California',
                    'industry': 'technology',
                    'company_type': '用户',
                    'status': 'active',
                    'owner_id': test_user.id
                },
                {
                    'company_name': '苹果有限公司',
                    'company_code': 'APPLE002',
                    'country': 'US',
                    'region': 'California',
                    'industry': 'technology',
                    'company_type': '用户',
                    'status': 'active',
                    'owner_id': test_user.id
                },
                {
                    'company_name': 'Apple Inc',
                    'company_code': 'APPLE003',
                    'country': 'US',
                    'region': 'California',
                    'industry': 'technology',
                    'company_type': '用户',
                    'status': 'active',
                    'owner_id': test_user.id
                }
            ]
            
            # 创建重复的客户数据组2：华为公司
            companies_group2 = [
                {
                    'company_name': '华为技术有限公司',
                    'company_code': 'HW001',
                    'country': 'CN',
                    'region': '广东省',
                    'industry': 'technology',
                    'company_type': '用户',
                    'status': 'active',
                    'owner_id': test_user.id
                },
                {
                    'company_name': '华为科技',
                    'company_code': 'HW002',
                    'country': 'CN',
                    'region': '广东省',
                    'industry': 'technology',
                    'company_type': '用户',
                    'status': 'active',
                    'owner_id': test_user.id
                },
                {
                    'company_name': '华为公司',
                    'company_code': 'HW003',
                    'country': 'CN',
                    'region': '广东省',
                    'industry': 'technology',
                    'company_type': '用户',
                    'status': 'active',
                    'owner_id': test_user.id
                }
            ]
            
            all_test_companies = companies_group1 + companies_group2
            created_companies = []
            
            # 创建公司记录
            for company_data in all_test_companies:
                # 检查是否已存在相同名称的公司
                existing = Company.query.filter_by(company_name=company_data['company_name']).first()
                if existing:
                    print(f"公司 '{company_data['company_name']}' 已存在，跳过创建")
                    created_companies.append(existing)
                    continue
                
                company = Company(**company_data)
                db.session.add(company)
                db.session.flush()  # 获取ID但不提交
                created_companies.append(company)
                print(f"创建公司: {company.company_name} (ID: {company.id})")
            
            # 为每个公司创建联系人
            contact_names = ['张三', '李四', '王五', 'John Smith', 'Jane Doe', 'Mike Johnson']
            for i, company in enumerate(created_companies):
                # 每个公司创建1-2个联系人
                num_contacts = 1 if i % 2 == 0 else 2
                for j in range(num_contacts):
                    contact_name = contact_names[(i + j) % len(contact_names)]
                    contact = Contact(
                        company_id=company.id,
                        name=contact_name,
                        department='技术部' if j == 0 else '销售部',
                        position='经理' if j == 0 else '主管',
                        phone=f'1380000{i:04d}',
                        email=f'{contact_name.lower().replace(" ", ".")}@{company.company_name.lower()}.com',
                        is_primary=(j == 0),
                        owner_id=test_user.id
                    )
                    db.session.add(contact)
                    print(f"  创建联系人: {contact.name}")
            
            # 为每个公司创建行动记录
            for i, company in enumerate(created_companies):
                # 每个公司创建1-3个行动记录
                num_actions = (i % 3) + 1
                for j in range(num_actions):
                    action = Action(
                        date=date.today(),
                        company_id=company.id,
                        communication=f'与{company.company_name}的第{j+1}次沟通记录，讨论技术合作事宜。',
                        owner_id=test_user.id
                    )
                    db.session.add(action)
                    print(f"  创建行动记录: 第{j+1}次沟通")
            
            # 提交所有更改
            db.session.commit()
            print(f"\n✅ 成功创建测试数据！")
            print(f"创建了 {len(created_companies)} 个公司记录")
            print(f"苹果公司组: {len(companies_group1)} 个")
            print(f"华为公司组: {len(companies_group2)} 个")
            print(f"\n现在可以使用客户合并工具进行测试了！")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建测试数据失败: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_test_data()