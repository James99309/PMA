from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
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
        """根据项目信息确定审批流程类型 - 返回真实项目类型，不再进行V1兼容转换"""
        if not project:
            return 'sales_focus'  # 默认为销售重点，而不是兼容的sales_key
        
        project_type = project.project_type
        # 直接返回真实的项目类型，移除V1兼容转换
        if project_type == "channel_follow":
            return 'channel_follow'
        elif project_type == "business_opportunity":
            return 'sales_opportunity'
        elif project_type == "sales_focus":
            return 'sales_focus'  # 返回真实类型，不再转换为sales_key
        elif project_type == "sales_key":
            return 'sales_key'    # 保持已有的sales_key类型
        else:
            # 默认为销售重点类型
            return 'sales_focus'
    
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

        # 4. 检查报价单确认标签（确保批价单基于已确认的报价单数据）
        quotation = pricing_order.quotation
        if quotation:
            # 检查报价单是否有确认徽章
            if quotation.confirmation_badge_status != 'confirmed':
                errors.append(f"报价单 {quotation.quotation_number} 产品明细尚未确认，无法提交批价单。请先在报价单页面确认产品明细。")
                return False, errors, warnings
        else:
            # 如果没有关联报价单，也是错误
            errors.append("批价单必须关联报价单才能提交审批")
            return False, errors, warnings

        # 5. 检查厂商直签的有效性
        if pricing_order.is_direct_contract and not current_user.is_vendor_user():
            warnings.append("非厂家账户无法使用厂商直签功能，该选项将被忽略")

        # 6. 检查是否能找到必要的审批人角色
        admin_id = PricingOrderService.get_role_user_id_v2('admin')
        if not admin_id:
            errors.append("系统缺少管理员角色，无法发起审批流程")
            return False, errors, warnings

        # 7. 检查部门负责人（非致命错误，但需要警告）
        dept_manager = PricingOrderService.get_department_manager(current_user.id)
        if not dept_manager:
            warnings.append("您没有设置部门负责人，部门审批环节将被跳过")

        # 8. 检查渠道经理（非致命错误）
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
                old_dealer_id = pricing_order.dealer_id
                old_distributor_id = pricing_order.distributor_id
                
                pricing_order.dealer_id = None
                pricing_order.distributor_id = None
                
                return True, "厂商直签已启用，经销商和分销商设置为空"
            else:
                return True, None
        except Exception as e:
            logger.error(f"🔍 [DIRECT_CONTRACT] ❌ 应用厂商直签设置失败: {str(e)}")
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
            
            # 自动获取项目中的经销商ID（从关联表查询）
            project_dealer_id = None
            if not dealer_id:
                from app.models.customer import Company
                from app.models.project_customer_association import ProjectCustomerAssociation

                # 从ProjectCustomerAssociation关联表获取经销商
                dealer_association = ProjectCustomerAssociation.query.filter_by(
                    project_id=project_id,
                    customer_type='dealer'
                ).first()

                if dealer_association:
                    dealer_company = Company.query.filter_by(
                        id=dealer_association.company_id,
                        is_deleted=False
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
        """创建结算单

        根据批价单的业务类型设置结算单的客户ID：
        1. 厂商直签 (is_direct_contract=True): dealer_id=NULL, distributor_id=NULL
        2. 厂家提货 (is_factory_pickup=True): dealer_id=批价单dealer_id, distributor_id=NULL
        3. 常规渠道: dealer_id=批价单dealer_id, distributor_id=批价单distributor_id
        """
        # 根据批价单的业务类型设置结算单的客户ID
        if pricing_order.is_direct_contract:
            # 厂商直签：dealer_id和distributor_id都为NULL
            dealer_id = None
            distributor_id = None
        elif pricing_order.is_factory_pickup:
            # 厂家提货：有dealer_id，distributor_id为NULL
            dealer_id = pricing_order.dealer_id
            distributor_id = None
        else:
            # 常规渠道：从批价单同步dealer_id和distributor_id
            dealer_id = pricing_order.dealer_id
            distributor_id = pricing_order.distributor_id

        # 创建结算单，同步业务类型标记
        settlement_order = SettlementOrder(
            pricing_order_id=pricing_order.id,
            project_id=pricing_order.project_id,
            quotation_id=pricing_order.quotation_id,
            distributor_id=distributor_id,
            dealer_id=dealer_id,
            is_direct_contract=pricing_order.is_direct_contract,  # 同步业务类型标记
            is_factory_pickup=pricing_order.is_factory_pickup,    # 同步业务类型标记
            created_by=current_user_id
        )

        db.session.add(settlement_order)
        db.session.flush()  # 获取ID

        return settlement_order

    @staticmethod
    def sync_business_type_to_settlements(pricing_order):
        """将批价单的业务类型同步到所有关联的结算单

        当批价单的业务类型字段被修改后调用此函数，确保结算单数据一致性。

        同步内容：
        1. is_direct_contract（厂商直签）
        2. is_factory_pickup（厂家提货）
        3. 根据业务类型规则同步客户ID（dealer_id 和 distributor_id）

        业务规则：
        - 厂商直签：dealer_id=NULL, distributor_id=NULL
        - 厂家提货：dealer_id=批价单dealer_id, distributor_id=NULL
        - 常规渠道：dealer_id=批价单dealer_id, distributor_id=批价单distributor_id
        """
        settlement_orders = SettlementOrder.query.filter_by(
            pricing_order_id=pricing_order.id
        ).all()

        for settlement_order in settlement_orders:
            # 同步业务类型标记
            settlement_order.is_direct_contract = pricing_order.is_direct_contract
            settlement_order.is_factory_pickup = pricing_order.is_factory_pickup

            # 根据业务类型更新客户ID
            if pricing_order.is_direct_contract:
                # 厂商直签：清空客户ID
                settlement_order.dealer_id = None
                settlement_order.distributor_id = None
            elif pricing_order.is_factory_pickup:
                # 厂家提货：有dealer_id，无distributor_id
                settlement_order.dealer_id = pricing_order.dealer_id
                settlement_order.distributor_id = None
            else:
                # 常规渠道：同步批价单的客户ID
                settlement_order.dealer_id = pricing_order.dealer_id
                settlement_order.distributor_id = pricing_order.distributor_id

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
                logger.error(f"🔍 [APPROVAL_SERVICE] ❌ 规范化厂商直签状态失败: {message}")
                return False, message
            
            # 应用厂商直签设置（在提交时自动填入当前用户的企业名称）
            
            applied, apply_message = PricingOrderService.apply_direct_contract_to_pricing_order(pricing_order, current_user)
            if not applied:
                logger.error(f"🔍 [APPROVAL_SERVICE] ❌ 应用厂商直签设置失败: {apply_message}")
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
    def approve_step(pricing_order_id, step_order, current_user_id, action, comment=None, frontend_amounts=None, frontend_data=None):
        """审批步骤
        
        Args:
            pricing_order_id: 批价单ID
            step_order: 审批步骤
            current_user_id: 当前用户ID
            action: 审批动作（approve/reject）
            comment: 审批意见
            frontend_amounts: 前端传递的金额数据，格式为 {'pricing_total': float, 'settlement_total': float}
            frontend_data: 前端传递的完整表单数据，格式为 {'basic_info': {}, 'pricing_details': [], 'settlement_details': []}
        """
        try:
            # 🔍 [调试] 添加详细的入口调试信息
            
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
                # 数据保存逻辑已移到批结算审批动作内部，这里不再需要处理frontend_data
                
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
        from app import current_app

        # 严格检查：只有在批价单状态为approved时才执行项目阶段更新
        if pricing_order.status != 'approved':
            current_app.logger.warning(f"批价单 {pricing_order.order_number} 状态为 {pricing_order.status}，不应调用complete_approval")
            return
        
        # 更新项目状态为签约
        project = pricing_order.project
        if project:
            old_stage = project.current_stage
            project.current_stage = 'signed'

            # 记录日志
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

        # 更新结算单状态为已批准（修复：使用独立结算单模型）
        from app.models.pricing_order import SettlementOrder
        settlement_order = SettlementOrder.query.filter_by(pricing_order_id=pricing_order.id).first()
        if settlement_order:
            settlement_order.status = 'approved'
            settlement_order.approved_by = pricing_order.approved_by
            settlement_order.approved_at = pricing_order.approved_at
            # 确保结算单总金额是最新的
            settlement_order.calculate_totals()
            current_app.logger.info(f"更新独立结算单 {settlement_order.order_number} 状态为已批准，总金额: {settlement_order.total_amount:,.2f}")
        else:
            current_app.logger.warning(f"批价单 {pricing_order.order_number} 没有对应的独立结算单")

        # 智能解锁相关对象（检查是否还有其他待审批批价单）
        PricingOrderService.unlock_related_objects(pricing_order)
    
    @staticmethod
    def unlock_related_objects(pricing_order):
        """智能解锁相关对象（仅当没有其他待审批批价单时才解锁）"""
        from app import current_app
        from app.models.pricing_order import PricingOrder

        # 智能解锁项目
        project = pricing_order.project
        if project:
            # 检查该项目下是否还有其他待审批的批价单
            pending_count = PricingOrder.query.filter_by(
                project_id=project.id,
                status='pending'
            ).count()

            if pending_count == 0:
                # 没有待审批的批价单，解锁项目
                project.is_locked = False
                project.locked_reason = None
                project.locked_by = None
                project.locked_at = None
                current_app.logger.info(f"项目 {project.project_name} 已解锁（无待审批批价单）")
            else:
                # 还有其他批价单在审批中，保持锁定
                current_app.logger.info(f"项目 {project.project_name} 保持锁定（还有 {pending_count} 个待审批批价单）")

        # 智能解锁报价单
        quotation = pricing_order.quotation
        if quotation:
            # 检查该报价单下是否还有其他待审批的批价单
            pending_count = PricingOrder.query.filter_by(
                quotation_id=quotation.id,
                status='pending'
            ).count()

            if pending_count == 0:
                # 没有待审批的批价单，解锁报价单
                quotation.is_locked = False
                quotation.lock_reason = None
                quotation.locked_by = None
                quotation.locked_at = None
                current_app.logger.info(f"报价单 {quotation.quotation_number} 已解锁（无待审批批价单）")
            else:
                # 还有其他批价单在审批中，保持锁定
                current_app.logger.info(f"报价单 {quotation.quotation_number} 保持锁定（还有 {pending_count} 个待审批批价单）")
    
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
            
            if not approval_instance:
                return False
                
            
            if approval_instance.status != ApprovalStatus.PENDING:
                return False
                
            
            # 检查当前步骤的审批人
            current_step = ApprovalStep.query.get(approval_instance.current_step)
            
            if current_step:
                
                # 如果有审批人ID，获取审批人用户名
                if current_step.approver_user_id:
                    from app.models.user import User
                    approver_user = User.query.get(current_step.approver_user_id)
                    approver_username = approver_user.username if approver_user else "未知用户"
                
                # 处理直接指定审批人的情况
                if current_step.approver_user_id and current_step.approver_user_id == current_user.id:
                    return True
                
                # 🔥 新增：处理分支决策类型的审批步骤
                if current_step.approver_type == 'branch':
                    try:
                        from app.helpers.approval_helpers import get_step_actual_approver
                        actual_approver = get_step_actual_approver(current_step, approval_instance)
                        
                        if actual_approver and actual_approver.id == current_user.id:
                            return True
                        else:
                            pass
                    except Exception as e:
                        logger.error(f"🔍 [APPROVER_CHECK] ❌ 分支决策审批人确定失败: {str(e)}")
                
                # 处理其他特殊审批人类型（如auto等）
                if current_step.approver_type in ['auto', 'next_level']:
                    try:
                        from app.helpers.approval_helpers import get_step_actual_approver
                        actual_approver = get_step_actual_approver(current_step, approval_instance)
                        
                        if actual_approver and actual_approver.id == current_user.id:
                            return True
                        else:
                            pass
                    except Exception as e:
                        logger.error(f"🔍 [APPROVER_CHECK] ❌ 特殊类型审批人确定失败: {str(e)}")
                
            else:
                pass
                
            return False
        except Exception as e:
            logger.error(f"🔍 [APPROVER_CHECK] ❌ 检查审批人时发生异常: {str(e)}")
            return False


    
    @staticmethod
    def can_edit_pricing_details(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑批价单明细 - V2统一审批系统
        
        审批状态下，检查审批人是否被授权编辑定价相关字段
        
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
            # 审批中：检查是否为当前审批人 + 是否有定价字段的编辑权限
            is_current_approver = PricingOrderService._is_current_approver_v2(pricing_order, current_user)
            
            if not is_current_approver:
                return False
            
            # 获取当前步骤的可编辑字段
            from app.helpers.approval_helpers import get_object_approval_instance
            from app.models.approval import ApprovalStep
            
            approval_instance = get_object_approval_instance('pricing_order', pricing_order.id)
            
            if not approval_instance:
                return False
                
            current_step = ApprovalStep.query.get(approval_instance.current_step)
            
            if not current_step:
                return False
                
            editable_fields = current_step.editable_fields or []
            
            # 检查是否有任何定价相关字段在可编辑列表中
            pricing_fields = ['product_name', 'unit_price', 'total_price', 'pricing_details']
            has_pricing_edit_permission = any(field in editable_fields for field in pricing_fields)
            
            return has_pricing_edit_permission
                
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
            # 审批中：检查是否为当前审批人 + 是否有结算字段的编辑权限
            is_current_approver = PricingOrderService._is_current_approver_v2(pricing_order, current_user)
            
            if not is_current_approver:
                return False
            
            # 获取当前步骤的可编辑字段
            from app.helpers.approval_helpers import get_object_approval_instance
            from app.models.approval import ApprovalStep
            
            approval_instance = get_object_approval_instance('pricing_order', pricing_order.id)
            
            if not approval_instance:
                return False
                
            current_step = ApprovalStep.query.get(approval_instance.current_step)
            
            if not current_step:
                return False
                
            editable_fields = current_step.editable_fields or []
            
            # 检查是否有任何结算相关字段在可编辑列表中
            settlement_fields = ['settlement_details', 'settlement_amount', 'settlement_rate', 'cost_price', 'settlement_total_discount_rate']
            has_settlement_edit_permission = any(field in editable_fields for field in settlement_fields)
            
            # 只有在有结算字段编辑权限时才进行其他权限检查
            if has_settlement_edit_permission:
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
            return project_type in ['sales_key', 'sales_focus', 'channel_follow']
        
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
    def can_edit_quantity(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑数量字段 - V2统一审批系统
        
        审批状态下，检查审批人是否被授权编辑数量相关字段
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑数量
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：检查是否为当前审批人 + 是否有数量字段的编辑权限
            is_current_approver = PricingOrderService._is_current_approver_v2(pricing_order, current_user)
            
            if not is_current_approver:
                return False
            
            # 获取当前步骤的可编辑字段
            from app.helpers.approval_helpers import get_object_approval_instance
            from app.models.approval import ApprovalStep
            
            approval_instance = get_object_approval_instance('pricing_order', pricing_order.id)
            
            if not approval_instance:
                return False
                
            current_step = ApprovalStep.query.get(approval_instance.current_step)
            
            if not current_step:
                return False
                
            editable_fields = current_step.editable_fields or []
            
            # 检查是否有任何数量相关字段在可编辑列表中
            quantity_fields = ['quantity', 'unit_quantity', 'total_quantity']
            has_quantity_edit_permission = any(field in editable_fields for field in quantity_fields)
            
            return has_quantity_edit_permission
                
        return False
    
    @staticmethod
    def can_edit_discount_and_price(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑折扣率和单价字段 - V2统一审批系统
        
        审批状态下，检查审批人是否被授权编辑折扣和价格相关字段
        """
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            return pricing_order.created_by == current_user.id
        elif pricing_order.status == 'pending':
            # 审批中：检查是否为当前审批人 + 是否有折扣价格字段的编辑权限
            is_current_approver = PricingOrderService._is_current_approver_v2(pricing_order, current_user)
            
            if not is_current_approver:
                return False
            
            # 获取当前步骤的可编辑字段
            from app.helpers.approval_helpers import get_object_approval_instance
            from app.models.approval import ApprovalStep
            
            approval_instance = get_object_approval_instance('pricing_order', pricing_order.id)
            
            if not approval_instance:
                return False
                
            current_step = ApprovalStep.query.get(approval_instance.current_step)
            
            if not current_step:
                return False
                
            editable_fields = current_step.editable_fields or []
            
            # 检查是否有任何折扣价格相关字段在可编辑列表中
            discount_price_fields = ['discount_rate', 'unit_price', 'discounted_price', 'total_discount_rate']
            has_discount_price_edit_permission = any(field in editable_fields for field in discount_price_fields)
            
            return has_discount_price_edit_permission
                
        return False
    @staticmethod
    def can_edit_basic_info(pricing_order, current_user, is_approval_context=False):
        """检查是否可以编辑基本信息（分销商、经销商等） - V2统一审批系统
        
        审批状态下，检查审批人是否被授权编辑基本信息字段
        """
        
        # 审批通过后不能编辑
        if pricing_order.status == 'approved':
            return False
            
        if pricing_order.status in ['draft', 'rejected']:
            # 草稿状态或被拒绝状态：创建人可编辑
            is_creator = pricing_order.created_by == current_user.id
            return is_creator
        elif pricing_order.status == 'pending':
            # 审批中：检查是否为当前审批人 + 是否有基本信息字段的编辑权限
            is_current_approver = PricingOrderService._is_current_approver_v2(pricing_order, current_user)
            
            if not is_current_approver:
                return False
            
            # 获取当前步骤的可编辑字段
            from app.helpers.approval_helpers import get_object_approval_instance
            from app.models.approval import ApprovalStep
            
            approval_instance = get_object_approval_instance('pricing_order', pricing_order.id)
            
            if not approval_instance:
                return False
                
            current_step = ApprovalStep.query.get(approval_instance.current_step)
            
            if not current_step:
                return False
                
            editable_fields = current_step.editable_fields or []
            
            # 检查是否有任何基本信息字段在可编辑列表中
            basic_info_fields = ['dealer_id', 'distributor_id', 'is_direct_contract', 'is_factory_pickup']
            has_basic_edit_permission = any(field in editable_fields for field in basic_info_fields)
            
            if has_basic_edit_permission:
                # 记录具体哪些基本信息字段可以编辑
                editable_basic_fields = [field for field in basic_info_fields if field in editable_fields]
            else:
                pass
            
            return has_basic_edit_permission
        
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
    def save_pricing_order_core_data(pricing_order_id, request_data, current_user):
        """
        审批专用的数据保存函数
        
        直接保存前端传递的完整数据，确保折扣率修改后的级联计算结果被正确保存
        """
        try:
            from flask import current_app
            
            pricing_order = PricingOrder.query.get_or_404(pricing_order_id)
            
            processed_fields = []
            
            # === 直接保存所有前端传递的数据 ===
            
            # 处理基本信息字段
            if 'basic_info' in request_data:
                basic_info = request_data['basic_info']
                
                # 经销商和分销商
                if 'dealer_id' in basic_info:
                    pricing_order.dealer_id = basic_info['dealer_id']
                    processed_fields.append('dealer_id')
                
                if 'distributor_id' in basic_info:
                    pricing_order.distributor_id = basic_info['distributor_id']
                    processed_fields.append('distributor_id')
                
                # 布尔字段
                if 'is_direct_contract' in basic_info:
                    pricing_order.is_direct_contract = basic_info['is_direct_contract'] == True
                    processed_fields.append('is_direct_contract')
                
                if 'is_factory_pickup' in basic_info:
                    pricing_order.is_factory_pickup = basic_info['is_factory_pickup'] == True
                    processed_fields.append('is_factory_pickup')
                
                # 批价单总折扣率
                if 'pricing_total_discount_rate' in basic_info and basic_info['pricing_total_discount_rate'] is not None:
                    old_value = pricing_order.pricing_total_discount_rate
                    pricing_order.pricing_total_discount_rate = Decimal(str(basic_info['pricing_total_discount_rate']))
                    processed_fields.append('pricing_total_discount_rate')
                    current_app.logger.info(f"✅ 更新批价单总折扣率: {old_value} -> {basic_info['pricing_total_discount_rate']}")
                
                # 结算单总折扣率
                if 'settlement_total_discount_rate' in basic_info and basic_info['settlement_total_discount_rate'] is not None:
                    old_value = pricing_order.settlement_total_discount_rate
                    pricing_order.settlement_total_discount_rate = Decimal(str(basic_info['settlement_total_discount_rate']))
                    processed_fields.append('settlement_total_discount_rate')
                    current_app.logger.info(f"✅ 更新结算单总折扣率: {old_value} -> {basic_info['settlement_total_discount_rate']}")
            
            # 使用 no_autoflush 块避免在删除和创建过程中触发自动刷新
            with db.session.no_autoflush:
                # 步骤1: 删除现有明细（先删子表，再删父表）
                if 'settlement_details' in request_data or 'pricing_details' in request_data:
                    from app.models.pricing_order import SettlementOrderDetail

                    # 删除结算单明细（子表）
                    SettlementOrderDetail.query.filter_by(pricing_order_id=pricing_order_id).delete()
                    current_app.logger.info("✅ 已删除现有结算单明细")

                    # 删除批价单明细（父表）
                    PricingOrderDetail.query.filter_by(pricing_order_id=pricing_order_id).delete()
                    current_app.logger.info("✅ 已删除现有批价单明细")

            # 步骤2: 先创建批价单明细（父表）
            pricing_details_map = {}  # 存储产品型号到批价单明细ID的映射
            if 'pricing_details' in request_data:
                details_data = request_data['pricing_details']
                current_app.logger.info(f"收到批价单明细数据: {len(details_data)} 条")

                # 重新创建明细并计算总金额
                pricing_total_amount = Decimal('0')
                for index, detail_data in enumerate(details_data):
                    # 从前端数据获取字段值
                    market_price = Decimal(str(detail_data.get('market_price', 0)))
                    unit_price = Decimal(str(detail_data.get('unit_price', 0)))
                    quantity = int(detail_data.get('quantity', 1))
                    discount_rate = Decimal(str(detail_data.get('discount_rate', 100))) / 100  # 转换为小数

                    # 计算小计
                    total_price = unit_price * quantity
                    pricing_total_amount += total_price

                    # 创建明细记录
                    detail = PricingOrderDetail(
                        pricing_order_id=pricing_order_id,
                        product_name=detail_data.get('product_name', ''),
                        product_model=detail_data.get('product_model', ''),
                        product_desc=detail_data.get('product_desc', ''),
                        brand=detail_data.get('brand', ''),
                        unit=detail_data.get('unit', '台'),
                        product_mn=detail_data.get('product_mn', ''),
                        market_price=market_price,
                        unit_price=unit_price,
                        quantity=quantity,
                        discount_rate=discount_rate,
                        total_price=total_price
                    )
                    db.session.add(detail)
                    db.session.flush()  # 立即刷新以获取ID

                    # 使用产品型号作为key建立映射（用于结算单明细关联）
                    product_key = f"{detail_data.get('product_model', '')}_{detail_data.get('product_mn', '')}"
                    pricing_details_map[product_key] = detail.id

                # 更新批价单总金额
                pricing_order.pricing_total_amount = pricing_total_amount
                processed_fields.append('pricing_details')
                current_app.logger.info(f"✅ 更新批价单明细和总金额: {pricing_total_amount}")

            # 步骤3: 后创建结算单明细（子表，关联批价单明细ID）
            if 'settlement_details' in request_data:
                from app.models.pricing_order import SettlementOrderDetail

                details_data = request_data['settlement_details']
                current_app.logger.info(f"收到结算单明细数据: {len(details_data)} 条")

                # 重新创建明细并计算总金额
                settlement_total_amount = Decimal('0')
                for index, detail_data in enumerate(details_data):
                    # 从前端数据获取字段值
                    market_price = Decimal(str(detail_data.get('market_price', 0)))
                    unit_price = Decimal(str(detail_data.get('unit_price', 0)))
                    quantity = int(detail_data.get('quantity', 1))
                    discount_rate = Decimal(str(detail_data.get('discount_rate', 100))) / 100  # 转换为小数

                    # 计算小计
                    total_price = unit_price * quantity
                    settlement_total_amount += total_price

                    # 查找对应的批价单明细ID
                    product_key = f"{detail_data.get('product_model', '')}_{detail_data.get('product_mn', '')}"
                    pricing_detail_id = pricing_details_map.get(product_key)

                    # 获取关联的结算单
                    settlement_order = pricing_order.settlement_orders[0] if pricing_order.settlement_orders else None

                    # 创建明细记录
                    detail = SettlementOrderDetail(
                        pricing_order_id=pricing_order_id,
                        settlement_order_id=settlement_order.id if settlement_order else None,
                        pricing_detail_id=pricing_detail_id,  # 设置关联的批价单明细ID
                        product_name=detail_data.get('product_name', ''),
                        product_model=detail_data.get('product_model', ''),
                        product_desc=detail_data.get('product_desc', ''),
                        brand=detail_data.get('brand', ''),
                        unit=detail_data.get('unit', '台'),
                        product_mn=detail_data.get('product_mn', ''),
                        market_price=market_price,
                        unit_price=unit_price,
                        quantity=quantity,
                        discount_rate=discount_rate,
                        total_price=total_price
                    )
                    db.session.add(detail)

                # 更新结算单总金额
                pricing_order.settlement_total_amount = settlement_total_amount
                processed_fields.append('settlement_details')
                current_app.logger.info(f"✅ 更新结算单明细和总金额: {settlement_total_amount}")
            
            # 提交数据库变更
            db.session.commit()
            
            # 验证保存结果
            pricing_order_after = PricingOrder.query.get(pricing_order_id)
            
            current_app.logger.info(f"审批保存成功 - 批价单 {pricing_order_id}, 处理字段: {processed_fields}")
            return True, f"数据保存成功，处理字段: {', '.join(processed_fields)}"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"审批保存失败 - 批价单 {pricing_order_id}: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return False, f"保存失败: {str(e)}"