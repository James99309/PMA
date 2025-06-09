from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
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


class PricingOrderService:
    """批价单服务类"""
    
    # 快速通过折扣率规则
    FAST_APPROVAL_RULES = {
        '渠道经理': 40.5,
        '营销总监': 38.0,
        '服务经理': 40.5,
        '总经理': 0.0  # 总经理无限制
    }
    
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
        """根据角色名称获取用户ID"""
        # 角色映射
        role_mapping = {
            '渠道经理': 'channel_manager',
            '营销总监': 'sales_director', 
            '服务经理': 'service_manager',
            '总经理': 'admin',
            '财务经理': 'finance_director'
        }
        
        # 获取对应的系统角色
        system_role = role_mapping.get(role_name)
        if not system_role:
            # 如果没有找到对应角色，返回管理员
            admin_user = User.query.filter_by(role='admin').first()
            return admin_user.id if admin_user else 1
        
        # 查找对应角色的用户
        user = User.query.filter_by(role=system_role).first()
        if user:
            return user.id
        
        # 如果没有找到，回退到管理员
        admin_user = User.query.filter_by(role='admin').first()
        return admin_user.id if admin_user else 1
    
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
            
            # 创建批价单
            pricing_order = PricingOrder(
                project_id=project_id,
                quotation_id=quotation_id,
                distributor_id=distributor_id,
                dealer_id=dealer_id or getattr(project, 'dealer_id', None),  # 安全地获取经销商ID
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
            
            if pricing_order.status != 'draft':
                return False, "只有草稿状态的批价单可以提交审批"
            
            # 更新状态为审批中
            pricing_order.status = 'pending'
            pricing_order.current_approval_step = 1
            
            # 锁定项目和报价单
            project = pricing_order.project
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
    def approve_step(pricing_order_id, step_order, current_user_id, action, comment=None):
        """审批步骤"""
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
                PricingOrderService.unlock_related_objects(pricing_order)
                
            elif action == 'approve':
                # 检查是否满足快速通过条件
                is_fast_approval = PricingOrderService.check_fast_approval(approval_record, pricing_order)
                
                if is_fast_approval:
                    # 快速通过：标记当前步骤为快速通过，并自动通过后续所有步骤
                    approval_record.is_fast_approval = True
                    approval_record.fast_approval_reason = f"结算单折扣率达到{approval_record.approver_role}快速通过标准"
                    
                    # 自动通过后续所有步骤
                    PricingOrderService.auto_approve_remaining_steps(pricing_order, current_user_id, approval_record.approver_role)
                    
                    # 注意：不再重新计算总金额和总折扣率，保持前端传递的数据
                    # 前端数据已经在审批路由中保存，这里直接使用
                    
                    pricing_order.status = 'approved'
                    pricing_order.approved_by = current_user_id
                    pricing_order.approved_at = datetime.now()
                    # 快速通过时，将当前步骤设置为0，表示流程结束
                    pricing_order.current_approval_step = 0
                    
                    # 更新项目状态为签约
                    PricingOrderService.complete_approval(pricing_order)
                    
                    # 发送邮件通知后续审批人
                    PricingOrderService.send_completion_notifications(pricing_order, approval_record)
                    
                else:
                    # 检查是否还有下一步
                    next_step = PricingOrderApprovalRecord.query.filter_by(
                        pricing_order_id=pricing_order_id,
                        step_order=step_order + 1
                    ).first()
                    
                    if next_step:
                        # 进入下一步
                        pricing_order.current_approval_step = step_order + 1
                    else:
                        # 最后一步：完成审批
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
    
    @staticmethod
    def auto_approve_remaining_steps(pricing_order, current_user_id, fast_approval_role):
        """自动通过后续所有审批步骤"""
        try:
            # 获取当前步骤之后的所有审批记录
            remaining_steps = PricingOrderApprovalRecord.query.filter(
                PricingOrderApprovalRecord.pricing_order_id == pricing_order.id,
                PricingOrderApprovalRecord.step_order > pricing_order.current_approval_step,
                PricingOrderApprovalRecord.action.is_(None)  # 只处理未审批的步骤
            ).all()
            
            # 自动通过所有后续步骤
            for step_record in remaining_steps:
                step_record.action = 'approve'
                step_record.comment = f'因{fast_approval_role}快速通过而自动审批'
                step_record.approved_at = datetime.now()
                step_record.is_fast_approval = True
                step_record.fast_approval_reason = f'因{fast_approval_role}快速通过而自动审批'
            
            return True
            
        except Exception as e:
            from app import current_app
            current_app.logger.error(f"自动通过后续步骤失败: {str(e)}")
            return False
    
    @staticmethod
    def check_fast_approval(approval_record, pricing_order):
        """检查是否满足快速通过条件"""
        approver_role = approval_record.approver_role
        if approver_role not in PricingOrderService.FAST_APPROVAL_RULES:
            return False
        
        min_discount_rate = PricingOrderService.FAST_APPROVAL_RULES[approver_role]
        if min_discount_rate == 0:  # 总经理无限制
            return True
        
        # 检查结算单折扣率
        settlement_discount_percentage = pricing_order.settlement_discount_percentage
        return settlement_discount_percentage >= min_discount_rate
    
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
    def can_edit_pricing_details(pricing_order, current_user):
        """检查是否可以编辑批价单明细"""
        # 审批通过或拒绝后，任何人都不能编辑
        if pricing_order.status in ['approved', 'rejected']:
            return False
            
        if pricing_order.status == 'draft':
            # 草稿状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：发起人、厂商销售负责人和当前审批人可编辑
            if pricing_order.created_by == current_user.id:
                return True
            if (pricing_order.project and 
                pricing_order.project.vendor_sales_manager_id == current_user.id):
                return True
            
            # 检查是否为当前审批步骤的审批人
            current_approval_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order.id,
                step_order=pricing_order.current_approval_step,
                approver_id=current_user.id
            ).first()
            if current_approval_record:
                return True
                
        return False
    
    @staticmethod
    def can_edit_settlement_details(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑结算单明细
        
        Args:
            pricing_order: 批价单对象
            current_user: 当前用户
            is_approval_context: 是否在审批上下文中（审批时允许更宽松的权限检查）
        """
        # 在审批上下文中，允许审批人编辑结算单明细，即使状态即将改变
        if not is_approval_context:
            # 只有审批中状态才能编辑，审批通过或拒绝后不能编辑
            if pricing_order.status != 'pending':
                return False
        
        # 只有特定角色可以查看和编辑结算单
        allowed_roles = ['渠道经理', '营销总监', '服务经理', '财务经理', 'admin']
        user_roles = [role.name for role in current_user.roles] if hasattr(current_user, 'roles') else []
        
        if current_user.role == 'admin':
            return True
        
        for role in user_roles:
            if role in allowed_roles:
                return True
        
        # 检查是否为当前审批步骤的审批人（有权限的角色）
        # 在审批上下文中，使用原始的审批步骤，而不是当前可能已经改变的步骤
        target_step = pricing_order.current_approval_step
        if is_approval_context and hasattr(pricing_order, '_original_approval_step'):
            target_step = pricing_order._original_approval_step
            
        current_approval_record = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=pricing_order.id,
            step_order=target_step,
            approver_id=current_user.id
        ).first()
        if current_approval_record:
            # 审批人需要有相应的角色权限才能编辑结算单
            role_mapping = {
                'channel_manager': '渠道经理',
                'sales_director': '营销总监', 
                'service_manager': '服务经理',
                'finance_manager': '财务经理',
                'admin': 'admin'
            }
            
            user_role = current_user.role.strip() if hasattr(current_user, 'role') else ''
            if user_role in role_mapping:
                mapped_role = role_mapping[user_role]
                if mapped_role in allowed_roles:
                    return True
            
            # 直接检查中文角色名
            if user_role in allowed_roles:
                return True
        
        return False
    
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
    def can_view_settlement_tab(current_user):
        """检查是否可以查看结算单页签"""
        # admin用户直接返回True
        if current_user.role == 'admin':
            return True
            
        allowed_roles = ['渠道经理', '营销总监', '服务经理', '财务经理', 'admin']
        
        # 检查用户角色
        if hasattr(current_user, 'roles') and current_user.roles:
            user_roles = [role.name for role in current_user.roles]
            for role in user_roles:
                if role in allowed_roles:
                    return True
        
        # 如果用户没有roles属性，但role字段包含允许的角色
        if hasattr(current_user, 'role') and current_user.role:
            user_role = current_user.role.strip()
            # 将英文角色映射到中文角色
            role_mapping = {
                'channel_manager': '渠道经理',
                'sales_director': '营销总监', 
                'service_manager': '服务经理',
                'finance_manager': '财务经理',
                'admin': 'admin'
            }
            
            if user_role in role_mapping:
                mapped_role = role_mapping[user_role]
                if mapped_role in allowed_roles:
                    return True
            
            # 直接检查中文角色名
            if user_role in allowed_roles:
                return True
        
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
            
            # 2. 保存批价单明细
            if pricing_details:
                if not PricingOrderService.can_edit_pricing_details(pricing_order, current_user):
                    logger.warning(f"用户 {current_user.username} 没有批价单明细编辑权限")
                else:
                    for detail_data in pricing_details:
                        detail_id = detail_data.get('id')
                        if detail_id:
                            from app.models.pricing_order import PricingOrderDetail
                            detail = PricingOrderDetail.query.get(detail_id)
                            if detail and detail.pricing_order_id == pricing_order.id:
                                if 'quantity' in detail_data:
                                    detail.quantity = int(detail_data['quantity'])
                                if 'discount_rate' in detail_data:
                                    detail.discount_rate = float(detail_data['discount_rate']) / 100
                                if 'unit_price' in detail_data:
                                    detail.unit_price = float(detail_data['unit_price'])
                                if 'total_price' in detail_data:
                                    detail.total_price = float(detail_data['total_price'])
                                logger.info(f"审批时更新批价单明细 {detail_id}: 折扣率 {detail.discount_rate:.3f}")
            
            # 3. 保存结算单明细（关键修复）
            if settlement_details:
                if not PricingOrderService.can_edit_settlement_details(pricing_order, current_user, is_approval_context=True):
                    logger.warning(f"用户 {current_user.username} 没有结算单明细编辑权限")
                else:
                    from app.models.pricing_order import SettlementOrderDetail
                    for detail_data in settlement_details:
                        detail_id = detail_data.get('id')
                        if detail_id:
                            detail = SettlementOrderDetail.query.get(detail_id)
                            if detail and detail.pricing_order_id == pricing_order.id:
                                if 'discount_rate' in detail_data:
                                    # 前端传递的是百分比形式（如40.5），需要转换为小数形式（如0.405）
                                    discount_rate_percent = float(detail_data['discount_rate'])
                                    detail.discount_rate = discount_rate_percent / 100
                                    logger.info(f"审批时更新结算单明细 {detail_id}: 折扣率从前端 {discount_rate_percent}% 转换为 {detail.discount_rate:.3f}")
                                if 'unit_price' in detail_data:
                                    detail.unit_price = float(detail_data['unit_price'])
                                if 'total_price' in detail_data:
                                    detail.total_price = float(detail_data['total_price'])
                                # 重新计算价格确保一致性
                                detail.calculate_prices()
            
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