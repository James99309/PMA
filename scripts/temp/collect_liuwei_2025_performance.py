#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采集 liuwei 2025年度业绩数据（中国NAS SP8D数据库）
用于解决方案经理绩效评估

采集维度：
1. 报价单（全部 + 有确认徽章的）- 数量、金额、植入产品Top5
2. 批价单 - 数量、金额、产品Top5
3. 项目关联情况 - 作为owner/vendor_sales_manager的项目
4. 行动记录 - 数量、频率、关联项目
5. 工作日志 - 工作项数量
6. 与销售的配合度分析
"""
import sys
import os
from collections import defaultdict

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
os.environ['PMA_DB_TYPE'] = 'sp8d'

from app import create_app, db
from sqlalchemy import func, case, extract, and_, or_, text

app = create_app()

def main():
    with app.app_context():
        from app.models.user import User
        from app.models.quotation import Quotation, QuotationDetail
        from app.models.pricing_order import PricingOrder, PricingOrderDetail
        from app.models.project import Project
        from app.models.action import Action
        from app.models.worklog import WorkItem
        from app.models.product import Product

        # ========== 1. 查找用户 ==========
        user = User.query.filter(func.lower(User.username) == 'liuwei').first()
        if not user:
            print("❌ 找不到用户 liuwei")
            # 模糊搜索
            candidates = User.query.filter(User.username.ilike('%liu%')).all()
            for c in candidates:
                print(f"  候选: {c.username} (id={c.id}, real_name={c.real_name})")
            return

        print(f"{'='*80}")
        print(f"用户: {user.username} (ID={user.id}, 姓名={user.real_name})")
        print(f"角色: {user.role if hasattr(user, 'role') else 'N/A'}")
        print(f"{'='*80}")

        # 2025年时间范围
        year_start = '2025-01-01'
        year_end = '2025-12-31 23:59:59'

        # ========== 2. 报价单分析 ==========
        print(f"\n{'='*80}")
        print("📋 一、报价单（Quotation）分析")
        print(f"{'='*80}")

        # 2a. liuwei作为owner的报价单
        quotations_as_owner = Quotation.query.filter(
            Quotation.owner_id == user.id,
            Quotation.created_at >= year_start,
            Quotation.created_at <= year_end
        ).all()

        print(f"\n--- 2a. 作为报价单Owner ---")
        print(f"报价单总数: {len(quotations_as_owner)}")
        if quotations_as_owner:
            total_amount = sum(q.amount or 0 for q in quotations_as_owner)
            total_implant = sum(q.implant_total_amount or 0 for q in quotations_as_owner)
            print(f"报价总金额: {total_amount:,.2f}")
            print(f"植入总金额: {total_implant:,.2f}")

            # 有确认徽章的
            confirmed = [q for q in quotations_as_owner if q.confirmation_badge_status == 'confirmed']
            pending = [q for q in quotations_as_owner if q.confirmation_badge_status == 'pending']
            print(f"已确认: {len(confirmed)} 份")
            print(f"待确认: {len(pending)} 份")
            print(f"无徽章: {len(quotations_as_owner) - len(confirmed) - len(pending)} 份")

        # 2b. liuwei作为确认人的报价单
        quotations_confirmed_by = Quotation.query.filter(
            Quotation.confirmed_by == user.id,
            Quotation.confirmed_at >= year_start,
            Quotation.confirmed_at <= year_end
        ).all()

        print(f"\n--- 2b. 作为报价单确认人（confirmed_by）---")
        print(f"确认的报价单总数: {len(quotations_confirmed_by)}")
        if quotations_confirmed_by:
            total_amount_confirmed = sum(q.amount or 0 for q in quotations_confirmed_by)
            total_implant_confirmed = sum(q.implant_total_amount or 0 for q in quotations_confirmed_by)
            print(f"确认报价单总金额: {total_amount_confirmed:,.2f}")
            print(f"确认报价单植入总额: {total_implant_confirmed:,.2f}")

            # 按月份分布
            monthly = defaultdict(int)
            for q in quotations_confirmed_by:
                if q.confirmed_at:
                    monthly[q.confirmed_at.month] += 1
            print(f"月份分布: {dict(sorted(monthly.items()))}")

        # 2c. 所有2025年报价单中liuwei相关的（owner或confirmed_by）
        all_related_quotations = Quotation.query.filter(
            or_(
                Quotation.owner_id == user.id,
                Quotation.confirmed_by == user.id
            ),
            Quotation.created_at >= year_start,
            Quotation.created_at <= year_end
        ).all()

        print(f"\n--- 2c. 所有关联报价单（owner或确认人）---")
        print(f"关联报价单总数: {len(all_related_quotations)}")

        # 有确认徽章的报价单
        all_confirmed = [q for q in all_related_quotations if q.confirmation_badge_status == 'confirmed']
        print(f"其中有确认徽章: {len(all_confirmed)} 份")
        if all_confirmed:
            confirmed_amount = sum(q.amount or 0 for q in all_confirmed)
            confirmed_implant = sum(q.implant_total_amount or 0 for q in all_confirmed)
            print(f"确认报价单金额合计: {confirmed_amount:,.2f}")
            print(f"确认报价单植入合计: {confirmed_implant:,.2f}")

        # 2d. 报价单中植入产品Top5（按金额）
        print(f"\n--- 2d. 植入产品Top5（按植入金额）---")
        # 获取所有关联报价单ID
        related_q_ids = [q.id for q in all_related_quotations]
        if related_q_ids:
            product_implant = defaultdict(lambda: {'amount': 0, 'quantity': 0, 'count': 0})
            details = QuotationDetail.query.filter(
                QuotationDetail.quotation_id.in_(related_q_ids),
                QuotationDetail.implant_subtotal > 0
            ).all()

            for d in details:
                key = d.product_mn or d.product_name or 'Unknown'
                product_implant[key]['amount'] += d.implant_subtotal or 0
                product_implant[key]['quantity'] += d.quantity or 0
                product_implant[key]['count'] += 1
                if 'name' not in product_implant[key]:
                    product_implant[key]['name'] = d.product_name or key

            sorted_by_amount = sorted(product_implant.items(), key=lambda x: x[1]['amount'], reverse=True)
            print(f"有植入的产品总数: {len(sorted_by_amount)}")
            print(f"\nTop5 按植入金额:")
            for i, (mn, info) in enumerate(sorted_by_amount[:5], 1):
                print(f"  {i}. {mn} ({info['name']}) - 金额: {info['amount']:,.2f}, 数量: {info['quantity']}, 出现次数: {info['count']}")

            print(f"\nTop5 按植入数量:")
            sorted_by_qty = sorted(product_implant.items(), key=lambda x: x[1]['quantity'], reverse=True)
            for i, (mn, info) in enumerate(sorted_by_qty[:5], 1):
                print(f"  {i}. {mn} ({info['name']}) - 数量: {info['quantity']}, 金额: {info['amount']:,.2f}, 出现次数: {info['count']}")

        # 2e. 确认徽章报价单的植入产品Top5
        print(f"\n--- 2e. 有确认徽章报价单的植入产品Top5 ---")
        confirmed_q_ids = [q.id for q in all_confirmed]
        if confirmed_q_ids:
            product_implant_confirmed = defaultdict(lambda: {'amount': 0, 'quantity': 0, 'count': 0})
            details_confirmed = QuotationDetail.query.filter(
                QuotationDetail.quotation_id.in_(confirmed_q_ids),
                QuotationDetail.implant_subtotal > 0
            ).all()

            for d in details_confirmed:
                key = d.product_mn or d.product_name or 'Unknown'
                product_implant_confirmed[key]['amount'] += d.implant_subtotal or 0
                product_implant_confirmed[key]['quantity'] += d.quantity or 0
                product_implant_confirmed[key]['count'] += 1
                if 'name' not in product_implant_confirmed[key]:
                    product_implant_confirmed[key]['name'] = d.product_name or key

            sorted_confirmed = sorted(product_implant_confirmed.items(), key=lambda x: x[1]['amount'], reverse=True)
            print(f"有植入的产品总数: {len(sorted_confirmed)}")
            print(f"\nTop5 按植入金额:")
            for i, (mn, info) in enumerate(sorted_confirmed[:5], 1):
                print(f"  {i}. {mn} ({info['name']}) - 金额: {info['amount']:,.2f}, 数量: {info['quantity']}, 出现次数: {info['count']}")
        else:
            print("无确认徽章的报价单")

        # ========== 3. 批价单分析 ==========
        print(f"\n{'='*80}")
        print("📦 二、批价单（PricingOrder）分析")
        print(f"{'='*80}")

        # 3a. liuwei创建的批价单
        pricing_orders = PricingOrder.query.filter(
            PricingOrder.created_by == user.id,
            PricingOrder.created_at >= year_start,
            PricingOrder.created_at <= year_end
        ).all()

        print(f"\n--- 3a. 作为创建人的批价单 ---")
        print(f"批价单总数: {len(pricing_orders)}")
        if pricing_orders:
            approved = [po for po in pricing_orders if po.status == 'approved']
            print(f"已批准: {len(approved)} 份")
            total_pricing = sum(po.pricing_total_amount or 0 for po in approved)
            total_settlement = sum(po.settlement_total_amount or 0 for po in approved)
            print(f"已批准批价总额: {total_pricing:,.2f}")
            print(f"已批准结算总额: {total_settlement:,.2f}")

            # 按状态分布
            status_dist = defaultdict(int)
            for po in pricing_orders:
                status_dist[po.status] += 1
            print(f"状态分布: {dict(status_dist)}")

        # 3b. 批价单中的产品Top5
        print(f"\n--- 3b. 批价单产品Top5 ---")
        approved_po_ids = [po.id for po in pricing_orders if po.status == 'approved'] if pricing_orders else []
        if approved_po_ids:
            product_pricing = defaultdict(lambda: {'amount': 0, 'quantity': 0, 'count': 0})
            po_details = PricingOrderDetail.query.filter(
                PricingOrderDetail.pricing_order_id.in_(approved_po_ids)
            ).all()

            for d in po_details:
                key = d.product_mn or d.product_name or 'Unknown'
                product_pricing[key]['amount'] += d.total_price or 0
                product_pricing[key]['quantity'] += d.quantity or 0
                product_pricing[key]['count'] += 1
                if 'name' not in product_pricing[key]:
                    product_pricing[key]['name'] = d.product_name or key

            sorted_pricing = sorted(product_pricing.items(), key=lambda x: x[1]['amount'], reverse=True)
            print(f"产品种类总数: {len(sorted_pricing)}")
            print(f"\nTop5 按金额:")
            for i, (mn, info) in enumerate(sorted_pricing[:5], 1):
                print(f"  {i}. {mn} ({info['name']}) - 金额: {info['amount']:,.2f}, 数量: {info['quantity']}, 出现次数: {info['count']}")

            print(f"\nTop5 按数量:")
            sorted_pricing_qty = sorted(product_pricing.items(), key=lambda x: x[1]['quantity'], reverse=True)
            for i, (mn, info) in enumerate(sorted_pricing_qty[:5], 1):
                print(f"  {i}. {mn} ({info['name']}) - 数量: {info['quantity']}, 金额: {info['amount']:,.2f}")
        else:
            print("无已批准批价单")

        # 3c. 通过产品ownership查找关联的批价单（产品owner是liuwei的）
        print(f"\n--- 3c. 产品Owner维度的批价单（Product.owner_id = liuwei）---")
        owned_products = Product.query.filter(Product.owner_id == user.id).all()
        print(f"liuwei拥有的产品数: {len(owned_products)}")
        if owned_products:
            owned_mns = [p.product_mn for p in owned_products if p.product_mn]
            print(f"产品MN列表: {owned_mns[:10]}{'...' if len(owned_mns) > 10 else ''}")

            # 查找这些产品在所有2025批价单中的出现
            if owned_mns:
                po_details_by_product = db.session.query(
                    PricingOrderDetail.product_mn,
                    PricingOrderDetail.product_name,
                    func.sum(PricingOrderDetail.total_price).label('total_amount'),
                    func.sum(PricingOrderDetail.quantity).label('total_qty'),
                    func.count(PricingOrderDetail.id).label('line_count')
                ).join(
                    PricingOrder, PricingOrder.id == PricingOrderDetail.pricing_order_id
                ).filter(
                    PricingOrderDetail.product_mn.in_(owned_mns),
                    PricingOrder.status == 'approved',
                    PricingOrder.created_at >= year_start,
                    PricingOrder.created_at <= year_end
                ).group_by(
                    PricingOrderDetail.product_mn,
                    PricingOrderDetail.product_name
                ).order_by(text('total_amount DESC')).all()

                total_by_ownership = sum(r.total_amount or 0 for r in po_details_by_product)
                print(f"通过产品ownership关联的批价金额合计: {total_by_ownership:,.2f}")
                print(f"\n产品明细:")
                for r in po_details_by_product[:10]:
                    print(f"  {r.product_mn} ({r.product_name}) - 金额: {r.total_amount:,.2f}, 数量: {r.total_qty}, 出现: {r.line_count}次")

        # ========== 4. 项目关联分析（原生SQL，避免activity_status列缺失问题）==========
        print(f"\n{'='*80}")
        print("🏗️ 三、项目关联分析")
        print(f"{'='*80}")

        # 4a. 作为项目Owner
        sql_owner = text("""
            SELECT p.id, p.project_name, p.current_stage, p.status,
                   p.created_at, p.last_activity_date, p.owner_id, p.vendor_sales_manager_id,
                   u.username as owner_username
            FROM projects p
            LEFT JOIN users u ON p.owner_id = u.id
            WHERE p.owner_id = :uid
        """)
        projects_as_owner = db.session.execute(sql_owner, {'uid': user.id}).fetchall()
        projects_2025_owner = [p for p in projects_as_owner
                               if (p.created_at and p.created_at.year == 2025) or
                                  (p.last_activity_date and p.last_activity_date.year == 2025)]

        print(f"\n--- 4a. 作为项目Owner ---")
        print(f"所有项目: {len(projects_as_owner)}")
        print(f"2025年活跃项目: {len(projects_2025_owner)}")

        if projects_2025_owner:
            stage_dist = defaultdict(int)
            status_dist = defaultdict(int)
            for p in projects_2025_owner:
                stage_dist[p.current_stage or 'unknown'] += 1
                status_dist[p.status or 'unknown'] += 1
            print(f"阶段分布: {dict(stage_dist)}")
            print(f"审批状态: {dict(status_dist)}")

        # 4b. 作为vendor_sales_manager（厂商销售负责人）
        sql_vsm = text("""
            SELECT p.id, p.project_name, p.current_stage, p.status,
                   p.created_at, p.last_activity_date, p.owner_id, p.vendor_sales_manager_id,
                   u.username as owner_username, u.real_name as owner_realname
            FROM projects p
            LEFT JOIN users u ON p.owner_id = u.id
            WHERE p.vendor_sales_manager_id = :uid
        """)
        projects_as_vsm = db.session.execute(sql_vsm, {'uid': user.id}).fetchall()
        projects_2025_vsm = [p for p in projects_as_vsm
                             if (p.created_at and p.created_at.year == 2025) or
                                (p.last_activity_date and p.last_activity_date.year == 2025)]

        print(f"\n--- 4b. 作为厂商销售负责人（vendor_sales_manager）---")
        print(f"所有项目: {len(projects_as_vsm)}")
        print(f"2025年活跃项目: {len(projects_2025_vsm)}")

        if projects_2025_vsm:
            stage_dist2 = defaultdict(int)
            for p in projects_2025_vsm:
                stage_dist2[p.current_stage or 'unknown'] += 1
            print(f"阶段分布: {dict(stage_dist2)}")

            print(f"\n关联销售配合:")
            sales_collab = defaultdict(list)
            for p in projects_2025_vsm:
                if p.owner_username:
                    sales_collab[p.owner_username].append(p.project_name)
            for sales, projects_list in sorted(sales_collab.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"  {sales}: {len(projects_list)} 个项目")

        # 4c. 作为项目创建人
        sql_creator = text("""
            SELECT COUNT(*) as cnt FROM projects
            WHERE created_by = :uid AND created_at >= :start AND created_at <= :end
        """)
        creator_count = db.session.execute(sql_creator, {'uid': user.id, 'start': year_start, 'end': year_end}).scalar()

        print(f"\n--- 4c. 作为项目创建人（2025年）---")
        print(f"创建项目数: {creator_count}")

        # ========== 5. 行动记录分析 ==========
        print(f"\n{'='*80}")
        print("📝 四、行动记录（Action）分析")
        print(f"{'='*80}")

        actions = Action.query.filter(
            Action.owner_id == user.id,
            Action.date >= '2025-01-01',
            Action.date <= '2025-12-31'
        ).all()

        print(f"2025年行动记录总数: {len(actions)}")

        if actions:
            monthly_actions = defaultdict(int)
            for a in actions:
                if a.date:
                    monthly_actions[a.date.month] += 1
            print(f"月份分布: {dict(sorted(monthly_actions.items()))}")

            with_project = [a for a in actions if a.project_id]
            with_company = [a for a in actions if a.company_id]
            with_contact = [a for a in actions if a.contact_id]
            print(f"关联项目: {len(with_project)}/{len(actions)}")
            print(f"关联公司: {len(with_company)}/{len(actions)}")
            print(f"关联联系人: {len(with_contact)}/{len(actions)}")

            # 关联的项目分布（原生SQL避免ORM问题）
            project_actions = defaultdict(int)
            for a in actions:
                if a.project_id:
                    project_actions[a.project_id] += 1

            if project_actions:
                pids = list(project_actions.keys())
                sql_proj_names = text("""
                    SELECT p.id, p.project_name, u.username as owner_username
                    FROM projects p
                    LEFT JOIN users u ON p.owner_id = u.id
                    WHERE p.id = ANY(:pids)
                """)
                proj_info = {r.id: r for r in db.session.execute(sql_proj_names, {'pids': pids}).fetchall()}

                print(f"\n行动记录最多的项目Top10:")
                sorted_pa = sorted(project_actions.items(), key=lambda x: x[1], reverse=True)
                for pid, count in sorted_pa[:10]:
                    info = proj_info.get(pid)
                    pname = info.project_name if info else f"(ID={pid})"
                    powner = info.owner_username if info else 'N/A'
                    print(f"  {pname} (owner={powner}) - {count} 条记录")

        # ========== 6. 工作日志分析 ==========
        print(f"\n{'='*80}")
        print("📅 五、工作日志（WorkItem）分析")
        print(f"{'='*80}")

        work_items = WorkItem.query.filter(
            WorkItem.owner_id == user.id,
            WorkItem.planned_date >= '2025-01-01',
            WorkItem.planned_date <= '2025-12-31',
            WorkItem.is_deleted == False
        ).all()

        print(f"2025年工作项总数: {len(work_items)}")

        if work_items:
            type_dist = defaultdict(int)
            status_dist_wi = defaultdict(int)
            for w in work_items:
                type_dist[w.work_type or 'unknown'] += 1
                status_dist_wi[w.status or 'unknown'] += 1
            print(f"工作类型分布: {dict(type_dist)}")
            print(f"完成状态分布: {dict(status_dist_wi)}")

            monthly_work = defaultdict(int)
            for w in work_items:
                if w.planned_date:
                    monthly_work[w.planned_date.month] += 1
            print(f"月份分布: {dict(sorted(monthly_work.items()))}")

            biz_trips = [w for w in work_items if w.is_business_trip]
            print(f"出差记录: {len(biz_trips)} 次")

        # ========== 7. 销售配合度综合分析 ==========
        print(f"\n{'='*80}")
        print("🤝 六、销售配合度综合分析")
        print(f"{'='*80}")

        # 7a. liuwei确认的报价单的owner分布
        if quotations_confirmed_by:
            sales_confirmed = defaultdict(lambda: {'count': 0, 'amount': 0, 'implant': 0})
            for q in quotations_confirmed_by:
                if q.owner:
                    sales_confirmed[q.owner.username]['count'] += 1
                    sales_confirmed[q.owner.username]['amount'] += q.amount or 0
                    sales_confirmed[q.owner.username]['implant'] += q.implant_total_amount or 0

            print(f"\n--- 7a. 确认报价单的销售分布 ---")
            for sales, info in sorted(sales_confirmed.items(), key=lambda x: x[1]['count'], reverse=True):
                print(f"  {sales}: 确认{info['count']}份, 金额{info['amount']:,.2f}, 植入{info['implant']:,.2f}")

        # 7b. liuwei行动记录中涉及的项目的owner分布（原生SQL）
        if actions:
            action_pids = list(set(a.project_id for a in actions if a.project_id))
            if action_pids:
                sql_action_proj = text("""
                    SELECT p.id, u.username as owner_username
                    FROM projects p
                    LEFT JOIN users u ON p.owner_id = u.id
                    WHERE p.id = ANY(:pids)
                """)
                proj_owners = {r.id: r.owner_username for r in db.session.execute(sql_action_proj, {'pids': action_pids}).fetchall()}

                sales_actions = defaultdict(int)
                for a in actions:
                    if a.project_id and a.project_id in proj_owners:
                        owner_name = proj_owners[a.project_id] or 'N/A'
                        sales_actions[owner_name] += 1

                print(f"\n--- 7b. 行动记录涉及的销售分布 ---")
                for sales, count in sorted(sales_actions.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {sales}: {count} 条行动记录")

        # ========== 8. 报价单明细列表 ==========
        print(f"\n{'='*80}")
        print("📋 七、报价单明细列表（确认的76份）")
        print(f"{'='*80}")

        if quotations_confirmed_by:
            print(f"\n{'编号':<16} {'项目阶段':<10} {'金额':>14} {'植入':>14} {'确认日期':<12} {'Owner':<12}")
            print("-" * 80)
            for q in sorted(quotations_confirmed_by, key=lambda x: x.confirmed_at or x.created_at):
                qnum = q.quotation_number or ''
                stage = q.project_stage or ''
                amt = f"{(q.amount or 0):,.2f}"
                imp = f"{(q.implant_total_amount or 0):,.2f}"
                cdate = q.confirmed_at.strftime('%Y-%m-%d') if q.confirmed_at else ''
                owner = q.owner.username if q.owner else 'N/A'
                print(f"  {qnum:<14} {stage:<10} {amt:>14} {imp:>14} {cdate:<12} {owner:<12}")

        # ========== 9. 汇总统计 ==========
        print(f"\n{'='*80}")
        print("📊 八、汇总统计")
        print(f"{'='*80}")

        print(f"\n用户: {user.real_name} ({user.username}), 角色: solution_manager")
        print(f"报价单(作为owner): {len(quotations_as_owner)} 份")
        print(f"报价单(作为确认人): {len(quotations_confirmed_by)} 份")
        print(f"报价单(有确认徽章,2025创建): {len(all_confirmed)} 份")
        print(f"批价单(创建): {len(pricing_orders)} 份")
        approved_count = len([po for po in pricing_orders if po.status == 'approved']) if pricing_orders else 0
        print(f"批价单(已批准): {approved_count} 份")
        print(f"产品(owner): {len(owned_products)} 个")
        print(f"项目(owner): {len(projects_as_owner)} 个 (2025活跃: {len(projects_2025_owner)})")
        print(f"项目(厂商销售负责人): {len(projects_as_vsm)} 个 (2025活跃: {len(projects_2025_vsm)})")
        print(f"项目(创建): {creator_count} 个")
        print(f"行动记录: {len(actions)} 条")
        print(f"工作项: {len(work_items)} 个")

        print(f"\n{'='*80}")
        print("数据采集完成！")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
