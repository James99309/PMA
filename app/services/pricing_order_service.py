from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import logging
from app import db
from app.models.pricing_order import (
    PricingOrder, PricingOrderDetail, SettlementOrder, SettlementOrderDetail, 
    PricingOrderApprovalRecord, PricingOrderStatus, PricingOrderApprovalFlowType,
    SettlementOrderStatus
)
from app.models.quotation import Quotation, QuotationDetail
from app.models.project import Project
from app.models.customer import Company
from app.models.user import User
from app.permissions import check_permission

logger = logging.getLogger(__name__)


class PricingOrderService:
    """批价单服务类"""
    
    # 快速通过折扣率规则 - 已取消快速审批功能
    # FAST_APPROVAL_RULES = {
    #     '渠道经理': 40.5,
    #     '营销总监': 38.0,
    #     '服务经理': 40.5,
    #     '总经理': 0.0  # 总经理无限制
    # }
    
    @staticmethod
    def determine_approval_flow_type(project):
        """根据项目信息确定审批流程类型"""
        if not project:
            return 'sales_key'
        
        project_type = project.project_type
        # 支持中英文项目类型映射
        if project_type in ["渠道跟进", "channel_follow"]:
            return 'channel_follow'
        elif project_type in ["销售机会", "sales_opportunity"]:
            return 'sales_opportunity'
        elif project_type in ["销售重点", "sales_key"]:
            return 'sales_key'
        else:
            # 默认为销售重点类
            return 'sales_key'
    
    @staticmethod
    def generate_approval_steps(flow_type, project, has_dealer=False):
        """生成审批步骤"""
        steps = []
        
        vendor_sales_manager = project.vendor_sales_manager if project else None
        project_owner = project.owner if project else None
        
        # 判断拥有者是否是厂商销售负责人（适用于所有流程类型）
        need_vendor_approval = (vendor_sales_manager and 
                               project_owner and 
                               vendor_sales_manager.id != project_owner.id)
        
        if flow_type == 'channel_follow':
            # 渠道跟进类
            if need_vendor_approval:
                steps.append({
                    'step_order': 1,
                    'step_name': '销售负责人审批',
                    'approver_role': '厂商销售负责人',
                    'approver_id': vendor_sales_manager.id
                })
                steps.append({
                    'step_order': 2,
                    'step_name': '渠道经理审批',
                    'approver_role': '渠道经理',
                    'approver_id': PricingOrderService.get_role_user_id('渠道经理')
                })
                steps.append({
                    'step_order': 3,
                    'step_name': '营销总监审批',
                    'approver_role': '营销总监',
                    'approver_id': PricingOrderService.get_role_user_id('营销总监')
                })
                steps.append({
                    'step_order': 4,
                    'step_name': '总经理审批',
                    'approver_role': '总经理',
                    'approver_id': PricingOrderService.get_role_user_id('总经理')
                })
            else:
                # 拥有人等于厂商负责人，跳过厂商负责人审批
                steps.append({
                    'step_order': 1,
                    'step_name': '渠道经理审批',
                    'approver_role': '渠道经理',
                    'approver_id': PricingOrderService.get_role_user_id('渠道经理')
                })
                steps.append({
                    'step_order': 2,
                    'step_name': '营销总监审批',
                    'approver_role': '营销总监',
                    'approver_id': PricingOrderService.get_role_user_id('营销总监')
                })
                steps.append({
                    'step_order': 3,
                    'step_name': '总经理审批',
                    'approver_role': '总经理',
                    'approver_id': PricingOrderService.get_role_user_id('总经理')
                })
        
        elif flow_type == 'sales_key':
            # 销售重点类
            if need_vendor_approval:
                steps.append({
                    'step_order': 1,
                    'step_name': '销售负责人审批',
                    'approver_role': '厂商销售负责人',
                    'approver_id': vendor_sales_manager.id
                })
                steps.append({
                    'step_order': 2,
                    'step_name': '营销总监审批',
                    'approver_role': '营销总监',
                    'approver_id': PricingOrderService.get_role_user_id('营销总监')
                })
                steps.append({
                    'step_order': 3,
                    'step_name': '总经理审批',
                    'approver_role': '总经理',
                    'approver_id': PricingOrderService.get_role_user_id('总经理')
                })
            else:
                # 拥有人等于厂商负责人，跳过厂商负责人审批
                steps.append({
                    'step_order': 1,
                    'step_name': '营销总监审批',
                    'approver_role': '营销总监',
                    'approver_id': PricingOrderService.get_role_user_id('营销总监')
                })
                steps.append({
                    'step_order': 2,
                    'step_name': '总经理审批',
                    'approver_role': '总经理',
                    'approver_id': PricingOrderService.get_role_user_id('总经理')
                })
            
        elif flow_type == 'sales_opportunity':
            # 销售机会类
            if need_vendor_approval:
                steps.append({
                    'step_order': 1,
                    'step_name': '销售负责人审批',
                    'approver_role': '厂商销售负责人',
                    'approver_id': vendor_sales_manager.id
                })
                steps.append({
                    'step_order': 2,
                    'step_name': '服务经理审批',
                    'approver_role': '服务经理',
                    'approver_id': PricingOrderService.get_role_user_id('服务经理')
                })
                steps.append({
                    'step_order': 3,
                    'step_name': '总经理审批',
                    'approver_role': '总经理',
                    'approver_id': PricingOrderService.get_role_user_id('总经理')
                })
            else:
                # 拥有人等于厂商负责人，跳过厂商负责人审批
                steps.append({
                    'step_order': 1,
                    'step_name': '服务经理审批',
                    'approver_role': '服务经理',
                    'approver_id': PricingOrderService.get_role_user_id('服务经理')
                })
                steps.append({
                    'step_order': 2,
                    'step_name': '总经理审批',
                    'approver_role': '总经理',
                    'approver_id': PricingOrderService.get_role_user_id('总经理')
                })
        
        return steps
    
    @staticmethod
    def get_role_user_id(role_name):
        """根据角色名称获取用户ID - 改进版：直接基于数据库角色字段"""
        
        # 中文角色名称到英文角色字段的映射
        role_field_mapping = {
            '渠道经理': 'channel_manager',
            '营销总监': 'sales_director', 
            '服务经理': 'service_manager',
            '总经理': 'ceo',
            '财务经理': 'finance_director',
            '商务助理': 'business_admin'
        }
        
        # 获取对应的数据库角色字段
        db_role = role_field_mapping.get(role_name)
        if not db_role:
            # 如果没有找到对应角色，记录警告并返回管理员
            logger.warning(f"未找到角色 {role_name} 的映射，使用管理员作为默认审批人")
            admin_user = User.query.filter_by(role='admin').first()
            return admin_user.id if admin_user else 1
        
        # 直接从数据库查找具有该角色的用户
        users = User.query.filter_by(role=db_role).all()
        
        if not users:
            # 如果没有找到对应角色的用户，记录警告并回退到管理员
            logger.warning(f"没有找到角色为 {db_role} 的用户，使用管理员作为默认审批人")
            admin_user = User.query.filter_by(role='admin').first()
            return admin_user.id if admin_user else 1
        elif len(users) == 1:
            # 只有一个用户具有该角色，直接返回
            logger.info(f"找到角色 {role_name}({db_role}) 的审批人: {users[0].real_name or users[0].username}")
            return users[0].id
        else:
            # 有多个用户具有该角色，需要额外的逻辑来选择
            # 这里可以根据业务规则进行选择，比如：
            # 1. 选择最早创建的用户
            # 2. 选择指定的主要负责人
            # 3. 提供配置选项让管理员指定
            
            # 目前先选择最早创建的用户，并记录警告
            selected_user = min(users, key=lambda u: u.created_at or 0)
            other_users = [u.real_name or u.username for u in users if u.id != selected_user.id]
            logger.warning(f"角色 {role_name}({db_role}) 有多个用户: {[u.real_name or u.username for u in users]}，"
                         f"自动选择了 {selected_user.real_name or selected_user.username}，"
                         f"其他用户: {other_users}")
            return selected_user.id
    
    @staticmethod
    def create_pricing_order(project_id, quotation_id, distributor_id=None, dealer_id=None, current_user_id=None):
        """创建批价单"""
        try:
            # 获取项目和报价单
            project = Project.query.get(project_id)
            quotation = Quotation.query.get(quotation_id)
            
            if not project or not quotation:
                return None, "项目或报价单不存在"
            
            # 确定审批流程类型
            flow_type = PricingOrderService.determine_approval_flow_type(project)
            
            # 自动获取项目中的经销商ID
            project_dealer_id = None
            if not dealer_id and project.dealer:
                # 根据项目中的经销商名称查找对应的公司ID
                from app.models.customer import Company
                dealer_company = Company.query.filter(
                    Company.company_name == project.dealer,
                    Company.company_type.in_(['经销商', 'dealer'])
                ).first()
                if dealer_company:
                    project_dealer_id = dealer_company.id
            
            # 创建批价单
            pricing_order = PricingOrder(
                project_id=project_id,
                quotation_id=quotation_id,
                distributor_id=distributor_id,
                dealer_id=dealer_id or project_dealer_id,  # 使用传入的经销商ID或项目中的经销商ID
                approval_flow_type=flow_type,
                created_by=current_user_id
            )
            
            db.session.add(pricing_order)
            db.session.flush()  # 获取ID
            
            # 从报价单复制产品明细到批价单
            PricingOrderService.copy_quotation_details_to_pricing(quotation, pricing_order)
            
            # 创建结算单（在明细复制完成后）
            settlement_order = PricingOrderService.create_settlement_order(pricing_order, current_user_id)
            
            # 创建结算单明细（基于批价单明细）
            PricingOrderService.create_settlement_details(pricing_order, settlement_order)
            
            # 生成审批步骤
            approval_steps = PricingOrderService.generate_approval_steps(
                flow_type, project, has_dealer=bool(pricing_order.dealer_id)
            )
            
            # 创建审批记录
            for step in approval_steps:
                approval_record = PricingOrderApprovalRecord(
                    pricing_order_id=pricing_order.id,
                    step_order=step['step_order'],
                    step_name=step['step_name'],
                    approver_role=step['approver_role'],
                    approver_id=step['approver_id']
                )
                db.session.add(approval_record)
            
            # 计算总额
            pricing_order.calculate_pricing_totals()
            pricing_order.calculate_settlement_totals()
            settlement_order.calculate_totals()
            
            db.session.commit()
            
            return pricing_order, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"数据库错误: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return None, f"创建失败: {str(e)}"
    
    @staticmethod
    def create_settlement_order(pricing_order, current_user_id):
        """创建结算单"""
        # 如果没有分销商，使用经销商作为分销商（结算单主要面向分销商）
        distributor_id = pricing_order.distributor_id or pricing_order.dealer_id
        
        # 如果仍然没有，需要从项目中获取客户公司作为分销商
        if not distributor_id and pricing_order.project:
            # 使用项目的客户公司作为分销商
            distributor_id = getattr(pricing_order.project, 'company_id', None)
        
        # 如果还是没有，创建一个默认的分销商记录或者报错
        if not distributor_id:
            # 查找一个默认的公司记录，或者使用第一个公司
            from app.models.customer import Company
            default_company = Company.query.first()
            if default_company:
                distributor_id = default_company.id
            else:
                raise ValueError("无法创建结算单：缺少分销商信息")
        
        settlement_order = SettlementOrder(
            pricing_order_id=pricing_order.id,
            project_id=pricing_order.project_id,
            quotation_id=pricing_order.quotation_id,
            distributor_id=distributor_id,
            dealer_id=pricing_order.dealer_id,
            created_by=current_user_id
        )
        
        db.session.add(settlement_order)
        db.session.flush()  # 获取ID
        
        return settlement_order
    
    @staticmethod
    def copy_quotation_details_to_pricing(quotation, pricing_order):
        """从报价单复制产品明细到批价单"""
        for qd in quotation.details:
            # 创建批价单明细
            pricing_detail = PricingOrderDetail(
                pricing_order_id=pricing_order.id,
                product_name=qd.product_name,
                product_model=qd.product_model,
                product_desc=qd.product_desc,
                brand=qd.brand,
                unit=qd.unit,
                product_mn=qd.product_mn,
                market_price=qd.market_price,
                unit_price=qd.unit_price,
                quantity=qd.quantity,
                discount_rate=qd.discount,
                source_type='quotation',
                source_quotation_detail_id=qd.id
            )
            pricing_detail.calculate_prices()
            db.session.add(pricing_detail)
            
        # 刷新以获取批价单明细的ID
        db.session.flush()
    
    @staticmethod
    def create_settlement_details(pricing_order, settlement_order):
        """创建结算单明细（基于批价单明细）"""
        for pricing_detail in pricing_order.pricing_details:
            settlement_detail = SettlementOrderDetail(
                pricing_order_id=pricing_order.id,
                settlement_order_id=settlement_order.id,
                product_name=pricing_detail.product_name,
                product_model=pricing_detail.product_model,
                product_desc=pricing_detail.product_desc,
                brand=pricing_detail.brand,
                unit=pricing_detail.unit,
                product_mn=pricing_detail.product_mn,
                market_price=pricing_detail.market_price,
                unit_price=pricing_detail.unit_price,
                quantity=pricing_detail.quantity,
                discount_rate=pricing_detail.discount_rate,
                pricing_detail_id=pricing_detail.id
            )
            settlement_detail.calculate_prices()
            db.session.add(settlement_detail)
    
    @staticmethod
    def update_pricing_detail(pricing_order_id, detail_id, quantity=None, discount_rate=None, unit_price=None):
        """更新批价单明细"""
        try:
            pricing_detail = PricingOrderDetail.query.filter_by(
                pricing_order_id=pricing_order_id, id=detail_id
            ).first()
            
            if not pricing_detail:
                return False, "明细不存在"
            
            if quantity is not None:
                pricing_detail.quantity = quantity
            if discount_rate is not None:
                pricing_detail.discount_rate = discount_rate
            if unit_price is not None:
                pricing_detail.unit_price = unit_price
                # 根据单价反算折扣率
                if pricing_detail.market_price and pricing_detail.market_price > 0:
                    pricing_detail.discount_rate = unit_price / pricing_detail.market_price
            
            pricing_detail.calculate_prices()
            
            # 同步更新结算单明细
            settlement_detail = SettlementOrderDetail.query.filter_by(
                pricing_detail_id=detail_id
            ).first()
            if settlement_detail:
                settlement_detail.quantity = pricing_detail.quantity
                settlement_detail.discount_rate = pricing_detail.discount_rate
                settlement_detail.unit_price = pricing_detail.unit_price
                settlement_detail.calculate_prices()
            
            # 重新计算总额
            pricing_order = PricingOrder.query.get(pricing_order_id)
            pricing_order.calculate_pricing_totals()
            pricing_order.calculate_settlement_totals()
            
            # 更新结算单总额
            settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order_id).first()
            if settlement_order:
                settlement_order.calculate_totals()
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"更新失败: {str(e)}"
    
    @staticmethod
    def update_settlement_detail(pricing_order_id, detail_id, discount_rate=None, unit_price=None):
        """更新结算单明细"""
        try:
            settlement_detail = SettlementOrderDetail.query.filter_by(
                pricing_order_id=pricing_order_id, id=detail_id
            ).first()
            
            if not settlement_detail:
                return False, "明细不存在"
            
            if discount_rate is not None:
                settlement_detail.discount_rate = discount_rate
            if unit_price is not None:
                settlement_detail.unit_price = unit_price
                # 反算折扣率
                if settlement_detail.market_price and settlement_detail.market_price > 0:
                    settlement_detail.discount_rate = unit_price / settlement_detail.market_price
            
            settlement_detail.calculate_prices()
            
            # 重新计算总额
            pricing_order = PricingOrder.query.get(pricing_order_id)
            pricing_order.calculate_settlement_totals()
            
            # 更新结算单总额
            settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order_id).first()
            if settlement_order:
                settlement_order.calculate_totals()
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"更新失败: {str(e)}"
    
    @staticmethod
    def update_total_discount_rate(pricing_order_id, tab_type='pricing', total_discount_rate=None):
        """更新总折扣率，联动修改所有产品折扣率"""
        try:
            pricing_order = PricingOrder.query.get(pricing_order_id)
            if not pricing_order:
                return False, "批价单不存在"
            
            if tab_type == 'pricing':
                # 更新批价单所有明细的折扣率
                for detail in pricing_order.pricing_details:
                    detail.discount_rate = total_discount_rate
                    detail.calculate_prices()
                    
                    # 同步更新结算单明细
                    settlement_detail = SettlementOrderDetail.query.filter_by(
                        pricing_detail_id=detail.id
                    ).first()
                    if settlement_detail:
                        settlement_detail.discount_rate = total_discount_rate
                        settlement_detail.calculate_prices()
                
                pricing_order.pricing_total_discount_rate = total_discount_rate
                pricing_order.calculate_pricing_totals()
                pricing_order.calculate_settlement_totals()
                
            else:  # settlement
                # 更新结算单所有明细的折扣率
                for detail in pricing_order.settlement_details:
                    detail.discount_rate = total_discount_rate
                    detail.calculate_prices()
                
                pricing_order.settlement_total_discount_rate = total_discount_rate
                pricing_order.calculate_settlement_totals()
            
            # 更新结算单总额
            settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order_id).first()
            if settlement_order:
                settlement_order.calculate_totals()
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"更新失败: {str(e)}"
    
    @staticmethod
    def submit_for_approval(pricing_order_id, current_user_id):
        """提交审批"""
        try:
            pricing_order = PricingOrder.query.get(pricing_order_id)
            if not pricing_order:
                return False, "批价单不存在"
            
            if pricing_order.status not in ['draft', 'rejected']:
                return False, "只有草稿状态或被拒绝的批价单可以提交审批"
            
            # 🔥 关键修复：清理旧的审批记录（召回后重新提交时）
            old_records = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order_id
            ).all()
            for record in old_records:
                db.session.delete(record)
                
            # 🔥 关键修复：生成新的审批流程
            project = pricing_order.project
            flow_type = PricingOrderService.determine_approval_flow_type(project)
            
            # 更新审批流程类型
            pricing_order.approval_flow_type = flow_type
            
            # 生成审批步骤
            approval_steps = PricingOrderService.generate_approval_steps(
                flow_type, 
                project, 
                has_dealer=(pricing_order.dealer_id is not None)
            )
            
            if not approval_steps:
                return False, "无法生成审批流程，请检查项目信息和用户角色配置"
            
            # 创建审批记录
            for step_data in approval_steps:
                approval_record = PricingOrderApprovalRecord(
                    pricing_order_id=pricing_order_id,
                    step_order=step_data['step_order'],
                    step_name=step_data['step_name'],
                    approver_role=step_data['approver_role'],
                    approver_id=step_data['approver_id']
                )
                db.session.add(approval_record)
            
            # 更新状态为审批中
            pricing_order.status = 'pending'
            pricing_order.current_approval_step = 1
            
            # 锁定项目和报价单
            if project:
                project.is_locked = True
                project.locked_reason = "批价审批流程进行中"
                project.locked_by = current_user_id
                project.locked_at = datetime.now()
            
            quotation = pricing_order.quotation
            if quotation:
                quotation.is_locked = True
                quotation.lock_reason = "批价审批流程进行中"
                quotation.locked_by = current_user_id
                quotation.locked_at = datetime.now()
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"提交失败: {str(e)}"
    
    @staticmethod
    def approve_step(pricing_order_id, step_order, current_user_id, action, comment=None, frontend_amounts=None):
        """审批步骤
        
        Args:
            pricing_order_id: 批价单ID
            step_order: 审批步骤
            current_user_id: 当前用户ID
            action: 审批动作（approve/reject）
            comment: 审批意见
            frontend_amounts: 前端传递的金额数据，格式为 {'pricing_total': float, 'settlement_total': float}
        """
        try:
            pricing_order = PricingOrder.query.get(pricing_order_id)
            if not pricing_order:
                return False, "批价单不存在"
            
            if pricing_order.status != 'pending':
                return False, "只有审批中的批价单可以审批"
            
            if pricing_order.current_approval_step != step_order:
                return False, "当前不是该步骤的审批时间"
            
            # 获取审批记录
            approval_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order_id,
                step_order=step_order
            ).first()
            
            if not approval_record:
                return False, "审批步骤不存在"
            
            if approval_record.approver_id != current_user_id:
                return False, "您没有权限审批该步骤"
            
            # 更新审批记录
            approval_record.action = action
            approval_record.comment = comment
            approval_record.approved_at = datetime.now()
            
            if action == 'reject':
                # 拒绝：结束审批流程
                pricing_order.status = 'rejected'
                
                # 重置结算单审批状态（保留数据，仅重置状态）
                PricingOrderService.reset_settlement_approval_status(pricing_order_id)
                
                PricingOrderService.unlock_related_objects(pricing_order)
                
            elif action == 'approve':
                # 已取消快速审批功能，审批步骤需要逐步进行
                # 检查是否还有下一步
                next_step = PricingOrderApprovalRecord.query.filter_by(
                    pricing_order_id=pricing_order_id,
                    step_order=step_order + 1
                ).first()
                
                if next_step:
                    # 进入下一步
                    pricing_order.current_approval_step = step_order + 1
                else:
                    # 最后一步：完成审批前需要进行金额校验
                    # 如果有前端传递的金额数据，优先使用前端数据进行校验
                    if frontend_amounts:
                        pricing_total = frontend_amounts.get('pricing_total', 0)
                        settlement_total = frontend_amounts.get('settlement_total', 0)
                        
                        # 使用前端最新金额进行校验
                        if settlement_total < pricing_total:
                            return False, f"审批失败：结算单总金额 ¥{settlement_total:,.2f} 小于批价单总金额 ¥{pricing_total:,.2f}，不能通过审批"
                    else:
                        # 回退到数据库金额校验（兼容性）
                        from app.models.pricing_order import SettlementOrder
                        settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order_id).first()
                        
                        if settlement_order:
                            # 重新计算最新的总金额
                            settlement_order.calculate_totals()
                            
                            # 检查结算单总金额不能小于批价单总金额
                            if settlement_order.total_amount < pricing_order.pricing_total_amount:
                                return False, f"审批失败：结算单总金额 ¥{settlement_order.total_amount:,.2f} 小于批价单总金额 ¥{pricing_order.pricing_total_amount:,.2f}，不能通过审批"
                    
                    # 金额校验通过，继续完成审批
                    # 注意：不再重新计算总金额和总折扣率，保持前端传递的数据
                    # 前端数据已经在审批路由中保存，这里直接使用
                    
                    pricing_order.status = 'approved'
                    pricing_order.approved_by = current_user_id
                    pricing_order.approved_at = datetime.now()
                    # 正常完成时，将当前步骤设置为0，表示流程结束
                    pricing_order.current_approval_step = 0
                    
                    PricingOrderService.complete_approval(pricing_order)
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"审批失败: {str(e)}"
    
    # 已取消快速审批功能，注释掉相关方法
    # @staticmethod
    # def auto_approve_remaining_steps(pricing_order, current_user_id, fast_approval_role):
    #     """自动通过后续所有审批步骤"""
    #     try:
    #         # 获取当前步骤之后的所有审批记录
    #         remaining_steps = PricingOrderApprovalRecord.query.filter(
    #             PricingOrderApprovalRecord.pricing_order_id == pricing_order.id,
    #             PricingOrderApprovalRecord.step_order > pricing_order.current_approval_step,
    #             PricingOrderApprovalRecord.action.is_(None)  # 只处理未审批的步骤
    #         ).all()
    #         
    #         # 自动通过所有后续步骤
    #         for step_record in remaining_steps:
    #             step_record.action = 'approve'
    #             step_record.comment = f'因{fast_approval_role}快速通过而自动审批'
    #             step_record.approved_at = datetime.now()
    #             step_record.is_fast_approval = True
    #             step_record.fast_approval_reason = f'因{fast_approval_role}快速通过而自动审批'
    #         
    #         return True
    #         
    #     except Exception as e:
    #         from app import current_app
    #         current_app.logger.error(f"自动通过后续步骤失败: {str(e)}")
    #         return False
    # 
    # @staticmethod
    # def check_fast_approval(approval_record, pricing_order):
    #     """检查是否满足快速通过条件"""
    #     approver_role = approval_record.approver_role
    #     if approver_role not in PricingOrderService.FAST_APPROVAL_RULES:
    #         return False
    #     
    #     min_discount_rate = PricingOrderService.FAST_APPROVAL_RULES[approver_role]
    #     if min_discount_rate == 0:  # 总经理无限制
    #         return True
    #     
    #     # 检查结算单折扣率
    #     settlement_discount_percentage = pricing_order.settlement_discount_percentage
    #     return settlement_discount_percentage >= min_discount_rate
    
    @staticmethod
    def complete_approval(pricing_order):
        """完成审批后的操作"""
        # 严格检查：只有在批价单状态为approved时才执行项目阶段更新
        if pricing_order.status != 'approved':
            from app import current_app
            current_app.logger.warning(f"批价单 {pricing_order.order_number} 状态为 {pricing_order.status}，不应调用complete_approval")
            return
        
        # 更新项目状态为签约
        project = pricing_order.project
        if project:
            old_stage = project.current_stage
            project.current_stage = 'signed'
            project.is_locked = True  # 保持锁定状态
            project.locked_reason = "项目已签约，锁定编辑"
            
            # 记录日志
            from app import current_app
            current_app.logger.info(f"批价单 {pricing_order.order_number} 审批通过，项目 {project.project_name} 阶段从 {old_stage} 更新为 signed")
            
            # 创建项目阶段历史记录
            from app.models.projectpm_stage_history import ProjectStageHistory
            ProjectStageHistory.add_history_record(
                project_id=project.id,
                from_stage=old_stage,
                to_stage='signed',
                change_date=datetime.now(),
                remarks=f"批价单审批通过自动推进",
                commit=False  # 不在方法内部提交，与主事务一同提交
            )
        
        # 更新报价单状态为已批价
        quotation = pricing_order.quotation
        if quotation:
            quotation.approval_status = 'quoted_approved'
            quotation.is_locked = True  # 保持锁定状态
            quotation.lock_reason = "报价单已批价，锁定编辑"
        
        # 更新结算单状态为已批准（修复：使用独立结算单模型）
        from app.models.pricing_order import SettlementOrder
        settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order.id).first()
        if settlement_order:
            settlement_order.status = 'approved'
            settlement_order.approved_by = pricing_order.approved_by
            settlement_order.approved_at = pricing_order.approved_at
            # 确保结算单总金额是最新的
            settlement_order.calculate_totals()
            from app import current_app
            current_app.logger.info(f"更新独立结算单 {settlement_order.order_number} 状态为已批准，总金额: {settlement_order.total_amount:,.2f}")
        else:
            from app import current_app
            current_app.logger.warning(f"批价单 {pricing_order.order_number} 没有对应的独立结算单")
    
    @staticmethod
    def unlock_related_objects(pricing_order):
        """解锁相关对象"""
        project = pricing_order.project
        if project:
            project.is_locked = False
            project.locked_reason = None
            project.locked_by = None
            project.locked_at = None
        
        quotation = pricing_order.quotation
        if quotation:
            quotation.is_locked = False
            quotation.lock_reason = None
            quotation.locked_by = None
            quotation.locked_at = None
    
    @staticmethod
    def send_completion_notifications(pricing_order, current_approval_record):
        """发送完成通知给后续审批人"""
        try:
            # 获取项目和用户信息
            project = pricing_order.project
            creator = pricing_order.creator
            
            # 收集需要通知的用户列表
            notification_users = set()
            
            # 添加创建人
            if creator:
                notification_users.add(creator.id)
            
            # 添加项目拥有者
            if project and project.owner:
                notification_users.add(project.owner.id)
            
            # 添加厂商销售负责人
            if project and project.vendor_sales_manager:
                notification_users.add(project.vendor_sales_manager.id)
            
            # 添加所有审批人
            for record in pricing_order.approval_records:
                if record.approver:
                    notification_users.add(record.approver.id)
            
            # 创建通知消息
            status_text = "审批通过" if pricing_order.status == 'approved' else "审批被拒绝"
            message = f"批价单 {pricing_order.order_number} 已{status_text}"
            
            # 这里应该调用通知系统发送消息
            # 简化处理：记录到日志
            from app import app
            app.logger.info(f"批价单审批完成通知: {message}, 通知用户: {list(notification_users)}")
            
            # 如果有邮件系统，可以在这里发送邮件
            # if hasattr(app, 'mail'):
            #     send_email_notification(notification_users, message, pricing_order)
            
            return True
            
        except Exception as e:
            from app import app
            app.logger.error(f"发送审批完成通知失败: {str(e)}")
            return False
    
    @staticmethod
    def can_edit_pricing_details(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑批价单明细
        
        Args:
            pricing_order: 批价单对象
            current_user: 当前用户
            is_approval_context: 是否在审批上下文中（审批时允许更宽松的权限检查）
        """
        # 检查管理员权限
        from app.permissions import is_admin_or_ceo
        is_admin = is_admin_or_ceo()
        
        # 审批通过后不能编辑，包括管理员也不能编辑已审批通过的批价单
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：只有当前审批人可以编辑（包括管理员也必须是当前审批人）
            # 检查是否为当前审批步骤的审批人
            target_step = pricing_order.current_approval_step
            if is_approval_context and hasattr(pricing_order, '_original_approval_step'):
                target_step = pricing_order._original_approval_step
                
            current_approval_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order.id,
                step_order=target_step,
                approver_id=current_user.id
            ).first()
            if current_approval_record:
                return True
            
            # 审批状态下，除当前审批人外，其他人都不能编辑（包括管理员）
            return False
                
        return False
    
    @staticmethod
    def can_edit_settlement_details(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑结算单明细
        
        Args:
            pricing_order: 批价单对象
            current_user: 当前用户
            is_approval_context: 是否在审批上下文中（审批时允许更宽松的权限检查）
        """
        # 只有审批中或被拒绝状态才能编辑，审批通过后不能编辑（包括管理员）
        if pricing_order.status not in ['pending', 'rejected', 'draft']:
            return False
        
        # 使用统一的管理员权限检查（状态检查已在前面完成）
        from app.permissions import is_admin_or_ceo
        is_admin = is_admin_or_ceo()
        
        # 草稿和被拒绝状态下的权限检查
        if pricing_order.status in ['draft', 'rejected']:
            # 管理员直接通过
            if is_admin:
                return True
            
            # 使用权限管理系统检查结算单权限（修正权限标识符）
            from app.permissions import check_permission
            if check_permission('settlement_edit'):
                return True
                
            # 特殊角色权限：渠道经理、营销总监、服务经理可以编辑结算单
            user_role = current_user.role.strip() if current_user.role else ''
            if user_role in ['channel_manager', 'sales_director', 'service_manager', 'business_admin', 'finance_director']:
                return True
            
            return False
        
        elif pricing_order.status == 'pending':
            # 审批中：只有当前审批人可以编辑（需要有相应角色权限）
            # 检查是否为当前审批步骤的审批人（有权限的角色）
            target_step = pricing_order.current_approval_step
            if is_approval_context and hasattr(pricing_order, '_original_approval_step'):
                target_step = pricing_order._original_approval_step
                
            current_approval_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order.id,
                step_order=target_step,
                approver_id=current_user.id
            ).first()
            if current_approval_record:
                # 检查是否是管理员或CEO（最高权限）
                if is_admin:
                    return True
                    
                # 在审批上下文中，当前审批人自动获得编辑权限
                # 特殊角色权限：渠道经理、营销总监、服务经理在审批时可以编辑结算单
                user_role = current_user.role.strip() if current_user.role else ''
                if user_role in ['channel_manager', 'sales_director', 'service_manager', 'business_admin', 'finance_director']:
                    return True
                    
                # 使用权限管理系统检查结算单权限
                from app.permissions import check_permission
                return check_permission('settlement_edit')
            
            # 审批状态下，除当前审批人外，其他人都不能编辑（包括管理员）
            return False
        
        return False
    
    @staticmethod
    def reset_settlement_approval_status(pricing_order_id):
        """重置结算单审批状态（而不是删除数据）"""
        try:
            from app.models.pricing_order import SettlementOrder, SettlementOrderDetail
            from app import db
            
            # 重置独立结算单状态为草稿
            settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order_id).first()
            if settlement_order:
                settlement_order.status = 'draft'
                settlement_order.approved_by = None
                settlement_order.approved_at = None
            
            # 重置结算单明细的结算状态
            settlement_details = SettlementOrderDetail.query.filter_by(pricing_order_id=pricing_order_id).all()
            for detail in settlement_details:
                detail.settlement_status = 'draft'
                detail.settlement_date = None
                detail.settlement_notes = None
                
        except Exception as e:
            # 记录错误但不阻断主流程
            from flask import current_app
            if current_app:
                current_app.logger.warning(f"重置批价单 {pricing_order_id} 结算状态时出错: {str(e)}")

    @staticmethod
    def recall_pricing_order(pricing_order_id, current_user_id, reason=None):
        """召回批价单"""
        try:
            pricing_order = PricingOrder.query.get(pricing_order_id)
            if not pricing_order:
                return False, "批价单不存在"
            
            # 检查权限：只有发起人可以召回
            if pricing_order.created_by != current_user_id:
                return False, "只有发起人可以召回批价单"
            
            # 检查状态：只有审批中的批价单可以召回
            if pricing_order.status != 'pending':
                return False, "只有审批中的批价单可以召回"
            
            # 更新批价单状态为草稿
            pricing_order.status = 'draft'
            pricing_order.current_approval_step = 0
            
            # 重置结算单审批状态（保留数据，仅重置状态）
            PricingOrderService.reset_settlement_approval_status(pricing_order_id)
            
            # 解锁相关对象
            PricingOrderService.unlock_related_objects(pricing_order)
            
            # 添加召回记录
            recall_record = PricingOrderApprovalRecord(
                pricing_order_id=pricing_order_id,
                step_order=pricing_order.current_approval_step,
                step_name="召回操作",
                approver_role="发起人",
                approver_id=current_user_id,
                action='recall',
                comment=f"发起人召回批价单。原因：{reason}" if reason else "发起人召回批价单",
                approved_at=datetime.now()
            )
            db.session.add(recall_record)
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, f"召回失败: {str(e)}"
    
    @staticmethod
    def can_admin_rollback_pricing_order(pricing_order_id, user_id):
        """检查是否可以执行管理员退回操作"""
        try:
            from app.models.user import User
            
            # 验证管理员或CEO权限
            user = User.query.get(user_id)
            if not user or user.role not in ['admin', 'ceo']:
                return False, "只有管理员或CEO可以执行退回操作"
            
            # 获取批价单
            pricing_order = PricingOrder.query.get(pricing_order_id)
            if not pricing_order:
                return False, "批价单不存在"
            
            # 检查状态：只能退回已通过的批价单，不能在审批过程中操作
            if pricing_order.status != 'approved':
                return False, f"只能退回已通过的批价单，当前状态：{pricing_order.status}"
            
            return True, None
            
        except Exception as e:
            return False, f"权限检查失败: {str(e)}"
    
    @staticmethod
    def can_view_settlement_tab(current_user):
        """检查是否可以查看结算单页签"""
        # admin和CEO用户直接返回True
        from app.permissions import is_admin_or_ceo
        if is_admin_or_ceo():
            return True
            
        # 检查基础结算单查看权限（使用正确的权限标识符）
        from app.permissions import check_permission
        if check_permission('settlement_view'):
            return True
            
        # 特殊角色权限：渠道经理、营销总监、服务经理可以查看结算单
        user_role = current_user.role.strip() if current_user.role else ''
        if user_role in ['channel_manager', 'sales_director', 'service_manager', 'business_admin', 'finance_director']:
            return True
            
        return False
    
    @staticmethod
    def can_view_pricing_order(pricing_order, current_user):
        """
        检查是否可以查看批价单
        根据新的权限规则：
        - 营销总监：可以看到所有的销售重点和渠道跟进的业务的批价单
        - 渠道经理：只能看到有经销商的渠道跟进和销售机会的批价单，不能看到销售重点
        - 服务经理：可以看到所有销售机会的批价单
        - 商务助理和财务总监：可以看到所有的销售重点，渠道跟进和销售机会的业务的批价单
        - 创建人和项目销售负责人：可以查看自己相关的批价单
        """
        # 管理员和CEO拥有所有权限
        from app.permissions import is_admin_or_ceo
        if is_admin_or_ceo():
            return True
        
        # 创建人可以查看
        if pricing_order.created_by == current_user.id:
            return True
            
        # 项目销售负责人可以查看
        if (pricing_order.project and 
            pricing_order.project.vendor_sales_manager_id == current_user.id):
            return True
            
        # 当前审批人可以查看
        if pricing_order.status == 'pending':
            from app.models.pricing_order import PricingOrderApprovalRecord
            current_approval_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order.id,
                step_order=pricing_order.current_approval_step,
                approver_id=current_user.id
            ).first()
            if current_approval_record:
                return True
        
        # 根据角色和项目类型检查权限
        if not pricing_order.project:
            return False
            
        project_type = pricing_order.project.project_type
        user_role = current_user.role.strip() if current_user.role else ''
        
        # 营销总监：可以看到所有的销售重点和渠道跟进的业务
        if user_role == 'sales_director':
            return project_type in ['销售重点', 'sales_key', '渠道跟进', 'channel_follow']
        
        # 渠道经理：只能看到渠道跟进和销售机会的批价单，不能看到销售重点
        if user_role == 'channel_manager':
            if project_type in ['渠道跟进', 'channel_follow', '销售机会', 'sales_opportunity']:
                # 检查是否有经销商
                return bool(pricing_order.dealer_id)
            return False
        
        # 服务经理：可以看到所有销售机会的批价单
        if user_role == 'service_manager':
            return project_type in ['销售机会', 'sales_opportunity']
        
        # 商务助理：可以看到所有的销售重点，渠道跟进的业务
        if user_role == 'business_admin':
            return project_type in ['销售重点', 'sales_key', '渠道跟进', 'channel_follow']
        
        # 财务总监：可以看到所有的销售重点，渠道跟进和销售机会的业务
        if user_role == 'finance_director':
            return project_type in ['销售重点', 'sales_key', '渠道跟进', 'channel_follow', '销售机会', 'sales_opportunity']
        
        return False

    @staticmethod
    def can_export_pdf(pricing_order, current_user, pdf_type='pricing'):
        """
        检查是否可以导出PDF
        根据新的权限规则：
        - 只有商务助理和财务总监可以打印所有的批价单和结算单
        - 其他角色根据查看权限决定是否可以导出批价单PDF
        - 结算单PDF需要更高权限
        """
        # 管理员和CEO拥有所有权限
        from app.permissions import is_admin_or_ceo
        if is_admin_or_ceo():
            return True
            
        user_role = current_user.role.strip() if current_user.role else ''
        
        # 商务助理和财务总监可以打印所有的批价单和结算单
        if user_role in ['business_admin', 'finance_director']:
            # 需要先检查是否有查看权限
            if PricingOrderService.can_view_pricing_order(pricing_order, current_user):
                return True
        
        # 其他角色只能导出批价单PDF，且需要有查看权限
        if pdf_type == 'pricing':
            return PricingOrderService.can_view_pricing_order(pricing_order, current_user)
        
        # 结算单PDF需要特殊权限（商务助理、财务总监、管理员）
        if pdf_type == 'settlement':
            if user_role in ['business_admin', 'finance_director', 'admin']:
                return PricingOrderService.can_view_pricing_order(pricing_order, current_user)
        
        return False
    
    @staticmethod
    def save_approval_data(pricing_order, pricing_details, settlement_details, basic_info, current_user, logger):
        """
        统一的审批数据保存方法
        确保批价单和结算单数据保存逻辑一致
        
        Args:
            pricing_order: 批价单对象
            pricing_details: 批价单明细数据
            settlement_details: 结算单明细数据
            basic_info: 基本信息
            current_user: 当前用户
            logger: 日志对象
            
        Returns:
            tuple: (success, error_message)
        """
        try:
            # 在审批上下文中，保存原始审批步骤用于权限检查
            pricing_order._original_approval_step = pricing_order.current_approval_step
            
            # 1. 保存基本信息
            if basic_info:
                pricing_order.is_direct_contract = basic_info.get('is_direct_contract', False)
                pricing_order.is_factory_pickup = basic_info.get('is_factory_pickup', False)
                if basic_info.get('distributor_id'):
                    pricing_order.distributor_id = basic_info.get('distributor_id')
                if basic_info.get('dealer_id'):
                    pricing_order.dealer_id = basic_info.get('dealer_id')
            
            # 2. 保存批价单明细（关键修复）
            if pricing_details:
                # 在审批上下文中检查权限（允许更宽松的权限检查）
                if not PricingOrderService.can_edit_pricing_details(pricing_order, current_user, is_approval_context=True):
                    logger.warning(f"用户 {current_user.username} 没有批价单明细编辑权限")
                else:
                    from app.models.pricing_order import PricingOrderDetail
                    logger.info(f"开始处理 {len(pricing_details)} 条批价单明细")
                    
                    for detail_data in pricing_details:
                        # 🔥 关键修复：通过产品名称查找批价单明细，而不是依赖前端传递的ID
                        product_name = detail_data.get('product_name', '').strip()
                        if not product_name:
                            logger.warning("跳过空产品名称的批价单明细")
                            continue
                        
                        # 查找对应的批价单明细
                        detail = PricingOrderDetail.query.filter_by(
                            pricing_order_id=pricing_order.id,
                            product_name=product_name
                        ).first()
                        
                        if detail:
                            logger.info(f"找到批价单明细: ID={detail.id}, 产品={product_name}")
                            
                            if 'discount_rate' in detail_data:
                                # 前端传递的是百分比形式（如40.5），需要转换为小数形式（如0.405）
                                discount_rate_percent = float(detail_data['discount_rate'])
                                old_discount_rate = detail.discount_rate
                                detail.discount_rate = discount_rate_percent / 100
                                logger.info(f"更新批价单明细 {detail.id}: 折扣率从 {old_discount_rate:.3f} 更新为 {detail.discount_rate:.3f} (前端传递: {discount_rate_percent}%)")
                            
                            if 'unit_price' in detail_data:
                                old_unit_price = detail.unit_price
                                detail.unit_price = float(detail_data['unit_price'])
                                logger.info(f"更新批价单明细 {detail.id}: 单价从 {old_unit_price:.2f} 更新为 {detail.unit_price:.2f}")
                            
                            if 'quantity' in detail_data:
                                old_quantity = detail.quantity
                                detail.quantity = int(detail_data['quantity'])
                                logger.info(f"更新批价单明细 {detail.id}: 数量从 {old_quantity} 更新为 {detail.quantity}")
                            
                            # 重新计算价格确保一致性
                            detail.calculate_prices()
                            logger.info(f"批价单明细 {detail.id} 重新计算后总价: {detail.total_price:.2f}")
                        else:
                            logger.warning(f"未找到产品名称为 '{product_name}' 的批价单明细")
            
            # 3. 保存结算单明细（关键修复）
            if settlement_details:
                if not PricingOrderService.can_edit_settlement_details(pricing_order, current_user, is_approval_context=True):
                    logger.warning(f"用户 {current_user.username} 没有结算单明细编辑权限")
                else:
                    from app.models.pricing_order import SettlementOrderDetail
                    logger.info(f"开始处理 {len(settlement_details)} 条结算单明细")
                    
                    for detail_data in settlement_details:
                        # 🔥 关键修复：通过产品名称查找结算单明细，而不是依赖前端传递的ID
                        product_name = detail_data.get('product_name', '').strip()
                        if not product_name:
                            logger.warning("跳过空产品名称的结算单明细")
                            continue
                        
                        # 查找对应的结算单明细
                        detail = SettlementOrderDetail.query.filter_by(
                            pricing_order_id=pricing_order.id,
                            product_name=product_name
                        ).first()
                        
                        if detail:
                            logger.info(f"找到结算单明细: ID={detail.id}, 产品={product_name}")
                            
                            if 'discount_rate' in detail_data:
                                # 前端传递的是百分比形式（如40.5），需要转换为小数形式（如0.405）
                                discount_rate_percent = float(detail_data['discount_rate'])
                                old_discount_rate = detail.discount_rate
                                detail.discount_rate = discount_rate_percent / 100
                                logger.info(f"更新结算单明细 {detail.id}: 折扣率从 {old_discount_rate:.3f} 更新为 {detail.discount_rate:.3f} (前端传递: {discount_rate_percent}%)")
                            
                            if 'unit_price' in detail_data:
                                old_unit_price = detail.unit_price
                                detail.unit_price = float(detail_data['unit_price'])
                                logger.info(f"更新结算单明细 {detail.id}: 单价从 {old_unit_price:.2f} 更新为 {detail.unit_price:.2f}")
                            
                            if 'quantity' in detail_data:
                                old_quantity = detail.quantity
                                detail.quantity = int(detail_data['quantity'])
                                logger.info(f"更新结算单明细 {detail.id}: 数量从 {old_quantity} 更新为 {detail.quantity}")
                            
                            # 重新计算价格确保一致性
                            detail.calculate_prices()
                            logger.info(f"结算单明细 {detail.id} 重新计算后总价: {detail.total_price:.2f}")
                        else:
                            logger.warning(f"未找到产品名称为 '{product_name}' 的结算单明细")
            
            # 4. 统一计算总金额和总折扣率
            pricing_order.calculate_pricing_totals()
            pricing_order.calculate_settlement_totals()
            
            # 5. 更新独立结算单模型（关键修复）
            from app.models.pricing_order import SettlementOrder, SettlementOrderDetail
            settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order.id).first()
            if settlement_order:
                # 修复结算单明细关系（确保 settlement_order_id 字段正确）
                settlement_details_by_po = SettlementOrderDetail.query.filter_by(pricing_order_id=pricing_order.id).all()
                for detail in settlement_details_by_po:
                    if detail.settlement_order_id != settlement_order.id:
                        detail.settlement_order_id = settlement_order.id
                        logger.info(f"修复结算单明细 {detail.id} 的关系: settlement_order_id = {settlement_order.id}")
                
                # 重新计算独立结算单的总金额
                settlement_order.calculate_totals()
                logger.info(f"更新独立结算单 {settlement_order.order_number}: 总金额 {settlement_order.total_amount:,.2f}, 折扣率 {settlement_order.discount_percentage:.1f}%")
            else:
                logger.warning(f"未找到批价单 {pricing_order.order_number} 对应的独立结算单")
            
            return True, None
            
        except Exception as e:
            logger.error(f"审批数据保存失败: {str(e)}")
            return False, f"保存数据失败: {str(e)}"

    @staticmethod
    def can_edit_quantity(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑数量字段
        
        审批状态下，数量字段应该被锁定，不允许任何人编辑
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑数量
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批状态下，数量字段锁定，任何人都不能编辑
            return False
                
        return False
    
    @staticmethod
    def can_edit_discount_and_price(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑折扣率和单价字段
        
        审批状态下，只有当前审批人可以编辑折扣率和单价
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：只有当前审批人可以编辑折扣率和单价
            # 检查是否为当前审批步骤的审批人
            target_step = pricing_order.current_approval_step
            if is_approval_context and hasattr(pricing_order, '_original_approval_step'):
                target_step = pricing_order._original_approval_step
                
            current_approval_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order.id,
                step_order=target_step,
                approver_id=current_user.id
            ).first()
            if current_approval_record:
                return True
            
            # 审批状态下，除当前审批人外，其他人都不能编辑
            return False
                
        return False
    
    @staticmethod
    def can_edit_basic_info(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑基本信息（分销商、经销商等）
        
        审批状态下，只有当前审批人可以编辑基本信息
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：只有当前审批人可以编辑基本信息
            # 检查是否为当前审批步骤的审批人
            target_step = pricing_order.current_approval_step
            if is_approval_context and hasattr(pricing_order, '_original_approval_step'):
                target_step = pricing_order._original_approval_step
                
            current_approval_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order.id,
                step_order=target_step,
                approver_id=current_user.id
            ).first()
            if current_approval_record:
                return True
            
            # 审批状态下，除当前审批人外，其他人都不能编辑
            return False
                
        return False
    
    @staticmethod
    def admin_rollback_pricing_order(pricing_order_id, admin_user_id, reason=None):
        """管理员将已通过的批价单退回到草稿状态（清除所有审批痕迹）"""
        try:
            from app.models.user import User
            
            # 先检查权限
            can_rollback, error_msg = PricingOrderService.can_admin_rollback_pricing_order(
                pricing_order_id, admin_user_id
            )
            if not can_rollback:
                return False, error_msg
            
            # 获取用户和批价单
            admin_user = User.query.get(admin_user_id)
            pricing_order = PricingOrder.query.get(pricing_order_id)
            
            # 开始数据库事务
            from app import db
            from flask import current_app
            
            # 1. 删除所有审批记录（清除痕迹）
            approval_records = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order_id
            ).all()
            
            for record in approval_records:
                db.session.delete(record)
            
            # 2. 重置批价单状态为草稿
            pricing_order.status = 'draft'
            pricing_order.current_approval_step = 0
            pricing_order.approved_at = None
            pricing_order.final_approver_id = None
            
            # 3. 重置结算单审批状态（保留数据，仅重置状态）
            PricingOrderService.reset_settlement_approval_status(pricing_order_id)
            
            # 4. 解锁相关对象
            PricingOrderService.unlock_related_objects(pricing_order)
            
            # 5. 记录操作日志
            current_app.logger.info(
                f"管理员 {admin_user.username} (ID: {admin_user_id}) "
                f"将批价单 {pricing_order.order_number} (ID: {pricing_order_id}) 的审批状态退回到草稿状态。"
                f"原因：{reason or '未提供'}"
            )
            
            # 提交事务
            db.session.commit()
            
            return True, "批价单审批已成功退回到草稿状态，所有审批记录已清除"
            
        except Exception as e:
            db.session.rollback()
            return False, f"退回失败: {str(e)}" 