#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""导入江苏+广东石化潜在项目情报"""
import sys, os
from datetime import datetime

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
from app.models.prospect_project import ProspectProject, ProspectStakeholder

PROJECTS = [
    {
        'project_name': '中国石油化工股份有限公司茂名分公司炼油转型升级及乙烯提质改造项目',
        'industry': 'chemical',
        'region': '广东',
        'city': '茂名',
        'stage': 'construction',
        'total_investment': '超300亿元',
        'source': 'ai',
        'keywords': ['石化', '炼油', '乙烯', 'EPC', '对讲机'],
        'description': '总投资超300亿元，112个主项，已开工59个（截至2025.03）。分布在高新技术产业园区 + 茂南石化工业园区，竣工时间2026年12月。仪表/电信系统可能在施工阶段招标。',
        'info_updated_by': 'AI调研',
        'stakeholders': [
            {'stakeholder_type': 'owner', 'company_name': '中国石油化工股份有限公司茂名分公司',
             'department': '工程管理部', 'city': '茂名'},
            {'stakeholder_type': 'epc', 'company_name': '中国石化南京工程有限公司',
             'department': '电信仪表部', 'notes': '负责茂名主要装置通信设计（500kt/y裂解汽油加氢、300kt/y芳烃抽提）'},
            {'stakeholder_type': 'epc', 'company_name': '中国石化上海工程有限公司',
             'notes': '140kt/y丁二烯装置'},
            {'stakeholder_type': 'design', 'company_name': '茂名瑞派石化工程公司',
             'notes': '本地设计院，联系相对容易'},
        ]
    },
    {
        'project_name': '广州石化安全绿色高质量发展技改项目',
        'industry': 'chemical',
        'region': '广东',
        'city': '广州',
        'stage': 'designing',
        'total_investment': None,
        'source': 'eia',
        'keywords': ['石化', '技改', '仪表', '环评已批'],
        'description': '广州市黄埔区，环评已批复（2025年），变电站EPC已招标。设计院：中石化系统设计院（广州石化工程院）。',
        'info_updated_by': 'AI调研',
        'stakeholders': [
            {'stakeholder_type': 'owner', 'company_name': '中国石油化工股份有限公司广州分公司',
             'city': '广州市黄埔区'},
            {'stakeholder_type': 'design', 'company_name': '广州石化工程院（中石化系统）'},
        ]
    },
    {
        'project_name': '广东石化揭阳炼化新建乙烯低温储罐项目',
        'industry': 'chemical',
        'region': '广东',
        'city': '揭阳',
        'stage': 'planning',
        'total_investment': None,
        'source': 'eia',
        'keywords': ['石化', '乙烯', '低温储罐', '环评'],
        'description': '3万立方米乙烯低温储罐，环评已批，2026年建设。位于揭阳市大南海石化工业区。广东石化有限责任公司（中委合资）。',
        'info_updated_by': 'AI调研',
        'stakeholders': [
            {'stakeholder_type': 'owner', 'company_name': '广东石化有限责任公司',
             'address': '揭阳市大南海石化工业区'},
        ]
    },
    {
        'project_name': '巴斯夫湛江一体化基地异构十三醇装置',
        'industry': 'chemical',
        'region': '广东',
        'city': '湛江',
        'stage': 'planning',
        'total_investment': '100亿欧元（一体化基地总投资）',
        'source': 'eia',
        'keywords': ['巴斯夫', '外资', '化工', '异构十三醇'],
        'description': '巴斯夫湛江一体化基地（总投资100亿欧元，持续建设至2030年代）。2025-2026新建3万吨/年异构十三醇装置（环评公示2025年9月）。外资项目沟通难度高，但持续有新装置上线。',
        'info_updated_by': 'AI调研',
        'stakeholders': [
            {'stakeholder_type': 'owner', 'company_name': '巴斯夫一体化基地（广东）有限公司',
             'city': '湛江市'},
        ]
    },
    {
        'project_name': '中国石化扬子石化分公司技术升级项目',
        'industry': 'chemical',
        'region': '江苏',
        'city': '南京',
        'stage': 'designing',
        'total_investment': None,
        'source': 'eia',
        'keywords': ['石化', '技改', '仪表通信', '省重大项目', '环评'],
        'description': '2026年江苏省重大项目，南京市大厂区，环评公示已完成（2025年1月）。技术升级项目，仪表通信系统通常同步改造，切入机会明确。',
        'info_updated_by': 'AI调研',
        'stakeholders': [
            {'stakeholder_type': 'owner', 'company_name': '中国石油化工股份有限公司扬子石化分公司',
             'city': '南京市大厂区'},
            {'stakeholder_type': 'design', 'company_name': '中国石化南京工程有限公司',
             'department': '电信仪表部', 'notes': '主设计院'},
        ]
    },
    {
        'project_name': '中国石化金陵分公司绿色转型升级项目',
        'industry': 'chemical',
        'region': '江苏',
        'city': '南京',
        'stage': 'planning',
        'total_investment': None,
        'source': 'ai',
        'keywords': ['石化', '绿色转型', '省重大项目'],
        'description': '2026年江苏省重大项目，南京市栖霞区。金陵石化绿色转型升级。',
        'info_updated_by': 'AI调研',
        'stakeholders': [
            {'stakeholder_type': 'owner', 'company_name': '中国石油化工股份有限公司金陵分公司',
             'city': '南京市栖霞区'},
        ]
    },
    {
        'project_name': '盛虹炼化（连云港）新材料扩建项目',
        'industry': 'chemical',
        'region': '江苏',
        'city': '连云港',
        'stage': 'construction',
        'total_investment': None,
        'source': 'ai',
        'keywords': ['炼化', '新材料', '民营', '扩建'],
        'description': '盛虹炼化（连云港）有限公司，已建成2600万吨/年，持续扩建新材料装置。位于连云港徐圩新区石化三路59号。大型民营炼化，采购相对灵活，多个装置同步建设。',
        'info_updated_by': 'AI调研',
        'stakeholders': [
            {'stakeholder_type': 'owner', 'company_name': '盛虹炼化（连云港）有限公司',
             'address': '连云港徐圩新区石化三路59号'},
        ]
    },
    {
        'project_name': '连云港石化高端新材料项目（α-烯烃+聚乙烯）',
        'industry': 'chemical',
        'region': '江苏',
        'city': '连云港',
        'stage': 'designing',
        'total_investment': '266亿元',
        'source': 'eia',
        'keywords': ['石化', '新材料', 'α-烯烃', '聚乙烯', '刚立项'],
        'description': '总投资266亿元，2025年11月获备案批复。2套10万吨/年α-烯烃 + 聚乙烯装置。刚立项，处于设计院介入早期阶段，最早介入对讲机系统设计的机会。',
        'info_updated_by': 'AI调研',
        'stakeholders': [
            {'stakeholder_type': 'owner', 'company_name': '连云港石化有限公司',
             'city': '连云港'},
            {'stakeholder_type': 'design', 'company_name': '华陆工程科技',
             'notes': '连云港项目设计院（待确认）'},
        ]
    },
]


def run():
    app = create_app()
    with app.app_context():
        now = datetime.utcnow()
        imported = 0
        skipped = 0

        for p_data in PROJECTS:
            # 检查是否已存在（按项目名）
            existing = ProspectProject.query.filter_by(
                project_name=p_data['project_name'],
                is_deleted=False
            ).first()
            if existing:
                print(f'  跳过（已存在）: {p_data["project_name"][:40]}')
                skipped += 1
                continue

            stakeholders_data = p_data.pop('stakeholders', [])

            p = ProspectProject(
                project_name=p_data['project_name'],
                industry=p_data.get('industry'),
                region=p_data.get('region'),
                city=p_data.get('city'),
                stage=p_data.get('stage', 'planning'),
                total_investment=p_data.get('total_investment'),
                description=p_data.get('description'),
                keywords=p_data.get('keywords'),
                source=p_data.get('source'),
                info_updated_by=p_data.get('info_updated_by'),
                info_updated_at=now,
                is_deleted=False,
                created_at=now,
                updated_at=now,
            )
            db.session.add(p)
            db.session.flush()  # 获取 p.id

            for s_data in stakeholders_data:
                s = ProspectStakeholder(
                    prospect_id=p.id,
                    stakeholder_type=s_data['stakeholder_type'],
                    company_name=s_data['company_name'],
                    department=s_data.get('department'),
                    address=s_data.get('address') or s_data.get('city'),
                    phone=s_data.get('phone'),
                    contact_person=s_data.get('contact_person'),
                    notes=s_data.get('notes'),
                )
                db.session.add(s)

            print(f'  导入: {p_data["project_name"][:50]} ({len(stakeholders_data)} 个关联方)')
            imported += 1

        db.session.commit()
        print(f'\n完成：导入 {imported} 个，跳过 {skipped} 个')


if __name__ == '__main__':
    run()
