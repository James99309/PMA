from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app import db
from app.models.pricing_order import PricingOrder, PricingOrderDetail, SettlementOrder, SettlementOrderDetail, PricingOrderApprovalRecord
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.customer import Company
from app.services.pricing_order_service import PricingOrderService
from app.services.pdf_generator import PDFGenerator
from app.services.discount_permission_service import DiscountPermissionService
from app.permissions import check_permission
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

pricing_order_bp = Blueprint('pricing_order', __name__)


def check_pricing_edit_permission(pricing_order, current_user):
    """
    检查批价单编辑权限，支持审批上下文
    
    Returns:
        tuple: (can_edit_pricing, can_edit_settlement, is_approval_context)
    """
    # 检查是否在审批上下文中
    is_approval_context = False
    current_approval_record = None
    
    if pricing_order.status == 'pending':
        current_approval_record = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=pricing_order.id,
            step_order=pricing_order.current_approval_step,
            approver_id=current_user.id
        ).first()
        
        if current_approval_record:
            is_approval_context = True
    
    # 根据上下文选择权限检查方式
    can_edit_pricing = PricingOrderService.can_edit_pricing_details(
        pricing_order, current_user, is_approval_context=is_approval_context
    )
    can_edit_settlement = PricingOrderService.can_edit_settlement_details(
        pricing_order, current_user, is_approval_context=is_approval_context
    )
    
    return can_edit_pricing, can_edit_settlement, is_approval_context


@pricing_order_bp.route('/project/<int:project_id>/start_pricing_process', methods=['POST'])
@login_required
def start_pricing_process(project_id):
    """启动批价流程（从项目页面的签约按钮触发）"""
    try:
        project = Project.query.get_or_404(project_id)
        
        # 检查项目是否在批价或签约阶段
        if project.current_stage not in ['quoted', 'signed']:
            return jsonify({
                'success': False,
                'message': '项目必须在批价或签约阶段才能发起批价流程'
            })
        
        # 获取项目的最新报价单
        quotation = Quotation.query.filter_by(project_id=project_id).order_by(
            Quotation.created_at.desc()
        ).first()
        
        if not quotation:
            return jsonify({
                'success': False,
                'message': '项目没有关联的报价单，无法发起批价流程'
            })
        
        # 检查报价单是否有审核标记
        has_approval = (
            # 传统审核流程：有审核状态且不是pending/rejected，且有已审核阶段
            (quotation.approval_status and 
             quotation.approval_status != 'pending' and
             quotation.approval_status != 'rejected' and
             quotation.approved_stages) or
            # 或者有确认徽章（产品明细已确认）
            (quotation.confirmation_badge_status == 'confirmed')
        )
        
        if not has_approval:
            return jsonify({
                'success': False,
                'message': f'报价单 {quotation.quotation_number} 尚未完成审核，无法发起批价流程。请先完成报价单审批。'
            })
        
        # 检查是否已存在批价单
        existing_pricing_order = PricingOrder.query.filter_by(
            project_id=project_id,
            quotation_id=quotation.id
        ).first()
        
        if existing_pricing_order:
            return jsonify({
                'success': True,
                'redirect_url': url_for('pricing_order.edit_pricing_order', order_id=existing_pricing_order.id)
            })
        
        # 创建新的批价单
        pricing_order, error = PricingOrderService.create_pricing_order(
            project_id=project_id,
            quotation_id=quotation.id,
            current_user_id=current_user.id
        )
        
        if error:
            return jsonify({
                'success': False,
                'message': error
            })
        
        return jsonify({
            'success': True,
            'redirect_url': url_for('pricing_order.edit_pricing_order', order_id=pricing_order.id)
        })
        
    except Exception as e:
        logger.error(f"启动批价流程失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'系统错误: {str(e)}'
        })


@pricing_order_bp.route('/<int:order_id>')
@login_required
def edit_pricing_order(order_id):
    """批价单编辑页面"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 权限检查 - 使用统一的权限管理
        if not PricingOrderService.can_view_pricing_order(pricing_order, current_user):
            flash('您没有权限查看该批价单', 'danger')
            return redirect(url_for('project.list_projects'))
        
        # 检查编辑权限 - 使用统一的权限检查函数
        can_edit_pricing, can_edit_settlement, is_approval_context = check_pricing_edit_permission(pricing_order, current_user)
        can_view_settlement = PricingOrderService.can_view_settlement_tab(current_user)
        
        # 获取客户数据（分销商和经销商）- 应用数据所有权过滤
        from app.utils.access_control import get_viewable_data
        
        # 获取用户有权限查看的经销商类型公司（分销商下拉框也显示经销商类型的公司）
        dealers = get_viewable_data(Company, current_user, [Company.company_type.in_(['经销商', 'dealer'])]).all()
        
        # 分销商下拉框显示的也是经销商类型的公司（因为系统中没有单独的分销商类型）
        distributors = dealers
        
        # 获取项目关联的经销商客户
        project_dealers = []
        if pricing_order.project:
            # 根据项目中的经销商字段查找对应的公司
            if pricing_order.project.dealer:
                dealer_company = get_viewable_data(Company, current_user, [
                    Company.company_name == pricing_order.project.dealer,
                    Company.company_type.in_(['经销商', 'dealer'])
                ]).first()
                if dealer_company:
                    project_dealers.append(dealer_company)
            
            # 添加其他有权限查看的经销商
            for dealer in dealers:
                if dealer not in project_dealers:
                    project_dealers.append(dealer)
        
        # 获取当前用户的审批记录
        current_approval_record = None
        if pricing_order.status == 'pending':
            current_approval_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order.id,
                step_order=pricing_order.current_approval_step,
                approver_id=current_user.id
            ).first()
        
        # 获取用户的折扣权限
        discount_limits = DiscountPermissionService.get_user_discount_limits(current_user)
        
        # 获取审批步骤的折扣权限状态
        from app.helpers.approval_helpers import get_approval_step_discount_status
        step_discount_statuses = get_approval_step_discount_status(pricing_order)
        
        return render_template('pricing_order/edit_pricing_order.html',
                             pricing_order=pricing_order,
                             can_edit_pricing=can_edit_pricing,
                             can_edit_settlement=can_edit_settlement,
                             can_view_settlement=can_view_settlement,
                             distributors=distributors,
                             dealers=dealers,
                             project_dealers=project_dealers,
                             current_approval_record=current_approval_record,
                             discount_limits=discount_limits,
                             step_discount_statuses=step_discount_statuses)
        
    except Exception as e:
        logger.error(f"访问批价单编辑页面失败: {str(e)}")
        flash(f'访问失败: {str(e)}', 'danger')
        return redirect(url_for('project.list_projects'))


@pricing_order_bp.route('/<int:order_id>/update_basic_info', methods=['POST'])
@login_required
def update_basic_info(order_id):
    """更新批价单基本信息"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        logger.info(f"开始更新批价单{order_id}基本信息，当前用户: {current_user.id}, 创建者: {pricing_order.created_by}, 状态: {pricing_order.status}")
        
        # 权限检查 - 使用统一的权限检查函数
        can_edit_pricing, _, _ = check_pricing_edit_permission(pricing_order, current_user)
        logger.info(f"权限检查结果: {can_edit_pricing}")
        
        if not can_edit_pricing:
            logger.warning(f"用户{current_user.id}没有权限编辑批价单{order_id}")
            return jsonify({
                'success': False,
                'message': '您没有权限编辑该批价单'
            }), 403
        
        data = request.get_json()
        logger.info(f"更新基本信息请求数据: {data}")
        
        if not data:
            logger.warning("请求数据为空")
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        # 处理厂商直签和厂家提货字段
        is_direct_contract = data.get('is_direct_contract', False)
        is_factory_pickup = data.get('is_factory_pickup', False)
        
        pricing_order.is_direct_contract = is_direct_contract
        pricing_order.is_factory_pickup = is_factory_pickup
        logger.info(f"设置厂商直签: {is_direct_contract}, 厂家提货: {is_factory_pickup}")
        
        # 根据厂商直签状态处理经销商和分销商
        if is_direct_contract:
            # 厂商直签时，清空经销商和分销商
            pricing_order.dealer_id = None
            pricing_order.distributor_id = None
            logger.info("厂商直签开启，清空经销商和分销商")
        else:
            # 非厂商直签时，正常处理经销商和分销商
            if 'dealer_id' in data:
                dealer_id = data['dealer_id']
                logger.info(f"处理经销商ID: {dealer_id}, 类型: {type(dealer_id)}")
                if dealer_id and str(dealer_id).strip():
                    try:
                        dealer_id = int(dealer_id)
                        pricing_order.dealer_id = dealer_id
                        logger.info(f"设置经销商ID为: {dealer_id}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"无效的经销商ID: {dealer_id}, 错误: {e}")
                        pricing_order.dealer_id = None
                else:
                    pricing_order.dealer_id = None
                    logger.info("清空经销商ID")
            
            # 处理分销商：如果厂家提货开启，清空分销商
            if is_factory_pickup:
                pricing_order.distributor_id = None
                logger.info("厂家提货开启，清空分销商")
            elif 'distributor_id' in data:
                distributor_id = data['distributor_id']
                logger.info(f"处理分销商ID: {distributor_id}, 类型: {type(distributor_id)}")
                if distributor_id and str(distributor_id).strip():
                    try:
                        distributor_id = int(distributor_id)
                        pricing_order.distributor_id = distributor_id
                        logger.info(f"设置分销商ID为: {distributor_id}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"无效的分销商ID: {distributor_id}, 错误: {e}")
                        pricing_order.distributor_id = None
                else:
                    pricing_order.distributor_id = None
                    logger.info("清空分销商ID")
        
        db.session.commit()
        logger.info(f"成功更新批价单 {order_id} 基本信息")
        
        return jsonify({
            'success': True,
            'message': '基本信息更新成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新基本信息失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@pricing_order_bp.route('/<int:order_id>/update_pricing_detail', methods=['POST'])
@login_required
def update_pricing_detail(order_id):
    """更新批价单明细"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 权限检查 - 使用统一的权限检查函数
        can_edit_pricing, _, _ = check_pricing_edit_permission(pricing_order, current_user)
        if not can_edit_pricing:
            return jsonify({
                'success': False,
                'message': '您没有权限编辑批价单明细'
            })
        
        data = request.get_json()
        detail_id = data.get('detail_id')
        quantity = data.get('quantity')
        discount_rate = data.get('discount_rate')
        unit_price = data.get('unit_price')  # 新增单价更新
        
        success, error = PricingOrderService.update_pricing_detail(
            order_id, detail_id, quantity=quantity, discount_rate=discount_rate, unit_price=unit_price
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': error
            })
        
        # 重新获取更新后的数据
        pricing_order = PricingOrder.query.get(order_id)
        
        # 获取更新后的明细数据
        updated_detail = PricingOrderDetail.query.get(detail_id)
        
        return jsonify({
            'success': True,
            'message': '明细更新成功',
            'pricing_total_amount': pricing_order.formatted_pricing_total_amount,
            'pricing_discount_percentage': pricing_order.pricing_discount_percentage,
            'settlement_total_amount': pricing_order.formatted_settlement_total_amount,
            'settlement_discount_percentage': pricing_order.settlement_discount_percentage,
            'updated_detail': {
                'id': updated_detail.id,
                'discount_rate': updated_detail.discount_rate,
                'unit_price': updated_detail.unit_price,
                'total_price': updated_detail.total_price
            } if updated_detail else None
        })
        
    except Exception as e:
        logger.error(f"更新批价单明细失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        })


@pricing_order_bp.route('/<int:order_id>/update_total_discount', methods=['POST'])
@login_required
def update_total_discount_rate(order_id):
    """更新批价单或结算单的总折扣率"""
    try:
        data = request.get_json()
        tab_type = data.get('tab_type', 'pricing')  # pricing 或 settlement
        total_discount_rate = data.get('total_discount_rate')
        
        if total_discount_rate is None:
            return jsonify({'success': False, 'message': '缺少折扣率参数'})
        
        # 转换为小数形式
        discount_rate_decimal = float(total_discount_rate) / 100
        
        # 获取批价单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PricingOrder, current_user)
        pricing_order = viewable_orders.filter(PricingOrder.id == order_id).first_or_404()
        
        # 检查编辑权限 - 使用统一的权限检查函数
        can_edit_pricing, _, _ = check_pricing_edit_permission(pricing_order, current_user)
        if not can_edit_pricing:
            return jsonify({'success': False, 'message': '无权限编辑此批价单'})
        
        # 根据tab类型获取相应的明细列表
        if tab_type == 'pricing':
            details = pricing_order.pricing_details
        else:  # settlement
            details = pricing_order.settlement_details
        
        # 更新所有明细的折扣率和价格，但保持总折扣率逻辑
        for detail in details:
            if detail.market_price and detail.market_price > 0:
                # 使用总折扣率更新明细的折扣率
                detail.discount_rate = discount_rate_decimal
                # 重新计算单价和总价
                detail.unit_price = detail.market_price * discount_rate_decimal
                detail.total_price = detail.unit_price * detail.quantity
        
        # 标记批价单已修改
        pricing_order.updated_at = datetime.utcnow()
        
        # 保存到数据库
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'总折扣率已更新为 {total_discount_rate}%',
            'total_discount_rate': total_discount_rate
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"更新总折扣率失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})


@pricing_order_bp.route('/<int:order_id>/submit', methods=['POST'])
@login_required
def submit_pricing_order(order_id):
    """提交批价单审批"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 权限检查
        if pricing_order.created_by != current_user.id and current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': '您没有权限提交该批价单'
            })
        
        success, error = PricingOrderService.submit_for_approval(order_id, current_user.id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': error
            })
        
        return jsonify({
            'success': True,
            'message': '批价单已提交审批'
        })
        
    except Exception as e:
        logger.error(f"提交批价单失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        })


@pricing_order_bp.route('/<int:order_id>/approve', methods=['POST'])
@login_required
def approve_pricing_order(order_id):
    """审批批价单"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        data = request.get_json()
        action = data.get('action')  # 'approve' 或 'reject'
        comment = data.get('comment', '')
        
        # 新增：接收前端可能传递的明细数据
        pricing_details = data.get('pricing_details', [])
        settlement_details = data.get('settlement_details', [])
        basic_info = data.get('basic_info', {})
        
        if action not in ['approve', 'reject']:
            return jsonify({
                'success': False,
                'message': '无效的审批动作'
            })
        
        # 🔥 关键修复：只有在通过审批时才保存前端数据，拒绝时不保存
        if action == 'approve' and (pricing_details or settlement_details or basic_info):
            logger.info(f"审批通过，保存前端修改的数据: 批价单明细{len(pricing_details)}条, 结算单明细{len(settlement_details)}条")
            
            # 使用统一的审批数据保存方法
            success, error_message = PricingOrderService.save_approval_data(
                pricing_order, pricing_details, settlement_details, basic_info, current_user, logger
            )
            
            if not success:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': error_message
                })
            
            # 提交保存的数据
            db.session.commit()
            logger.info(f"审批通过，数据保存成功: {pricing_order.order_number}")
        elif action == 'reject':
            logger.info(f"审批拒绝，不保存前端修改的数据: {pricing_order.order_number}")
        
        # 获取当前审批步骤
        current_step = pricing_order.current_approval_step
        
        success, error = PricingOrderService.approve_step(
            order_id, current_step, current_user.id, action, comment
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': error
            })
        
        action_text = '通过' if action == 'approve' else '拒绝'
        return jsonify({
            'success': True,
            'message': f'审批{action_text}成功'
        })
        
    except Exception as e:
        logger.error(f"审批批价单失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'审批失败: {str(e)}'
        })


@pricing_order_bp.route('/<int:order_id>/approval_flow')
@login_required
def get_approval_flow(order_id):
    """获取审批流程信息"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 权限检查 - 使用统一的权限管理
        if not PricingOrderService.can_view_pricing_order(pricing_order, current_user):
            return jsonify({
                'success': False,
                'message': '您没有权限查看该批价单'
            })
        
        # 构建审批流程信息
        flow_data = []
        for record in pricing_order.approval_records:
            flow_data.append({
                'step_order': record.step_order,
                'step_name': record.step_name,
                'approver_role': record.approver_role,
                'approver_name': record.approver.real_name or record.approver.username if record.approver else '未指定',
                'action': record.action,
                'comment': record.comment,
                'approved_at': record.approved_at.strftime('%Y-%m-%d %H:%M:%S') if record.approved_at else None,
                'is_current': record.step_order == pricing_order.current_approval_step,
                'is_fast_approval': record.is_fast_approval,
                'fast_approval_reason': record.fast_approval_reason
            })
        
        return jsonify({
            'success': True,
            'data': {
                'order_number': pricing_order.order_number,
                'status': pricing_order.status,
                'current_step': pricing_order.current_approval_step,
                'flow_data': flow_data
            }
        })
        
    except Exception as e:
        logger.error(f"获取审批流程失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        })


@pricing_order_bp.route('/list')
@login_required
def list_pricing_orders():
    """批价单列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 构建查询
    query = PricingOrder.query
    
    # 权限过滤：根据新的权限规则过滤批价单
    user_role = current_user.role.strip() if current_user.role else ''
    
    # 使用统一的管理员权限检查
    from app.permissions import is_admin_or_ceo
    if not is_admin_or_ceo():
        # 根据角色和项目类型进行过滤
        if user_role == 'sales_director':
            # 营销总监：可以看到所有的销售重点和渠道跟进的业务的批价单
            query = query.join(Project).filter(
                db.or_(
                    Project.project_type.in_(['销售重点', 'sales_key', '渠道跟进', 'channel_follow']),
                    PricingOrder.created_by == current_user.id,
                    PricingOrder.approval_records.any(
                        PricingOrderApprovalRecord.approver_id == current_user.id
                    )
                )
            )
        elif user_role == 'channel_manager':
            # 渠道经理：只能看到有经销商的渠道跟进和销售机会的批价单，不能看到销售重点
            # 即使是审批人，也不能查看销售重点项目的批价单
            query = query.join(Project).filter(
                db.or_(
                    db.and_(
                        Project.project_type.in_(['渠道跟进', 'channel_follow', '销售机会', 'sales_opportunity']),
                        PricingOrder.dealer_id.isnot(None)
                    ),
                    PricingOrder.created_by == current_user.id,
                    # 作为审批人但只能查看非销售重点项目的批价单
                    db.and_(
                        PricingOrder.approval_records.any(
                            PricingOrderApprovalRecord.approver_id == current_user.id
                        ),
                        Project.project_type.notin_(['销售重点', 'sales_focus'])
                    )
                )
            )
        elif user_role == 'service_manager':
            # 服务经理：可以看到所有销售机会的批价单
            query = query.join(Project).filter(
                db.or_(
                    Project.project_type.in_(['销售机会', 'sales_opportunity']),
                    PricingOrder.created_by == current_user.id,
                    PricingOrder.approval_records.any(
                        PricingOrderApprovalRecord.approver_id == current_user.id
                    )
                )
            )
        elif user_role == 'business_admin':
            # 商务助理：可以看到所有的销售重点，渠道跟进的业务的批价单
            query = query.join(Project).filter(
                db.or_(
                    Project.project_type.in_(['销售重点', 'sales_key', '渠道跟进', 'channel_follow']),
                    PricingOrder.created_by == current_user.id,
                    PricingOrder.approval_records.any(
                        PricingOrderApprovalRecord.approver_id == current_user.id
                    )
                )
            )
        elif user_role == 'finance_director':
            # 财务总监：可以看到所有的销售重点，渠道跟进和销售机会的业务的批价单
            query = query.join(Project).filter(
                db.or_(
                    Project.project_type.in_(['销售重点', 'sales_key', '渠道跟进', 'channel_follow', '销售机会', 'sales_opportunity']),
                    PricingOrder.created_by == current_user.id,
                    PricingOrder.approval_records.any(
                        PricingOrderApprovalRecord.approver_id == current_user.id
                    )
                )
            )
        else:
            # 其他用户：只能查看自己创建的或参与审批的批价单
            query = query.filter(
                db.or_(
                    PricingOrder.created_by == current_user.id,
                    PricingOrder.approval_records.any(
                        PricingOrderApprovalRecord.approver_id == current_user.id
                    )
                )
            )
    
    # 分页
    pagination = query.order_by(PricingOrder.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    pricing_orders = pagination.items
    
    return render_template('pricing_order/list_pricing_orders.html',
                         pricing_orders=pricing_orders,
                         pagination=pagination)


@pricing_order_bp.route('/<int:order_id>/add_product', methods=['POST'])
@login_required
def add_product_to_pricing(order_id):
    """添加产品到批价单"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 权限检查 - 使用统一的权限检查函数
        can_edit_pricing, _, _ = check_pricing_edit_permission(pricing_order, current_user)
        if not can_edit_pricing:
            return jsonify({
                'success': False,
                'message': '您没有权限编辑批价单明细'
            })
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['product_name', 'market_price', 'quantity']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'字段 {field} 不能为空'
                })
        
        # 创建批价单明细
        pricing_detail = PricingOrderDetail(
            pricing_order_id=order_id,
            product_name=data['product_name'],
            product_model=data.get('product_model', ''),
            product_desc=data.get('product_desc', ''),
            brand=data.get('brand', ''),
            unit=data.get('unit', '台'),
            market_price=float(data['market_price']),
            quantity=int(data['quantity']),
            discount_rate=float(data.get('discount_rate', 0.8)),
            source_type='manual'
        )
        
        # 计算价格
        pricing_detail.calculate_prices()
        
        db.session.add(pricing_detail)
        db.session.flush()
        
        # 同时创建结算单明细
        settlement_detail = SettlementOrderDetail(
            pricing_order_id=order_id,
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
        
        # 重新计算总额和总折扣率（基于明细数据）
        pricing_order.calculate_pricing_totals(recalculate_discount_rate=True)
        pricing_order.calculate_settlement_totals(recalculate_discount_rate=True)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '产品添加成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'添加失败: {str(e)}'
        })


@pricing_order_bp.route('/<int:order_id>/delete_product/<int:detail_id>', methods=['DELETE'])
@login_required
def delete_product_from_pricing(order_id, detail_id):
    """从批价单删除产品"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 权限检查 - 使用统一的权限检查函数
        can_edit_pricing, _, _ = check_pricing_edit_permission(pricing_order, current_user)
        if not can_edit_pricing:
            return jsonify({
                'success': False,
                'message': '您没有权限编辑批价单明细'
            })
        
        pricing_detail = PricingOrderDetail.query.filter_by(
            pricing_order_id=order_id, id=detail_id
        ).first()
        
        if not pricing_detail:
            return jsonify({
                'success': False,
                'message': '产品明细不存在'
            })
        
        # 检查是否可删除（和源通信品牌的产品不可删除）
        if not pricing_detail.is_deletable:
            return jsonify({
                'success': False,
                'message': '和源通信品牌的产品不可删除'
            })
        
        # 删除对应的结算单明细
        settlement_detail = SettlementOrderDetail.query.filter_by(
            pricing_detail_id=detail_id
        ).first()
        if settlement_detail:
            db.session.delete(settlement_detail)
        
        # 删除批价单明细
        db.session.delete(pricing_detail)
        
        # 重新计算总额和总折扣率（基于明细数据）
        pricing_order.calculate_pricing_totals(recalculate_discount_rate=True)
        pricing_order.calculate_settlement_totals(recalculate_discount_rate=True)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '产品删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除产品失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        })


@pricing_order_bp.route('/<int:order_id>/save_pricing_details', methods=['POST'])
@login_required
def save_pricing_details(order_id):
    """保存批价单明细（批量保存）"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 记录当前项目阶段状态用于调试
        project_stage_before = pricing_order.project.current_stage if pricing_order.project else None
        logger.info(f"保存批价单 {pricing_order.order_number} 明细前，项目阶段: {project_stage_before}")
        
        # 权限检查 - 使用统一的权限检查函数
        can_edit_pricing, _, _ = check_pricing_edit_permission(pricing_order, current_user)
        if not can_edit_pricing:
            return jsonify({
                'success': False,
                'message': '您没有权限编辑批价单明细'
            })
        
        data = request.get_json()
        details_data = data.get('details', [])
        
        if not details_data:
            return jsonify({
                'success': False,
                'message': '请添加至少一个产品明细'
            })
        
        # 删除现有明细
        existing_details = PricingOrderDetail.query.filter_by(pricing_order_id=order_id).all()
        for detail in existing_details:
            # 同时删除对应的结算单明细
            settlement_detail = SettlementOrderDetail.query.filter_by(
                pricing_detail_id=detail.id
            ).first()
            if settlement_detail:
                db.session.delete(settlement_detail)
            db.session.delete(detail)
        
        # 创建新明细
        for detail_data in details_data:
            # 验证必填字段
            if not detail_data.get('product_name'):
                continue
            
            # 创建批价单明细
            pricing_detail = PricingOrderDetail(
                pricing_order_id=order_id,
                product_name=detail_data['product_name'],
                product_model=detail_data.get('product_model', ''),
                product_desc=detail_data.get('product_desc', ''),
                brand=detail_data.get('brand', ''),
                unit=detail_data.get('unit', '台'),
                product_mn=detail_data.get('product_mn', ''),
                market_price=float(detail_data.get('market_price', 0)),
                quantity=int(detail_data.get('quantity', 1)),
                discount_rate=float(detail_data.get('discount_rate', 100)) / 100,
                source_type='manual'
            )
            
            # 计算价格
            pricing_detail.calculate_prices()
            db.session.add(pricing_detail)
            db.session.flush()  # 获取ID
            
            # 同时创建结算单明细
            settlement_detail = SettlementOrderDetail(
                pricing_order_id=order_id,
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
        
        # 重新计算总额和总折扣率（基于明细数据）
        pricing_order.calculate_pricing_totals(recalculate_discount_rate=True)
        pricing_order.calculate_settlement_totals(recalculate_discount_rate=True)
        
        db.session.commit()
        
        # 检查项目阶段是否被意外修改
        project_stage_after = pricing_order.project.current_stage if pricing_order.project else None
        if project_stage_before != project_stage_after:
            logger.warning(f"警告：保存批价单 {pricing_order.order_number} 明细时，项目阶段发生了意外变化: {project_stage_before} -> {project_stage_after}")
        else:
            logger.info(f"保存批价单 {pricing_order.order_number} 明细后，项目阶段保持不变: {project_stage_after}")
        
        return jsonify({
            'success': True,
            'message': '批价单明细保存成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存批价单明细失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        })


@pricing_order_bp.route('/<int:order_id>/save_settlement_details', methods=['POST'])
@login_required
def save_settlement_details(order_id):
    """保存结算单明细（批量保存）"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 记录当前项目阶段状态用于调试
        project_stage_before = pricing_order.project.current_stage if pricing_order.project else None
        logger.info(f"保存结算单 {pricing_order.order_number} 明细前，项目阶段: {project_stage_before}")
        
        # 权限检查 - 使用统一的权限检查函数
        _, can_edit_settlement, _ = check_pricing_edit_permission(pricing_order, current_user)
        if not can_edit_settlement:
            return jsonify({
                'success': False,
                'message': '您没有权限编辑结算单明细'
            })
        
        data = request.get_json()
        details_data = data.get('details', [])
        
        if not details_data:
            return jsonify({
                'success': False,
                'message': '请添加至少一个产品明细'
            })
        
        # 删除现有明细
        existing_details = SettlementOrderDetail.query.filter_by(pricing_order_id=order_id).all()
        for detail in existing_details:
            db.session.delete(detail)
        
        # 创建新明细
        for detail_data in details_data:
            # 验证必填字段
            if not detail_data.get('product_name'):
                continue
            
            # 创建结算单明细
            settlement_detail = SettlementOrderDetail(
                pricing_order_id=order_id,
                product_name=detail_data['product_name'],
                product_model=detail_data.get('product_model', ''),
                product_desc=detail_data.get('product_desc', ''),
                brand=detail_data.get('brand', ''),
                unit=detail_data.get('unit', '台'),
                product_mn=detail_data.get('product_mn', ''),
                market_price=float(detail_data.get('market_price', 0)),
                quantity=int(detail_data.get('quantity', 1)),
                discount_rate=float(detail_data.get('discount_rate', 100)) / 100,
                pricing_detail_id=detail_data.get('pricing_detail_id')  # 如果有关联的批价单明细
            )
            
            # 计算价格
            settlement_detail.calculate_prices()
            db.session.add(settlement_detail)
        
        # 重新计算总额
        pricing_order.calculate_settlement_totals()
        
        db.session.commit()
        
        # 检查项目阶段是否被意外修改
        project_stage_after = pricing_order.project.current_stage if pricing_order.project else None
        if project_stage_before != project_stage_after:
            logger.warning(f"警告：保存结算单 {pricing_order.order_number} 明细时，项目阶段发生了意外变化: {project_stage_before} -> {project_stage_after}")
        else:
            logger.info(f"保存结算单 {pricing_order.order_number} 明细后，项目阶段保持不变: {project_stage_after}")
        
        return jsonify({
            'success': True,
            'message': '结算单明细保存成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存结算单明细失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        })


@pricing_order_bp.route('/test')
@login_required
def test_pricing():
    """测试页面 - 仅用于开发调试"""
    return "<h1>批价单功能测试页面</h1><p>当前系统运行正常</p>"


@pricing_order_bp.route('/<int:order_id>/save_all', methods=['POST'])
@login_required
def save_all_pricing_data(order_id):
    """保存批价单所有数据（基本信息和明细）"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 记录当前项目阶段状态用于调试
        project_stage_before = pricing_order.project.current_stage if pricing_order.project else None
        logger.info(f"保存批价单 {pricing_order.order_number} 所有数据前，项目阶段: {project_stage_before}")
        
        # 权限检查 - 使用统一的权限检查函数
        can_edit_pricing, _, _ = check_pricing_edit_permission(pricing_order, current_user)
        if not can_edit_pricing:
            return jsonify({
                'success': False,
                'message': '您没有权限编辑该批价单'
            })
        
        data = request.get_json()
        basic_info = data.get('basic_info', {})
        pricing_details = data.get('pricing_details', [])
        settlement_details = data.get('settlement_details', [])
        
        # 更新基本信息
        if 'distributor_id' in basic_info:
            distributor_id = basic_info['distributor_id']
            if distributor_id and str(distributor_id).strip():
                try:
                    pricing_order.distributor_id = int(distributor_id)
                except (ValueError, TypeError):
                    pricing_order.distributor_id = None
            else:
                pricing_order.distributor_id = None
                
        if 'dealer_id' in basic_info:
            dealer_id = basic_info['dealer_id']
            if dealer_id and str(dealer_id).strip():
                try:
                    pricing_order.dealer_id = int(dealer_id)
                except (ValueError, TypeError):
                    pricing_order.dealer_id = None
            else:
                pricing_order.dealer_id = None
        
        # 保存批价单明细（如果提供）
        if pricing_details:
            # 删除现有批价单明细
            existing_pricing_details = PricingOrderDetail.query.filter_by(pricing_order_id=order_id).all()
            for detail in existing_pricing_details:
                # 同时删除对应的结算单明细
                settlement_detail = SettlementOrderDetail.query.filter_by(
                    pricing_detail_id=detail.id
                ).first()
                if settlement_detail:
                    db.session.delete(settlement_detail)
                db.session.delete(detail)
            
            # 创建新的批价单明细
            for detail_data in pricing_details:
                if not detail_data.get('product_name'):
                    continue
                
                # 获取前端传递的数据
                market_price = float(detail_data.get('market_price', 0))
                quantity = int(detail_data.get('quantity', 1))
                discount_rate_percent = float(detail_data.get('discount_rate', 100))
                unit_price = float(detail_data.get('unit_price', 0))
                
                # 转换折扣率为小数形式
                discount_rate = discount_rate_percent / 100
                
                # 如果前端没有传递单价，则根据折扣率计算
                if unit_price == 0 and market_price > 0:
                    unit_price = market_price * discount_rate
                
                logger.info(f"保存批价单明细 - 产品: {detail_data['product_name']}, 市场价: {market_price}, 单价: {unit_price}, 数量: {quantity}, 折扣率: {discount_rate_percent}%")
                
                pricing_detail = PricingOrderDetail(
                    pricing_order_id=order_id,
                    product_name=detail_data['product_name'],
                    product_model=detail_data.get('product_model', ''),
                    product_desc=detail_data.get('product_desc', ''),
                    brand=detail_data.get('brand', ''),
                    unit=detail_data.get('unit', '台'),
                    product_mn=detail_data.get('product_mn', ''),
                    market_price=market_price,
                    unit_price=unit_price,  # 直接使用计算好的单价
                    quantity=quantity,
                    discount_rate=discount_rate,
                    source_type='manual'
                )
                # 重新计算总价以确保一致性
                pricing_detail.total_price = unit_price * quantity
                db.session.add(pricing_detail)
                db.session.flush()
                
                # 查找对应的结算单明细数据
                settlement_data = None
                for s_detail in settlement_details:
                    if s_detail.get('product_name') == detail_data['product_name']:
                        settlement_data = s_detail
                        break
                
                # 创建结算单明细，优先使用前端传递的结算单数据
                if settlement_data:
                    # 使用前端传递的结算单明细数据
                    settlement_market_price = float(settlement_data.get('market_price', market_price))
                    settlement_quantity = int(settlement_data.get('quantity', quantity))
                    settlement_discount_rate_percent = float(settlement_data.get('discount_rate', discount_rate_percent))
                    settlement_unit_price = float(settlement_data.get('unit_price', unit_price))
                    
                    # 转换折扣率为小数形式
                    settlement_discount_rate = settlement_discount_rate_percent / 100
                    
                    # 如果前端没有传递单价，则根据折扣率计算
                    if settlement_unit_price == 0 and settlement_market_price > 0:
                        settlement_unit_price = settlement_market_price * settlement_discount_rate
                    
                    logger.info(f"保存结算单明细 - 产品: {settlement_data['product_name']}, 市场价: {settlement_market_price}, 单价: {settlement_unit_price}, 数量: {settlement_quantity}, 折扣率: {settlement_discount_rate_percent}%")
                else:
                    # 如果没有对应的结算单数据，使用批价单数据作为默认值
                    settlement_market_price = market_price
                    settlement_quantity = quantity
                    settlement_discount_rate = discount_rate
                    settlement_unit_price = unit_price
                    logger.info(f"未找到对应结算单明细，使用批价单数据作为默认值 - 产品: {detail_data['product_name']}")
                
                settlement_detail = SettlementOrderDetail(
                    pricing_order_id=order_id,
                    product_name=pricing_detail.product_name,
                    product_model=pricing_detail.product_model,
                    product_desc=pricing_detail.product_desc,
                    brand=pricing_detail.brand,
                    unit=pricing_detail.unit,
                    product_mn=pricing_detail.product_mn,
                    market_price=settlement_market_price,
                    unit_price=settlement_unit_price,
                    quantity=settlement_quantity,
                    discount_rate=settlement_discount_rate,
                    pricing_detail_id=pricing_detail.id
                )
                # 重新计算总价以确保一致性
                settlement_detail.total_price = settlement_unit_price * settlement_quantity
                db.session.add(settlement_detail)
        
        # 保存结算单明细（如果提供且有权限）
        _, can_edit_settlement, _ = check_pricing_edit_permission(pricing_order, current_user)
        if settlement_details and can_edit_settlement:
            # 更新现有结算单明细
            for detail_data in settlement_details:
                if not detail_data.get('id'):
                    continue
                
                settlement_detail = SettlementOrderDetail.query.get(detail_data['id'])
                if settlement_detail and settlement_detail.pricing_order_id == order_id:
                    if 'discount_rate' in detail_data:
                        discount_rate_percent = float(detail_data['discount_rate'])
                        settlement_detail.discount_rate = discount_rate_percent / 100
                        logger.info(f"保存时更新结算单明细 {detail_data['id']}: 折扣率从前端 {discount_rate_percent}% 转换为 {settlement_detail.discount_rate:.3f}")
                    if 'unit_price' in detail_data:
                        settlement_detail.unit_price = float(detail_data['unit_price'])
                    settlement_detail.calculate_prices()
        
        # 重新计算总额和总折扣率（基于明细数据）
        pricing_order.calculate_pricing_totals(recalculate_discount_rate=True)
        pricing_order.calculate_settlement_totals(recalculate_discount_rate=True)
        
        db.session.commit()
        
        # 检查项目阶段是否被意外修改
        project_stage_after = pricing_order.project.current_stage if pricing_order.project else None
        if project_stage_before != project_stage_after:
            logger.warning(f"警告：保存批价单 {pricing_order.order_number} 数据时，项目阶段发生了意外变化: {project_stage_before} -> {project_stage_after}")
        else:
            logger.info(f"保存批价单 {pricing_order.order_number} 数据后，项目阶段保持不变: {project_stage_after}")
        
        return jsonify({
            'success': True,
            'message': '批价单保存成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存批价单所有数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        })


@pricing_order_bp.route('/<int:order_id>/save_and_submit', methods=['POST'])
@login_required
def save_and_submit_pricing_order(order_id):
    """保存并提交批价单审批"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 权限检查
        if pricing_order.created_by != current_user.id and current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': '您没有权限提交该批价单'
            })
        
        # 先保存所有数据
        data = request.get_json()
        basic_info = data.get('basic_info', {})
        pricing_details = data.get('pricing_details', [])
        settlement_details = data.get('settlement_details', [])
        
        # 更新基本信息
        # 处理厂商直签和厂家提货字段
        is_direct_contract = basic_info.get('is_direct_contract', False)
        is_factory_pickup = basic_info.get('is_factory_pickup', False)
        
        pricing_order.is_direct_contract = is_direct_contract
        pricing_order.is_factory_pickup = is_factory_pickup
        
        # 根据厂商直签状态处理经销商和分销商
        if is_direct_contract:
            # 厂商直签时，清空经销商和分销商
            pricing_order.dealer_id = None
            pricing_order.distributor_id = None
        else:
            # 非厂商直签时，正常处理经销商和分销商
            if 'dealer_id' in basic_info:
                dealer_id = basic_info['dealer_id']
                if dealer_id and str(dealer_id).strip():
                    try:
                        pricing_order.dealer_id = int(dealer_id)
                    except (ValueError, TypeError):
                        pricing_order.dealer_id = None
                else:
                    pricing_order.dealer_id = None
            
            # 处理分销商：如果厂家提货开启，清空分销商
            if is_factory_pickup:
                pricing_order.distributor_id = None
            elif 'distributor_id' in basic_info:
                distributor_id = basic_info['distributor_id']
                if distributor_id and str(distributor_id).strip():
                    try:
                        pricing_order.distributor_id = int(distributor_id)
                    except (ValueError, TypeError):
                        pricing_order.distributor_id = None
                else:
                    pricing_order.distributor_id = None
        
        # 保存明细（如果提供）
        if pricing_details:
            # 删除现有明细
            existing_details = PricingOrderDetail.query.filter_by(pricing_order_id=order_id).all()
            for detail in existing_details:
                settlement_detail = SettlementOrderDetail.query.filter_by(
                    pricing_detail_id=detail.id
                ).first()
                if settlement_detail:
                    db.session.delete(settlement_detail)
                db.session.delete(detail)
            
            # 创建新明细
            for detail_data in pricing_details:
                if not detail_data.get('product_name'):
                    continue
                
                # 获取前端传递的数据
                market_price = float(detail_data.get('market_price', 0))
                quantity = int(detail_data.get('quantity', 1))
                discount_rate_percent = float(detail_data.get('discount_rate', 100))
                unit_price = float(detail_data.get('unit_price', 0))
                
                # 转换折扣率为小数形式
                discount_rate = discount_rate_percent / 100
                
                # 如果前端没有传递单价，则根据折扣率计算
                if unit_price == 0 and market_price > 0:
                    unit_price = market_price * discount_rate
                
                logger.info(f"提交批价单明细 - 产品: {detail_data['product_name']}, 市场价: {market_price}, 单价: {unit_price}, 数量: {quantity}, 折扣率: {discount_rate_percent}%")
                
                pricing_detail = PricingOrderDetail(
                    pricing_order_id=order_id,
                    product_name=detail_data['product_name'],
                    product_model=detail_data.get('product_model', ''),
                    product_desc=detail_data.get('product_desc', ''),
                    brand=detail_data.get('brand', ''),
                    unit=detail_data.get('unit', '台'),
                    product_mn=detail_data.get('product_mn', ''),
                    market_price=market_price,
                    unit_price=unit_price,  # 直接使用计算好的单价
                    quantity=quantity,
                    discount_rate=discount_rate,
                    source_type='manual'
                )
                # 重新计算总价以确保一致性
                pricing_detail.total_price = unit_price * quantity
                db.session.add(pricing_detail)
                db.session.flush()
                
                # 同时创建结算单明细，使用对应的结算单数据
                settlement_data = None
                # 查找对应的结算单明细数据
                for s_detail in settlement_details:
                    if s_detail.get('product_name') == detail_data['product_name']:
                        settlement_data = s_detail
                        break
                
                if settlement_data:
                    # 使用前端传递的结算单明细数据
                    settlement_market_price = float(settlement_data.get('market_price', market_price))
                    settlement_quantity = int(settlement_data.get('quantity', quantity))
                    settlement_discount_rate_percent = float(settlement_data.get('discount_rate', discount_rate_percent))
                    settlement_unit_price = float(settlement_data.get('unit_price', unit_price))
                    
                    # 转换折扣率为小数形式
                    settlement_discount_rate = settlement_discount_rate_percent / 100
                    
                    # 如果前端没有传递单价，则根据折扣率计算
                    if settlement_unit_price == 0 and settlement_market_price > 0:
                        settlement_unit_price = settlement_market_price * settlement_discount_rate
                    
                    logger.info(f"提交结算单明细 - 产品: {settlement_data['product_name']}, 市场价: {settlement_market_price}, 单价: {settlement_unit_price}, 数量: {settlement_quantity}, 折扣率: {settlement_discount_rate_percent}%")
                else:
                    # 如果没有对应的结算单数据，使用批价单数据
                    settlement_market_price = market_price
                    settlement_quantity = quantity
                    settlement_discount_rate = discount_rate
                    settlement_unit_price = unit_price
                    logger.info(f"未找到对应结算单明细，使用批价单数据 - 产品: {detail_data['product_name']}")
                
                settlement_detail = SettlementOrderDetail(
                    pricing_order_id=order_id,
                    product_name=pricing_detail.product_name,
                    product_model=pricing_detail.product_model,
                    product_desc=pricing_detail.product_desc,
                    brand=pricing_detail.brand,
                    unit=pricing_detail.unit,
                    product_mn=pricing_detail.product_mn,
                    market_price=settlement_market_price,
                    unit_price=settlement_unit_price,
                    quantity=settlement_quantity,
                    discount_rate=settlement_discount_rate,
                    pricing_detail_id=pricing_detail.id
                )
                # 重新计算总价以确保一致性
                settlement_detail.total_price = settlement_unit_price * settlement_quantity
                db.session.add(settlement_detail)
        
        # 重新计算总额和总折扣率（基于明细数据）
        pricing_order.calculate_pricing_totals(recalculate_discount_rate=True)
        pricing_order.calculate_settlement_totals(recalculate_discount_rate=True)
        
        # 提交审批
        success, error = PricingOrderService.submit_for_approval(order_id, current_user.id)
        
        if not success:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': error
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '批价单已保存并提交审批'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存并提交批价单失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'保存并提交失败: {str(e)}'
        })


@pricing_order_bp.route('/<int:order_id>/recall', methods=['POST'])
@login_required
def recall_pricing_order(order_id):
    """召回批价单"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        success, error = PricingOrderService.recall_pricing_order(
            order_id, current_user.id, reason
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': error
            }), 400
        
        logger.info(f"用户 {current_user.username} 召回了批价单 {order_id}")
        
        return jsonify({
            'success': True,
            'message': '批价单已成功召回'
        })
        
    except Exception as e:
        logger.error(f"召回批价单失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'召回失败: {str(e)}'
        }), 500


@pricing_order_bp.route('/<int:order_id>/delete', methods=['DELETE'])
@login_required
def delete_pricing_order(order_id):
    """删除批价单"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 权限检查：只有创建人且状态为草稿时才能删除
        if pricing_order.created_by != current_user.id:
            return jsonify({
                'success': False,
                'message': '您没有权限删除该批价单'
            }), 403
        
        if pricing_order.status != 'draft':
            return jsonify({
                'success': False,
                'message': '只有草稿状态的批价单才能删除'
            }), 400
        
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        # 删除相关的结算单明细
        settlement_details = SettlementOrderDetail.query.filter_by(
            pricing_order_id=order_id
        ).all()
        for detail in settlement_details:
            db.session.delete(detail)
        
        # 删除结算单主记录
        settlement_orders = SettlementOrder.query.filter_by(
            pricing_order_id=order_id
        ).all()
        for settlement_order in settlement_orders:
            db.session.delete(settlement_order)
        
        # 删除批价单明细
        pricing_details = PricingOrderDetail.query.filter_by(
            pricing_order_id=order_id
        ).all()
        for detail in pricing_details:
            db.session.delete(detail)
        
        # 删除审批记录（如果有）
        approval_records = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=order_id
        ).all()
        for record in approval_records:
            db.session.delete(record)
        
        # 删除批价单
        db.session.delete(pricing_order)
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 删除了批价单 {pricing_order.order_number}，原因: {reason}")
        
        return jsonify({
            'success': True,
            'message': '批价单已成功删除'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除批价单失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@pricing_order_bp.route('/<int:order_id>/export_pdf/<pdf_type>')
@login_required
def export_pdf(order_id, pdf_type):
    """导出批价单/结算单PDF"""
    try:
        pricing_order = PricingOrder.query.get_or_404(order_id)
        
        # 权限检查 - 使用统一的权限管理
        if not PricingOrderService.can_export_pdf(pricing_order, current_user, pdf_type):
            flash('您没有权限导出该批价单', 'danger')
            return redirect(url_for('pricing_order.edit_pricing_order', order_id=order_id))
        
        # 创建PDF生成器实例
        pdf_generator = PDFGenerator()
        
        # 根据类型生成PDF
        if pdf_type == 'pricing':
            pdf_result = pdf_generator.generate_pricing_order_pdf(pricing_order)
            pdf_content = pdf_result['content']
            filename = pdf_result['filename']
        elif pdf_type == 'settlement':
            # 检查结算单查看权限
            if not PricingOrderService.can_view_settlement_tab(current_user):
                flash('您没有权限查看结算单', 'danger')
                return redirect(url_for('pricing_order.edit_pricing_order', order_id=order_id))
            pdf_result = pdf_generator.generate_settlement_order_pdf(pricing_order)
            pdf_content = pdf_result['content']
            filename = pdf_result['filename']
        else:
            flash('无效的PDF类型', 'danger')
            return redirect(url_for('pricing_order.edit_pricing_order', order_id=order_id))
        
        # 创建临时文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_content)
        temp_file.close()
        
        # 发送文件
        def remove_file(response):
            try:
                os.remove(temp_file.name)
            except Exception as e:
                logger.warning(f"清理临时PDF文件失败: {str(e)}")
            return response
        
        response = send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
        # 在响应后清理临时文件
        response.call_on_close(lambda: remove_file(response))
        
        return response
        
    except Exception as e:
        logger.error(f"导出PDF失败: {str(e)}")
        flash(f'导出PDF失败: {str(e)}', 'danger')
        return redirect(url_for('pricing_order.edit_pricing_order', order_id=order_id))


@pricing_order_bp.route('/<int:order_id>/admin_rollback', methods=['POST'])
@login_required
def admin_rollback_pricing_order(order_id):
    """管理员退回已通过的批价单"""
    try:
        from app.permissions import admin_required
        from flask import abort
        
        # 检查管理员权限
        if current_user.role != 'admin':
            abort(403)
        
        # 检查是否可以退回
        if not PricingOrderService.can_admin_rollback_pricing_order(order_id, current_user.id):
            return jsonify({
                'success': False,
                'message': '权限不足或批价单状态不允许退回'
            }), 403
        
        # 获取退回原因
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        # 执行退回操作
        success, message = PricingOrderService.admin_rollback_pricing_order(
            order_id, current_user.id, reason
        )
        
        if not success:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
        logger.info(f"管理员 {current_user.username} 退回了批价单 {order_id}")
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"管理员退回批价单失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'退回失败: {str(e)}'
        }), 500 