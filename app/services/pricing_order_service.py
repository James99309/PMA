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
    
    # 流程版本切换的时间节点
    V2_CUTOFF_DATE = datetime(2025, 1, 1)
    
    @staticmethod
    def should_use_v2_flow(pricing_order=None):
        """判断是否应该使用V2流程 - 强制使用V2系统"""
        # 🔥 V1系统已废弃，所有批价单强制使用V2统一审批系统
        return True
    
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
        elif project_type in ["销售机会", "sales_opportunity", "business_opportunity"]:
            return 'sales_opportunity'
        elif project_type in ["销售重点", "sales_key", "sales_focus"]:
            return 'sales_key'
        else:
            # 默认为销售重点类
            return 'sales_key'
    
    # V2 新方法：提交前验证
    @staticmethod
    def validate_before_submit_v2(pricing_order, current_user):
        """提交前完整验证 - V2版本"""
        errors = []
        warnings = []
        
        # 1. 检查项目是否存在
        project = pricing_order.project
        if not project:
            errors.append("批价单关联的项目不存在")
            return False, errors, warnings
        
        # 2. 检查项目是否有厂家负责人（关键验证）
        if not project.vendor_sales_manager_id:
            errors.append("项目必须设置厂家负责人才能提交批价单。请先在项目页面设置厂家销售负责人。")
            return False, errors, warnings
        
        # 3. 验证厂家负责人是否存在
        vendor_sales_manager = project.vendor_sales_manager
        if not vendor_sales_manager:
            errors.append("项目设置的厂家销售负责人不存在，请重新设置")
            return False, errors, warnings
        
        # 4. 检查厂商直签的有效性
        if pricing_order.is_direct_contract and not current_user.is_vendor_user():
            warnings.append("非厂家账户无法使用厂商直签功能，该选项将被忽略")
        
        # 5. 检查是否能找到必要的审批人角色
        admin_id = PricingOrderService.get_role_user_id_v2('admin')
        if not admin_id:
            errors.append("系统缺少管理员角色，无法发起审批流程")
            return False, errors, warnings
        
        # 6. 检查部门负责人（非致命错误，但需要警告）
        dept_manager = PricingOrderService.get_department_manager(current_user.id)
        if not dept_manager:
            warnings.append("您没有设置部门负责人，部门审批环节将被跳过")
        
        # 7. 检查渠道经理（非致命错误）
        channel_manager_id = PricingOrderService.get_role_user_id_v2('channel_manager')
        if not channel_manager_id:
            warnings.append("系统缺少渠道经理角色，渠道审批环节将被跳过")
        
        return True, errors, warnings
    
    @staticmethod
    def get_department_manager(user_id):
        """获取用户的部门负责人"""
        try:
            user = User.query.get(user_id)
            if not user or not user.department or not user.company_name:
                return None
            
            # 查找部门负责人
            department_manager = User.query.filter_by(
                department=user.department,
                company_name=user.company_name,
                is_department_manager=True
            ).first()
            
            return department_manager
        except Exception as e:
            logger.error(f"获取部门负责人失败: {str(e)}")
            return None
    
    @staticmethod
    def get_role_user_id_v2(role_name):
        """获取指定角色的用户ID - V2版本"""
        try:
            user = User.query.filter_by(role=role_name).first()
            return user.id if user else None
        except Exception as e:
            logger.error(f"获取角色用户失败: {role_name}, {str(e)}")
            return None
    
    @staticmethod
    def normalize_direct_contract_status(pricing_order, current_user):
        """规范化厂商直签状态（草稿阶段自动判断）"""
        try:
            # 如果当前用户不是厂家账户，强制将厂商直签设为False
            if pricing_order.is_direct_contract and not current_user.is_vendor_user():
                pricing_order.is_direct_contract = False
                logger.info(f"非厂家账户 {current_user.username} 的厂商直签状态已自动设置为False")
                return True, "非厂家账户无法使用厂商直签功能，已自动关闭"
            
            return True, None
        except Exception as e:
            logger.error(f"规范化厂商直签状态失败: {str(e)}")
            return False, f"处理失败: {str(e)}"
            
    @staticmethod
    def apply_direct_contract_to_pricing_order(pricing_order, current_user):
        """处理厂商直签设置，保持经销商和分销商为空"""
        try:
            if pricing_order.is_direct_contract:
                # 厂商直签时，保持经销商和分销商为空
                pricing_order.dealer_id = None
                pricing_order.distributor_id = None
                logger.info("厂商直签开启，经销商和分销商保持为空")
                return True, "厂商直签已启用，经销商和分销商设置为空"
                        
            return True, None
        except Exception as e:
            logger.error(f"应用厂商直签设置失败: {str(e)}")
            return False, f"处理失败: {str(e)}"
    
    @staticmethod
    def get_vendor_company_name():
        """获取厂商企业名称（已废弃，保留向后兼容）"""
        from app.models.dictionary import Dictionary
        vendor_company = Dictionary.query.filter_by(
            type='company',
            is_vendor=True,
            is_active=True
        ).first()
        return vendor_company.value if vendor_company else "和源通信（上海）股份有限公司"
    
    @staticmethod
    def generate_approval_steps_v2(pricing_order, submitter_id):
        """生成新版本的审批步骤 - V2版本"""
        steps = []
        project = pricing_order.project
        submitter = User.query.get(submitter_id)
        
        if not project or not submitter:
            logger.error("项目或提交人信息缺失")
            return []
        
        vendor_sales_manager = project.vendor_sales_manager
        is_direct_contract = pricing_order.is_direct_contract
        
        # 步骤计数器
        step_order = 1
        
        # 第一步：如果发起人不是厂家销售负责人，需要先经过厂家负责人审批
        if vendor_sales_manager and vendor_sales_manager.id != submitter_id:
            steps.append({
                'step_order': step_order,
                'step_name': '厂家销售负责人审批',
                'approver_role': '厂家销售负责人',
                'approver_id': vendor_sales_manager.id
            })
            step_order += 1
        
        # 判断是否为厂家账户发起
        is_vendor_submitter = submitter.is_vendor_user()
        
        # 如果非厂家账户发起，厂商直签开关无效
        effective_direct_contract = is_direct_contract and is_vendor_submitter
        
        if effective_direct_contract:
            # 厂商直签流程：部门负责人 → 管理员
            dept_manager = PricingOrderService.get_department_manager(submitter_id)
            if dept_manager:
                steps.append({
                    'step_order': step_order,
                    'step_name': '部门负责人审批',
                    'approver_role': '部门负责人',
                    'approver_id': dept_manager.id
                })
                step_order += 1
            else:
                # 部门负责人缺失，跳到下一步
                logger.warning(f"提交人 {submitter_id} 部门负责人缺失，跳过部门负责人审批")
        else:
            # 非厂商直签流程：渠道经理 → 部门负责人 → 管理员
            channel_manager_id = PricingOrderService.get_role_user_id_v2('channel_manager')
            if channel_manager_id:
                steps.append({
                    'step_order': step_order,
                    'step_name': '渠道经理审批',
                    'approver_role': '渠道经理',
                    'approver_id': channel_manager_id
                })
                step_order += 1
            else:
                logger.warning("渠道经理角色缺失，跳过渠道经理审批")
            
            # 部门负责人审批
            dept_manager = PricingOrderService.get_department_manager(submitter_id)
            if dept_manager:
                steps.append({
                    'step_order': step_order,
                    'step_name': '部门负责人审批',
                    'approver_role': '部门负责人',
                    'approver_id': dept_manager.id
                })
                step_order += 1
            else:
                logger.warning(f"提交人 {submitter_id} 部门负责人缺失，跳过部门负责人审批")
        
        # 最后一步：管理员审批
        admin_id = PricingOrderService.get_role_user_id_v2('admin')
        if admin_id:
            steps.append({
                'step_order': step_order,
                'step_name': '管理员审批',
                'approver_role': '管理员',
                'approver_id': admin_id
            })
        else:
            logger.error("管理员角色缺失，无法完成审批流程")
            return []  # 无管理员则无法审批
        
        return steps
    
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
        from app.models.product import Product
        from app.models.quotation import QuotationDetail
        from sqlalchemy import case
        
        # 使用与报价单详情页面相同的排序逻辑
        # 优先显示产品库中的产品（按Product.id排序），然后显示不在产品库中的产品（按QuotationDetail.id排序）
        sorted_details = db.session.query(QuotationDetail)\
            .outerjoin(Product, Product.product_name == QuotationDetail.product_name)\
            .filter(QuotationDetail.quotation_id == quotation.id)\
            .order_by(case((Product.id.is_(None), 1), else_=0), Product.id.asc(), QuotationDetail.id.asc())\
            .all()
        
        for qd in sorted_details:
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
        """更新结算单明细 - 只影响结算单，不影响批价单"""
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
            
            # 🔥 关键修复：只重新计算结算单总额，不影响批价单
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
                # 🔥 关键修复：更新结算单时不影响批价单
                # 只更新结算单所有明细的折扣率，不同步到批价单
                for detail in pricing_order.settlement_details:
                    detail.discount_rate = total_discount_rate
                    detail.calculate_prices()
                
                pricing_order.settlement_total_discount_rate = total_discount_rate
                # 🔥 关键修复：只重新计算结算单总额，不计算批价单总额
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
        """提交审批 - 支持V1/V2版本"""
        try:
            pricing_order = PricingOrder.query.get(pricing_order_id)
            if not pricing_order:
                return False, "批价单不存在"

            if pricing_order.status not in ['draft', 'rejected']:
                return False, "只有草稿状态或被拒绝的批价单可以提交审批"

            current_user = User.query.get(current_user_id)
            if not current_user:
                return False, "当前用户不存在"

            # V1系统已废弃，所有批价单使用V2统一审批系统
            return PricingOrderService._submit_for_approval_v2(pricing_order, current_user)
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"提交审批失败: {str(e)}")
            return False, f"提交失败: {str(e)}"
    
    
    @staticmethod
    def _submit_for_approval_v2(pricing_order, current_user):
        """提交审批 - V2版本（使用统一审批流程系统）"""
        try:
            # 规范化厂商直签状态
            normalized, message = PricingOrderService.normalize_direct_contract_status(pricing_order, current_user)
            if not normalized:
                return False, message
            
            # 应用厂商直签设置（在提交时自动填入当前用户的企业名称）
            applied, apply_message = PricingOrderService.apply_direct_contract_to_pricing_order(pricing_order, current_user)
            if not applied:
                return False, apply_message
            
            # 提交前完整验证
            can_submit, errors, warnings = PricingOrderService.validate_before_submit_v2(pricing_order, current_user)
            if not can_submit:
                return False, "; ".join(errors)
            
            # V2版本：使用统一审批流程系统
            from app.helpers.approval_helpers import start_approval_process, get_available_templates
            
            # 获取批价单审批模板
            templates = get_available_templates('pricing_order')
            if not templates:
                return False, "未找到批价单审批模板"
            
            # 使用第一个可用模板（应该只有一个）
            template = templates[0]
            
            # 启动审批流程
            approval_instance = start_approval_process(
                object_type='pricing_order',
                object_id=pricing_order.id,
                template_id=template.id,
                user_id=current_user.id
            )
            
            if not approval_instance:
                return False, "创建审批流程失败"
            
            # 清理旧的审批记录（V1系统的记录）
            old_records = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order.id
            ).all()
            for record in old_records:
                db.session.delete(record)
            
            # 更新状态为审批中（统一审批系统会自动处理步骤）
            pricing_order.status = 'pending'
            
            # 锁定项目和报价单
            project = pricing_order.project
            if project:
                project.is_locked = True
                project.locked_reason = "批价审批流程进行中"
                project.locked_by = current_user.id
                project.locked_at = datetime.now()
            
            quotation = pricing_order.quotation
            if quotation:
                quotation.is_locked = True
                quotation.lock_reason = "批价审批流程进行中"
                quotation.locked_by = current_user.id
                quotation.locked_at = datetime.now()
            
            db.session.commit()
            
            # 构建返回消息
            success_message = f"批价单提交审批成功，使用统一审批流程系统"
            if warnings:
                success_message += f"。注意：{'; '.join(warnings)}"
            
            logger.info(f"批价单 {pricing_order.order_number} 使用V2流程（统一审批系统）提交审批成功，审批实例ID: {approval_instance.id}")
            return True, success_message
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"V2提交审批失败: {str(e)}")
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
            return False    @staticmethod
    def _is_current_approver_v2(pricing_order, current_user):
        """检查用户是否为V2统一审批系统中的当前审批人"""
        try:
            from app.helpers.approval_helpers import get_object_approval_instance
            from app.models.approval import ApprovalStatus, ApprovalStep
            
            # 获取当前审批实例
            approval_instance = get_object_approval_instance('pricing_order', pricing_order.id)
            if not approval_instance or approval_instance.status != ApprovalStatus.PENDING:
                return False
                
            # 检查当前步骤的审批人
            current_step = ApprovalStep.query.get(approval_instance.current_step)
            if current_step and current_step.approver_user_id == current_user.id:
                return True
                
            return False
        except Exception:
            return False


    
    @staticmethod
    def can_edit_pricing_details(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑批价单明细 - V2统一审批系统
        
        Args:
            pricing_order: 批价单对象
            current_user: 当前用户
            is_approval_context: 是否在审批上下文中
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：只有当前审批人可以编辑
            return PricingOrderService._is_current_approver_v2(pricing_order, current_user)
                
        return False
    @staticmethod
    def can_edit_settlement_details(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑结算单明细 - V2统一审批系统
        
        Args:
            pricing_order: 批价单对象
            current_user: 当前用户
            is_approval_context: 是否在审批上下文中
        """
        # 只有审批中或被拒绝状态才能编辑，审批通过后不能编辑
        if pricing_order.status not in ['pending', 'rejected', 'draft']:
            return False
        
        from app.permissions import is_admin_or_ceo, check_permission
        is_admin = is_admin_or_ceo()
        
        # 草稿和被拒绝状态下的权限检查
        if pricing_order.status in ['draft', 'rejected']:
            # 管理员直接通过
            if is_admin:
                return True
            
            # 使用权限管理系统检查结算单权限
            if check_permission('settlement_edit'):
                return True
                
            # 特殊角色权限：渠道经理、营销总监、服务经理可以编辑结算单
            user_role = current_user.role.strip() if current_user.role else ''
            if user_role in ['channel_manager', 'sales_director', 'service_manager', 'business_admin', 'finance_director']:
                return True
            
            return False
        
        elif pricing_order.status == 'pending':
            # 审批中：V2系统下，只有当前审批人可以编辑
            if PricingOrderService._is_current_approver_v2(pricing_order, current_user):
                # 管理员或在审批上下文中自动获得权限
                if is_admin or is_approval_context:
                    return True
                    
                # 检查角色权限
                if check_permission('settlement_edit'):
                    return True
                    
                # 特殊角色权限
                user_role = current_user.role.strip() if current_user.role else ''
                if user_role in ['channel_manager', 'sales_director', 'service_manager', 'business_admin', 'finance_director']:
                    return True
            
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
            
            # 检查是否使用V2流程系统
            use_v2 = PricingOrderService.should_use_v2_flow(pricing_order)
            
            if use_v2:
                # V2流程：处理统一审批系统
                from app.helpers.approval_helpers import get_object_approval_instance
                from app.models.approval import ApprovalStatus
                
                approval_instance = get_object_approval_instance('pricing_order', pricing_order_id)
                if approval_instance:
                    # 更新审批实例状态为召回
                    approval_instance.status = ApprovalStatus.RECALLED
                    approval_instance.ended_at = datetime.now()
                    
                    # 添加召回记录到统一系统
                    from app.models.approval import ApprovalRecord
                    recall_record = ApprovalRecord(
                        instance_id=approval_instance.id,
                        step_id=approval_instance.current_step,
                        approver_id=current_user_id,
                        action='recall',
                        comment=f"发起人召回批价单。原因：{reason}" if reason else "发起人召回批价单",
                        timestamp=datetime.now()
                    )
                    db.session.add(recall_record)
                    logger.info(f"V2流程：批价单 {pricing_order_id} 审批实例 {approval_instance.id} 已召回")
                else:
                    logger.warning(f"V2流程的批价单 {pricing_order_id} 没有找到审批实例")
            else:
                # V1流程：添加召回记录
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
                logger.info(f"V1流程：批价单 {pricing_order_id} 已召回")
            
            # 更新批价单状态为草稿
            pricing_order.status = 'draft'
            pricing_order.current_approval_step = 0
            
            # 重置结算单审批状态（保留数据，仅重置状态）
            PricingOrderService.reset_settlement_approval_status(pricing_order_id)
            
            # 解锁相关对象
            PricingOrderService.unlock_related_objects(pricing_order)
            
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
            # V2统一审批系统：检查是否为当前审批人
            if PricingOrderService._is_current_approver_v2(pricing_order, current_user):
                return True
            
            # 兼容V1系统（如果还有遗留数据）
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
            return project_type in ['销售重点', 'sales_key', 'sales_focus', '渠道跟进', 'channel_follow']
        
        # 渠道经理：可以看到其权限范围内的批价单
        if user_role == 'channel_manager':
            return True  # 权限控制交由access_control.py统一管理
        
        # 服务经理：可以看到其权限范围内的所有批价单
        if user_role == 'service_manager':
            return True  # 权限控制交由access_control.py统一管理
        
        # 商务助理：可以看到其权限范围内的批价单
        if user_role == 'business_admin':
            return True  # 权限控制交由access_control.py统一管理
        
        # 财务总监：可以看到其权限范围内的所有批价单
        if user_role == 'finance_director':
            return True  # 权限控制交由access_control.py统一管理
        
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
                                # 🔥 关键修复：审批状态下严禁修改数量
                                if pricing_order.status == 'pending':
                                    logger.warning(f"审批状态下拒绝修改数量：产品={product_name}, 当前数量={detail.quantity}, 尝试修改为={detail_data['quantity']}")
                                else:
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
                                # 🔥 关键修复：审批状态下严禁修改数量
                                if pricing_order.status == 'pending':
                                    logger.warning(f"审批状态下拒绝修改数量：产品={product_name}, 当前数量={detail.quantity}, 尝试修改为={detail_data['quantity']}")
                                else:
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
        """检查是否可以编辑折扣率和单价字段 - V2统一审批系统
        
        审批状态下，只有当前审批人可以编辑折扣率和单价
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：V2系统下，只有当前审批人可以编辑折扣率和单价
            return PricingOrderService._is_current_approver_v2(pricing_order, current_user)
                
        return False
    @staticmethod
    def can_edit_basic_info(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑基本信息（分销商、经销商等） - V2统一审批系统
        
        审批状态下，只有当前审批人可以编辑基本信息
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：V2系统下，只有当前审批人可以编辑基本信息
            return PricingOrderService._is_current_approver_v2(pricing_order, current_user)
                
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
    
    @staticmethod
    def can_modify_direct_contract(pricing_order, current_user):
        """检查是否可以修改厂商直签状态 - V2版本专用"""
        # 只有厂家账户可以设置厂商直签状态
        if not current_user.is_vendor_user():
            return False, "只有厂家账户可以设置厂商直签状态"
        
        # 审批中和审批通过后都不可修改（修正：审批中不能修改）
        if pricing_order.status in ['pending', 'approved']:
            return False, "审批过程中和审批通过后不可修改厂商直签状态"
        
        return True, None
        
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
                                # 🔥 关键修复：审批状态下严禁修改数量
                                if pricing_order.status == 'pending':
                                    logger.warning(f"审批状态下拒绝修改数量：产品={product_name}, 当前数量={detail.quantity}, 尝试修改为={detail_data['quantity']}")
                                else:
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
                                # 🔥 关键修复：审批状态下严禁修改数量
                                if pricing_order.status == 'pending':
                                    logger.warning(f"审批状态下拒绝修改数量：产品={product_name}, 当前数量={detail.quantity}, 尝试修改为={detail_data['quantity']}")
                                else:
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
        """检查是否可以编辑折扣率和单价字段 - V2统一审批系统
        
        审批状态下，只有当前审批人可以编辑折扣率和单价
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：V2系统下，只有当前审批人可以编辑折扣率和单价
            return PricingOrderService._is_current_approver_v2(pricing_order, current_user)
                
        return False
    @staticmethod
    def can_edit_basic_info(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑基本信息（分销商、经销商等） - V2统一审批系统
        
        审批状态下，只有当前审批人可以编辑基本信息
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：V2系统下，只有当前审批人可以编辑基本信息
            return PricingOrderService._is_current_approver_v2(pricing_order, current_user)
                
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
    
    @staticmethod
    def can_modify_direct_contract(pricing_order, current_user):
        """检查是否可以修改厂商直签状态 - V2版本专用"""
        # 只有厂家账户可以设置厂商直签状态
        if not current_user.is_vendor_user():
            return False, "只有厂家账户可以设置厂商直签状态"
        
        # 审批中和审批通过后都不可修改（修正：审批中不能修改）
        if pricing_order.status in ['pending', 'approved']:
            return False, "审批过程中和审批通过后不可修改厂商直签状态"
        
        return True, None