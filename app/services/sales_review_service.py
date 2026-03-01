#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""销售评估数据聚合服务

通过 ORM 直接查询本地数据库，收集目标用户的 7 类业务数据，
返回结构化 dict 供报告生成器使用。
"""

import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone

from app import db
from app.models.user import User, Affiliation
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.quotation import Quotation, QuotationDetail
from app.models.worklog import WorkLog, WorkItem
from app.models.change_log import ChangeLog

logger = logging.getLogger(__name__)


class SalesReviewDataService:
    """销售评估数据采集服务"""

    @classmethod
    def collect_review_data(cls, target_user_id):
        """收集 7 类数据 + 统计聚合，返回结构化 dict"""
        user = User.query.get(target_user_id)
        if not user:
            raise ValueError(f'用户 ID {target_user_id} 不存在')

        data = {
            'user_profile': cls._collect_user_profile(user),
            'customers': cls._collect_customers(target_user_id),
            'contacts': cls._collect_contacts(target_user_id),
            'projects': cls._collect_projects(target_user_id),
            'quotations': cls._collect_quotations(target_user_id),
            'worklogs': cls._collect_worklogs(target_user_id),
            'change_logs': cls._collect_change_logs(target_user_id),
        }

        data['statistics'] = cls._compute_statistics(data)
        return data

    # ------------------------------------------------------------------
    # 1. 用户档案
    # ------------------------------------------------------------------
    @classmethod
    def _collect_user_profile(cls, user):
        """基本用户信息"""
        now_ts = datetime.now(timezone.utc).timestamp()
        created_ts = user.created_at or now_ts
        tenure_days = int((now_ts - created_ts) / 86400)

        # 查询下属关系
        subordinates = []
        affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
        for aff in affiliations:
            sub = User.query.get(aff.owner_id)
            if sub:
                subordinates.append({
                    'id': sub.id,
                    'name': sub.real_name or sub.username,
                    'role': sub.role,
                })

        return {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name or user.username,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'department': user.department,
            'company_name': user.company_name,
            'is_department_manager': user.is_department_manager,
            'created_at': datetime.fromtimestamp(created_ts, tz=timezone.utc).strftime('%Y-%m-%d'),
            'tenure_days': tenure_days,
            'tenure_months': round(tenure_days / 30, 1),
            'subordinates': subordinates,
        }

    # ------------------------------------------------------------------
    # 2. 客户（Company）
    # ------------------------------------------------------------------
    @classmethod
    def _collect_customers(cls, user_id):
        """收集用户名下所有客户"""
        companies = Company.query.filter(
            Company.owner_id == user_id,
            Company.is_deleted == False
        ).order_by(Company.created_at.desc()).all()

        results = []
        for c in companies:
            results.append({
                'id': c.id,
                'name': c.company_name,
                'type': c.company_type,
                'industry': c.industry,
                'country': c.country,
                'region': c.region,
                'city': c.city,
                'status': c.status,
                'source': c.source,
                'created_at': c.created_at.strftime('%Y-%m-%d') if c.created_at else None,
            })
        return results

    # ------------------------------------------------------------------
    # 3. 联系人（Contact）
    # ------------------------------------------------------------------
    @classmethod
    def _collect_contacts(cls, user_id):
        """收集用户名下所有联系人"""
        contacts = Contact.query.filter_by(owner_id=user_id).order_by(
            Contact.created_at.desc()
        ).all()

        results = []
        for ct in contacts:
            company_name = ''
            if ct.company_id:
                company = Company.query.get(ct.company_id)
                if company:
                    company_name = company.company_name
            results.append({
                'id': ct.id,
                'name': ct.name,
                'company_id': ct.company_id,
                'company_name': company_name,
                'department': ct.department,
                'position': ct.position,
                'phone': ct.phone,
                'email': ct.email,
                'is_primary': ct.is_primary,
                'created_at': ct.created_at.strftime('%Y-%m-%d') if ct.created_at else None,
            })
        return results

    # ------------------------------------------------------------------
    # 4. 项目（Project）
    # ------------------------------------------------------------------
    @classmethod
    def _collect_projects(cls, user_id):
        """收集用户创建的和名下的项目"""
        # 包含 created_by 和 owner_id 两种关系
        projects = Project.query.filter(
            db.or_(
                Project.created_by == user_id,
                Project.owner_id == user_id,
            )
        ).order_by(Project.created_at.desc()).all()

        results = []
        for p in projects:
            creator_name = ''
            owner_name = ''
            if p.created_by:
                creator = User.query.get(p.created_by)
                if creator:
                    creator_name = creator.real_name or creator.username
            if p.owner_id:
                owner = User.query.get(p.owner_id)
                if owner:
                    owner_name = owner.real_name or owner.username

            results.append({
                'id': p.id,
                'name': p.project_name,
                'industry': p.industry,
                'stage': p.current_stage,
                'project_type': p.project_type,
                'report_source': p.report_source,
                'quotation_amount': p.quotation_customer,
                'quotation_currency': p.quotation_currency or 'CNY',
                'country': p.country,
                'region': p.region,
                'city': p.city,
                'rating': p.rating,
                'status': p.status,
                'is_active': p.is_active,
                'created_by': p.created_by,
                'created_by_name': creator_name,
                'owner_id': p.owner_id,
                'owner_name': owner_name,
                'is_self_created': p.created_by == user_id,
                'report_time': p.report_time.strftime('%Y-%m-%d') if p.report_time else None,
                'delivery_forecast': p.delivery_forecast.strftime('%Y-%m-%d') if p.delivery_forecast else None,
                'created_at': p.created_at.strftime('%Y-%m-%d') if p.created_at else None,
            })
        return results

    # ------------------------------------------------------------------
    # 5. 报价（Quotation）
    # ------------------------------------------------------------------
    @classmethod
    def _collect_quotations(cls, user_id):
        """收集用户名下的报价"""
        quotations = Quotation.query.filter_by(owner_id=user_id).order_by(
            Quotation.created_at.desc()
        ).all()

        results = []
        for q in quotations:
            # 获取关联信息
            project_name = ''
            customer_name = ''
            if q.project_id:
                project = Project.query.get(q.project_id)
                if project:
                    project_name = project.project_name
            if q.customer_id:
                customer = Company.query.get(q.customer_id)
                if customer:
                    customer_name = customer.company_name

            # 获取报价明细
            details = QuotationDetail.query.filter_by(quotation_id=q.id).all()
            detail_list = []
            for d in details:
                detail_list.append({
                    'product_name': d.product_name,
                    'product_model': d.product_model,
                    'brand': d.brand,
                    'quantity': d.quantity,
                    'unit_price': d.unit_price,
                    'total_price': d.total_price,
                })

            results.append({
                'id': q.id,
                'quotation_number': q.quotation_number,
                'project_id': q.project_id,
                'project_name': project_name,
                'customer_id': q.customer_id,
                'customer_name': customer_name,
                'amount': q.amount,
                'currency': q.currency or 'CNY',
                'project_stage': q.project_stage,
                'project_type': q.project_type,
                'approval_status': q.approval_status,
                'implant_total_amount': q.implant_total_amount,
                'details': detail_list,
                'created_at': q.created_at.strftime('%Y-%m-%d') if q.created_at else None,
            })

        # 同时查询跨团队报价（目标用户创建的项目中，由其他人出的报价）
        self_created_project_ids = [
            p.id for p in Project.query.filter_by(created_by=user_id).all()
        ]
        cross_team_quotations = []
        if self_created_project_ids:
            cross_q = Quotation.query.filter(
                Quotation.project_id.in_(self_created_project_ids),
                Quotation.owner_id != user_id,
            ).order_by(Quotation.created_at.desc()).all()
            for q in cross_q:
                owner_name = ''
                if q.owner_id:
                    owner = User.query.get(q.owner_id)
                    if owner:
                        owner_name = owner.real_name or owner.username
                proj = Project.query.get(q.project_id) if q.project_id else None
                cross_team_quotations.append({
                    'id': q.id,
                    'quotation_number': q.quotation_number,
                    'project_name': proj.project_name if proj else '',
                    'amount': q.amount,
                    'currency': q.currency or 'CNY',
                    'owner_id': q.owner_id,
                    'owner_name': owner_name,
                    'project_stage': q.project_stage,
                    'created_at': q.created_at.strftime('%Y-%m-%d') if q.created_at else None,
                })

        return {
            'own_quotations': results,
            'cross_team_quotations': cross_team_quotations,
        }

    # ------------------------------------------------------------------
    # 6. 工作日志（WorkLog + WorkItem）
    # ------------------------------------------------------------------
    @classmethod
    def _collect_worklogs(cls, user_id):
        """收集用户的工作日志和工作项"""
        worklogs = WorkLog.query.filter_by(owner_id=user_id).order_by(
            WorkLog.log_date.desc()
        ).all()

        log_results = []
        for wl in worklogs:
            log_results.append({
                'id': wl.id,
                'log_date': wl.log_date.strftime('%Y-%m-%d') if wl.log_date else None,
                'log_type': wl.log_type,
                'status': wl.status,
                'total_hours': wl.total_hours,
                'summary': wl.summary,
                'submitted_at': wl.submitted_at.strftime('%Y-%m-%d %H:%M') if wl.submitted_at else None,
            })

        # 工作项
        work_items = WorkItem.query.filter(
            WorkItem.owner_id == user_id,
            WorkItem.is_deleted == False,
        ).order_by(WorkItem.planned_date.desc()).all()

        item_results = []
        for wi in work_items:
            project_name = ''
            customer_name = ''
            if wi.project_id:
                project = Project.query.get(wi.project_id)
                if project:
                    project_name = project.project_name
            if wi.customer_id:
                customer = Company.query.get(wi.customer_id)
                if customer:
                    customer_name = customer.company_name

            item_results.append({
                'id': wi.id,
                'title': wi.title,
                'description': wi.description,
                'work_type': wi.work_type,
                'planned_date': wi.planned_date.strftime('%Y-%m-%d') if wi.planned_date else None,
                'end_date': wi.end_date.strftime('%Y-%m-%d') if wi.end_date else None,
                'estimated_hours': wi.estimated_hours,
                'actual_hours': wi.actual_hours,
                'status': wi.status,
                'project_id': wi.project_id,
                'project_name': project_name,
                'customer_id': wi.customer_id,
                'customer_name': customer_name,
                'execution_notes': wi.execution_notes,
                'is_business_trip': wi.is_business_trip,
            })

        return {
            'worklogs': log_results,
            'work_items': item_results,
        }

    # ------------------------------------------------------------------
    # 7. 操作日志（ChangeLog）
    # ------------------------------------------------------------------
    @classmethod
    def _collect_change_logs(cls, user_id):
        """收集用户的系统操作日志（最近500条）"""
        logs = ChangeLog.query.filter_by(user_id=user_id).order_by(
            ChangeLog.created_at.desc()
        ).limit(500).all()

        results = []
        for cl in logs:
            results.append({
                'module_name': cl.module_name,
                'operation_type': cl.operation_type,
                'field_name': cl.field_name,
                'record_info': cl.record_info,
                'created_at': cl.created_at.strftime('%Y-%m-%d %H:%M') if cl.created_at else None,
            })
        return results

    # ------------------------------------------------------------------
    # 统计聚合
    # ------------------------------------------------------------------
    @classmethod
    def _compute_statistics(cls, data):
        """根据已收集的数据计算统计指标"""
        stats = {}

        # --- 客户统计 ---
        customers = data['customers']
        stats['customer_count'] = len(customers)
        stats['customer_type_distribution'] = dict(Counter(
            c['type'] for c in customers if c.get('type')
        ))
        stats['customer_industry_distribution'] = dict(Counter(
            c['industry'] for c in customers if c.get('industry')
        ))
        stats['customer_region_distribution'] = dict(Counter(
            (c.get('region') or c.get('city') or c.get('country') or '未知')
            for c in customers
        ))

        # 客户创建时间分布（按月）
        month_dist = defaultdict(int)
        for c in customers:
            if c.get('created_at'):
                month_dist[c['created_at'][:7]] += 1
        stats['customer_creation_monthly'] = dict(sorted(month_dist.items()))

        # --- 联系人统计 ---
        contacts = data['contacts']
        stats['contact_count'] = len(contacts)
        # 每家公司的联系人数量
        company_contact_count = Counter(
            ct['company_name'] for ct in contacts if ct.get('company_name')
        )
        stats['contacts_per_company'] = dict(
            company_contact_count.most_common(20)
        )

        # --- 项目统计 ---
        projects = data['projects']
        stats['project_count'] = len(projects)
        stats['self_created_project_count'] = sum(
            1 for p in projects if p.get('is_self_created')
        )
        stats['project_stage_distribution'] = dict(Counter(
            p['stage'] for p in projects if p.get('stage')
        ))
        stats['project_industry_distribution'] = dict(Counter(
            p['industry'] for p in projects if p.get('industry')
        ))

        # 项目金额汇总（按币种）
        amount_by_currency = defaultdict(float)
        for p in projects:
            if p.get('quotation_amount'):
                currency = p.get('quotation_currency', 'CNY')
                amount_by_currency[currency] += p['quotation_amount']
        stats['project_amount_by_currency'] = dict(amount_by_currency)

        # 活跃 pipeline（排除 signed/delivered/lost 的项目）
        pipeline_stages = {'discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted'}
        pipeline = [p for p in projects if p.get('stage') in pipeline_stages]
        stats['active_pipeline_count'] = len(pipeline)
        pipeline_amount = defaultdict(float)
        for p in pipeline:
            if p.get('quotation_amount'):
                currency = p.get('quotation_currency', 'CNY')
                pipeline_amount[currency] += p['quotation_amount']
        stats['active_pipeline_amount'] = dict(pipeline_amount)

        # --- 报价统计 ---
        own_q = data['quotations']['own_quotations']
        cross_q = data['quotations']['cross_team_quotations']
        stats['own_quotation_count'] = len(own_q)
        stats['cross_team_quotation_count'] = len(cross_q)
        own_amount = defaultdict(float)
        for q in own_q:
            if q.get('amount'):
                own_amount[q.get('currency', 'CNY')] += q['amount']
        stats['own_quotation_amount'] = dict(own_amount)
        cross_amount = defaultdict(float)
        for q in cross_q:
            if q.get('amount'):
                cross_amount[q.get('currency', 'CNY')] += q['amount']
        stats['cross_team_quotation_amount'] = dict(cross_amount)

        # --- 工作日志统计 ---
        wl_data = data['worklogs']
        worklogs = wl_data['worklogs']
        work_items = wl_data['work_items']
        stats['worklog_count'] = len(worklogs)
        stats['worklog_submitted_count'] = sum(
            1 for wl in worklogs if wl.get('status') == 'submitted'
        )
        stats['worklog_draft_count'] = sum(
            1 for wl in worklogs if wl.get('status') == 'draft'
        )
        stats['worklog_submit_rate'] = (
            f"{stats['worklog_submitted_count'] / stats['worklog_count'] * 100:.0f}%"
            if stats['worklog_count'] > 0 else '0%'
        )
        stats['work_item_count'] = len(work_items)
        stats['work_type_distribution'] = dict(Counter(
            wi['work_type'] for wi in work_items if wi.get('work_type')
        ))
        stats['total_actual_hours'] = sum(
            wi.get('actual_hours') or 0 for wi in work_items
        )
        stats['business_trip_count'] = sum(
            1 for wi in work_items if wi.get('is_business_trip')
        )

        # --- 变更日志统计 ---
        change_logs = data['change_logs']
        stats['change_log_count'] = len(change_logs)
        stats['change_log_module_distribution'] = dict(Counter(
            cl['module_name'] for cl in change_logs if cl.get('module_name')
        ))
        stats['change_log_operation_distribution'] = dict(Counter(
            cl['operation_type'] for cl in change_logs if cl.get('operation_type')
        ))

        return stats
