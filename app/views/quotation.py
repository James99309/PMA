from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.models.quotation import Quotation, QuotationDetail
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.product import Product  # 添加产品模型导入
from datetime import datetime
from sqlalchemy import or_, func
from app import db
from flask_login import login_required, current_user
from app.decorators import permission_required, permission_required_with_approval_context  # 添加权限装饰器导入
from app.utils.access_control import get_viewable_data, can_edit_data, can_view_project, can_change_quotation_owner
import logging
from decimal import Decimal
import json
from flask import current_app
from app.utils.dictionary_helpers import project_type_label, project_stage_label, REPORT_SOURCE_OPTIONS, PROJECT_TYPE_OPTIONS, PRODUCT_SITUATION_OPTIONS, PROJECT_STAGE_LABELS, COMPANY_TYPE_LABELS
from app.utils.notification_helpers import trigger_event_notification
from app.services.event_dispatcher import notify_project_created, notify_project_status_updated
from app.helpers.project_helpers import is_project_editable
from app.utils.activity_tracker import check_company_activity, update_active_status
from app.models.settings import SystemSettings
from zoneinfo import ZoneInfo
from app.utils.role_mappings import get_role_display_name
from app.utils.solution_manager_notifications import notify_solution_managers_quotation_created, notify_solution_managers_quotation_updated
from app.helpers.approval_helpers import get_object_approval_instance, get_current_step_info, can_user_approve
from sqlalchemy import event
from app.models.quotation import update_quotation_product_signature, QuotationDetail

# 配置日志
logger = logging.getLogger(__name__)

quotation = Blueprint('quotation', __name__)

@quotation.route('/quotations')
@login_required
@permission_required('quotation', 'view')  # 添加视图权限装饰器
def list_quotations():
    try:
        # 获取搜索参数
        project_search = request.args.get('project', '')
        project_type = request.args.get('project_type', '')
        
        # 获取排序参数
        sort_field = request.args.get('sort', 'created_at')  # 默认按创建时间排序
        sort_order = request.args.get('order', 'desc')  # 默认降序
        
        # 使用访问控制函数构建查询
        query = get_viewable_data(Quotation, current_user)
        
        # 渠道经理默认只查看渠道跟进项目的报价单
        if current_user.role and current_user.role.strip() == 'channel_manager' and not project_type:
            project_type = 'channel_follow'
        
        # 营销总监默认查看销售重点和渠道跟进项目的报价单
        if current_user.role and current_user.role.strip() == 'sales_director' and not project_type:
            # 使用特殊标识来表示多个项目类型
            project_type = 'marketing_focus'
        
        # 标记是否已经JOIN了Project表
        project_joined = False
        
        # 项目名称搜索
        if project_search:
            query = query.join(Project)
            query = query.filter(Project.project_name.like(f'%{project_search}%'))
            project_joined = True
        
        # 项目类型筛选
        if project_type:
            if not project_joined:
                query = query.join(Project, Quotation.project_id == Project.id)
                project_joined = True
            
            if project_type == 'channel_follow':
                query = query.filter(Project.project_type.in_(['channel_follow', '渠道跟进']))
            elif project_type == 'sales_focus':
                query = query.filter(Project.project_type.in_(['sales_focus', '销售重点']))
            elif project_type == 'marketing_focus':
                # 营销总监的特殊筛选：销售重点和渠道跟进
                query = query.filter(Project.project_type.in_(['sales_focus', 'channel_follow', '销售重点', '渠道跟进']))
            else:
                query = query.filter(Project.project_type == project_type)
        
        # 处理排序
        if sort_field == 'project_name':
            # 按项目名称排序需要关联Project表
            if not project_joined:
                query = query.join(Project, Quotation.project_id == Project.id)
                project_joined = True
            if sort_order == 'desc':
                query = query.order_by(Project.project_name.desc())
            else:
                query = query.order_by(Project.project_name.asc())
        elif sort_field == 'project_stage':
            # 按项目阶段排序需要关联Project表
            if not project_joined:
                query = query.join(Project, Quotation.project_id == Project.id)
                project_joined = True
            if sort_order == 'desc':
                query = query.order_by(Project.current_stage.desc())
            else:
                query = query.order_by(Project.current_stage.asc())
        elif sort_field == 'project_type':
            # 按项目类型排序需要关联Project表
            if not project_joined:
                query = query.join(Project, Quotation.project_id == Project.id)
                project_joined = True
            if sort_order == 'desc':
                query = query.order_by(Project.project_type.desc())
            else:
                query = query.order_by(Project.project_type.asc())
        elif sort_field == 'owner':
            # 按拥有人排序
            if sort_order == 'desc':
                query = query.order_by(Quotation.owner_id.desc())
            else:
                query = query.order_by(Quotation.owner_id.asc())
        else:
            # 其他字段直接使用
            sort_attr = getattr(Quotation, sort_field, Quotation.created_at)
            if sort_order == 'desc':
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        
        quotations = query.all()
        
        # 获取项目类型选项
        project_type_options = [
            {'value': '', 'label': '全部类型'},
            {'value': 'channel_follow', 'label': '渠道跟进'},
            {'value': 'sales_focus', 'label': '销售重点'}
        ]
        
        # 为营销总监添加特殊选项
        if current_user.role and current_user.role.strip() == 'sales_director':
            project_type_options.insert(1, {'value': 'marketing_focus', 'label': '营销重点项目'})
        
        return render_template('quotation/list.html', 
                              quotations=quotations, 
                              sort_field=sort_field, 
                              sort_order=sort_order,
                              project_type=project_type,
                              project_type_options=project_type_options,
                              project_search=project_search)
                              
    except Exception as e:
        logger.error(f"加载报价单列表时出错: {str(e)}", exc_info=True)
        
        # 尝试回滚数据库事务
        try:
            db.session.rollback()
            logger.info("数据库事务已回滚")
        except Exception as rollback_error:
            logger.error(f"数据库事务回滚失败: {str(rollback_error)}")
        
        flash(f'加载报价单失败：{str(e)}', 'danger')
        return render_template('quotation/list.html', 
                              quotations=[], 
                              sort_field='created_at', 
                              sort_order='desc',
                              project_type='',
                              project_type_options=[],
                              project_search='')

@quotation.route('/create', methods=['GET', 'POST'])
@login_required
@permission_required('quotation', 'create')  # 添加创建权限装饰器
def create_quotation():
    # 获取返回URL参数
    return_to = request.args.get('return_to')
    
    # 获取预设的项目ID
    preset_project_id = request.args.get('project_id')
    
    if request.method == 'POST':
        try:
            # 检查请求是否为JSON数据
            if request.is_json:
                current_app.logger.debug("收到创建报价单的AJAX请求")
                # 获取请求中的JSON数据
                data = request.get_json()
                
                # 记录请求数据结构
                current_app.logger.debug(f"创建报价单请求数据结构: {data.keys() if isinstance(data, dict) else '非字典数据'}")
                
                # 验证数据是否为空
                if not data:
                    current_app.logger.error("请求数据为空或格式错误")
                    return jsonify({
                        'status': 'error',
                        'message': '请求数据为空或格式错误'
                    }), 400
                
                # 验证项目ID
                if not data.get('project_id'):
                    current_app.logger.error("请求数据中缺少project_id字段")
                    return jsonify({
                        'status': 'error',
                        'message': '项目不能为空'
                    }), 400
                
                # 确保项目ID是整数
                try:
                    project_id = int(data.get('project_id'))
                    
                    # 验证项目是否存在
                    project = Project.query.get(project_id)
                    if not project:
                        current_app.logger.error(f"项目ID {project_id} 不存在")
                        return jsonify({
                            'status': 'error',
                            'message': f'ID为{project_id}的项目不存在'
                        }), 400
                except (ValueError, TypeError) as e:
                    current_app.logger.error(f"项目ID类型转换错误: {str(e)}")
                    return jsonify({
                        'status': 'error',
                        'message': '项目ID格式错误，必须是整数'
                    }), 400
                
                # 获取总金额
                try:
                    total_amount = float(data.get('total_amount', 0))
                    if total_amount < 0:
                        total_amount = 0
                except (ValueError, TypeError) as e:
                    current_app.logger.error(f"解析总金额失败: {str(e)}")
                    return jsonify({
                        'status': 'error',
                        'message': f'总金额格式错误: {str(e)}'
                    }), 400
                
                # 创建新报价单
                quotation = Quotation(
                    project_id=project_id,
                    contact_id=None,
                    amount=total_amount,
                    project_stage=data.get('project_stage', ''),
                    project_type=data.get('project_type', ''),
                    currency=data.get('currency', 'CNY'),  # 添加货币字段
                    owner_id=current_user.id
                )
                db.session.add(quotation)
                current_app.logger.debug(f"创建新报价单: {quotation.quotation_number}")
                
                # 添加明细项
                details = data.get('details', [])
                detail_errors = []
                
                if not details:
                    current_app.logger.warning("报价单没有明细项")
                    return jsonify({
                        'status': 'error',
                        'message': '报价单必须包含至少一个明细项'
                    }), 400
                
                if not isinstance(details, list):
                    current_app.logger.error(f'明细项不是列表格式: {type(details)}')
                    return jsonify({
                        'status': 'error',
                        'message': '明细项必须是数组格式'
                    }), 400
                
                current_app.logger.debug(f'开始处理 {len(details)} 个明细项')
                
                for index, detail in enumerate(details):
                    try:
                        current_app.logger.debug(f'处理第 {index+1} 个明细项: {detail}')
                        
                        if not isinstance(detail, dict):
                            error_msg = f"第 {index+1} 行数据格式错误，必须是对象格式"
                            current_app.logger.error(error_msg)
                            detail_errors.append(error_msg)
                            continue
                        
                        # 验证必填字段
                        product_name = detail.get('product_name', '').strip()
                        if not product_name:
                            error_msg = f"第 {index+1} 行产品名称不能为空"
                            current_app.logger.warning(error_msg)
                            detail_errors.append(error_msg)
                            continue
                        
                        # 安全地获取数值字段
                        try:
                            market_price = float(detail.get('market_price', 0))
                        except (ValueError, TypeError) as e:
                            market_price = 0
                            error_msg = f"第 {index+1} 行市场价格格式无效"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        try:
                            discount = float(detail.get('discount_rate', 100)) / 100
                            # 确保折扣率不小于0，不限制上限
                            if discount < 0:
                                error_msg = f"第 {index+1} 行折扣率不能为负数"
                                current_app.logger.warning(error_msg)
                                detail_errors.append(error_msg)
                                discount = 0
                        except (ValueError, TypeError) as e:
                            discount = 1.0
                            error_msg = f"第 {index+1} 行折扣率格式无效，已设为100%"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        try:
                            quantity = int(detail.get('quantity', 1))
                            if quantity <= 0:
                                quantity = 1
                                error_msg = f"第 {index+1} 行数量必须大于0，已设为1"
                                current_app.logger.warning(error_msg)
                                detail_errors.append(error_msg)
                        except (ValueError, TypeError) as e:
                            quantity = 1
                            error_msg = f"第 {index+1} 行数量格式无效，已设为1"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        try:
                            unit_price = float(detail.get('unit_price', 0))
                            if unit_price < 0:
                                unit_price = 0
                                error_msg = f"第 {index+1} 行单价不能为负数，已设为0"
                                current_app.logger.warning(error_msg)
                                detail_errors.append(error_msg)
                        except (ValueError, TypeError) as e:
                            unit_price = 0
                            error_msg = f"第 {index+1} 行单价格式无效，已设为0"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        try:
                            total_price = float(detail.get('total_price', 0))
                            if total_price < 0:
                                total_price = 0
                                error_msg = f"第 {index+1} 行小计不能为负数，已设为0"
                                current_app.logger.warning(error_msg)
                                detail_errors.append(error_msg)
                        except (ValueError, TypeError) as e:
                            # 如果小计无效，从单价和数量重新计算
                            total_price = unit_price * quantity
                            error_msg = f"第 {index+1} 行小计格式无效，已重新计算为: {total_price}"
                            current_app.logger.warning(f"{error_msg}: {str(e)}")
                            detail_errors.append(error_msg)
                        
                        # 创建新明细
                        new_detail = QuotationDetail(
                            product_name=product_name,
                            product_model=detail.get('product_model', ''),
                            product_desc=detail.get('product_desc', ''),
                            brand=detail.get('brand', ''),
                            unit=detail.get('unit', ''),
                            quantity=quantity,
                            discount=discount,
                            market_price=market_price,
                            unit_price=unit_price,
                            total_price=total_price,
                            product_mn=detail.get('product_mn', ''),
                            currency=data.get('currency', 'CNY')  # 添加明细货币字段
                        )
                        current_app.logger.debug(f'创建第 {index+1} 行明细项')
                        quotation.details.append(new_detail)
                    except Exception as item_error:
                        error_msg = f"处理第 {index+1} 行明细时出错: {str(item_error)}"
                        current_app.logger.error(error_msg)
                        detail_errors.append(error_msg)
                
                try:
                    current_app.logger.info('准备提交所有更改到数据库...')
                    db.session.commit()
                    current_app.logger.info('数据库更改提交成功')
                    
                    # 手动更新时间戳，确保updated_at字段正确
                    quotation.updated_at = datetime.utcnow()
                    db.session.commit()
                    
                    # 记录创建历史
                    try:
                        from app.utils.change_tracker import ChangeTracker
                        ChangeTracker.log_create(quotation)
                    except Exception as track_err:
                        current_app.logger.warning(f"记录报价单创建历史失败: {str(track_err)}")
                    
                    # 注意：项目金额更新交由SQLAlchemy事件监听器处理，此处无需手动更新
                    current_app.logger.info('项目报价金额将由事件监听器自动更新')
                    
                    # 异步触发报价单创建通知，避免阻塞响应
                    try:
                        from app.utils.notification_helpers import trigger_event_notification
                        from flask import url_for
                        import threading
                        from app.utils.solution_manager_notifications import notify_solution_managers_quotation_created
                        
                        # 在线程外获取app实例和必要数据
                        app = current_app._get_current_object()
                        quotation_owner_id = quotation.owner_id
                        quotation_id = quotation.id
                        
                        def send_notifications_async():
                            """异步发送通知"""
                            with app.app_context():
                                try:
                                    # 重新查询quotation对象以获取最新状态
                                    fresh_quotation = Quotation.query.get(quotation_id)
                                    if fresh_quotation:
                                        # 构建URL而不使用url_for
                                        quotation_url = f"http://localhost:10000/quotation/{quotation_id}/detail"
                                        
                                        # 触发报价单创建通知
                                        trigger_event_notification(
                                            event_key='quotation_created',
                                            target_user_id=quotation_owner_id,
                                            context={
                                                'quotation': fresh_quotation,
                                                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                'quotation_url': quotation_url,
                                                'current_year': datetime.now().year
                                            }
                                        )
                                        # 通知解决方案经理（异步）
                                        notify_solution_managers_quotation_created(fresh_quotation)
                                        app.logger.debug('异步报价单创建通知已发送')
                                except Exception as notify_err:
                                    app.logger.warning(f"异步触发报价单创建通知失败: {str(notify_err)}")
                        
                        # 启动异步通知线程
                        threading.Thread(target=send_notifications_async, daemon=True).start()
                        current_app.logger.debug('异步通知线程已启动')
                        
                    except Exception as notify_err:
                        logger.warning(f"启动异步通知失败: {str(notify_err)}")
                    
                    # 移除flash消息，直接跳转（提升用户体验）
                    # flash('报价单创建成功！', 'success')
                    
                    # 处理返回URL
                    if return_to and 'project/view' in return_to:
                        return redirect(return_to)
                    else:
                        return redirect(url_for('quotation.list_quotations'))
                except Exception as commit_error:
                    db.session.rollback()
                    error_type = type(commit_error).__name__
                    current_app.logger.error(f"提交更改时出错: {error_type} - {str(commit_error)}")
                    
                    # 返回错误信息
                    return jsonify({
                        'status': 'error',
                        'message': f'保存失败: {error_type} - {str(commit_error)}'
                    }), 500
            else:
                # 传统表单提交的处理逻辑保留
                # 创建报价单
                quotation = Quotation(
                    project_id=request.form.get('project_id'),
                    contact_id=None,
                    currency=request.form.get('currency', 'CNY'),  # 添加货币字段
                    owner_id=current_user.id  # 设置当前用户为所有者
                )
                db.session.add(quotation)
                
                # 创建报价单明细
                product_names = request.form.getlist('product_name[]')
                product_models = request.form.getlist('product_model[]')
                product_descs = request.form.getlist('product_spec[]')
                brands = request.form.getlist('product_brand[]')
                units = request.form.getlist('product_unit[]')
                discounts = request.form.getlist('discount_rate[]')
                market_prices = request.form.getlist('product_price[]')
                quantities = request.form.getlist('quantity[]')
                product_mns = request.form.getlist('product_mn[]')  # 添加MN号字段
                
                total_amount = 0.0
                for i in range(len(product_names)):
                    # 清理价格字符串中的千位分隔符
                    cleaned_price = market_prices[i].replace(',', '') if market_prices[i] else '0'
                    cleaned_discount = discounts[i].replace(',', '') if discounts[i] else '0'
                    cleaned_quantity = quantities[i].replace(',', '') if quantities[i] else '0'
                    
                    market_price = float(cleaned_price)
                    discount = float(cleaned_discount)
                    quantity = float(cleaned_quantity)
                    discounted_price = market_price * (discount / 100)  # 修正：折扣率应该是discount/100而不是1-discount/100
                    subtotal = discounted_price * quantity  # 计算小计
                    total_amount += subtotal  # 累加总金额
                    
                    detail = QuotationDetail(
                        product_name=product_names[i],
                        product_model=product_models[i],
                        product_desc=product_descs[i],
                        brand=brands[i],
                        unit=units[i],
                        discount=discount/100,  # 存储为小数形式
                        market_price=market_price,
                        quantity=quantity,
                        unit_price=discounted_price,
                        total_price=subtotal,
                        product_mn=product_mns[i] if i < len(product_mns) else '',  # 添加MN号
                        currency=request.form.get('currency', 'CNY')  # 添加明细货币字段
                    )
                    
                    # 计算植入小计
                    detail.calculate_prices()
                    
                    quotation.details.append(detail)
                
                # 更新报价单总金额
                quotation.amount = total_amount
                # 手动更新时间戳，确保updated_at字段正确
                quotation.updated_at = datetime.utcnow()
                db.session.commit()
                
                # 记录创建历史
                try:
                    from app.utils.change_tracker import ChangeTracker
                    ChangeTracker.log_create(quotation)
                except Exception as track_err:
                    current_app.logger.warning(f"记录报价单创建历史失败: {str(track_err)}")
                
                # 注意：项目金额更新交由SQLAlchemy事件监听器处理，此处无需手动更新
                current_app.logger.info('项目报价金额将由事件监听器自动更新')
                
                # 触发报价单创建通知
                try:
                    from app.utils.notification_helpers import trigger_event_notification
                    from flask import url_for
                    trigger_event_notification(
                        event_key='quotation_created',
                        target_user_id=quotation.owner_id,
                        context={
                            'quotation': quotation,
                            'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'quotation_url': url_for('quotation.view_quotation', id=quotation.id, _external=True),
                            'current_year': datetime.now().year
                        }
                    )
                    # 通知解决方案经理
                    notify_solution_managers_quotation_created(quotation)
                except Exception as notify_err:
                    logger.warning(f"触发报价单创建通知失败: {str(notify_err)}")
                
                flash('报价单创建成功！', 'success')
                
                # 处理返回URL
                if return_to and 'project/view' in return_to:
                    return redirect(return_to)
                else:
                    return redirect(url_for('quotation.list_quotations'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f'处理POST请求时发生错误: {type(e).__name__}')
            
            # 根据请求类型返回不同的响应
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': f'{type(e).__name__}: {str(e)}'
                }), 500
            else:
                flash(f'报价单创建失败：{str(e)}', 'danger')
                print(f"Error: {str(e)}")  # 添加错误日志
    
    # GET 请求处理
    # 只显示未有报价单的项目
    subquery = db.session.query(Quotation.project_id).distinct()
    projects = get_viewable_data(Project, current_user).filter(~Project.id.in_(subquery)).all()
    
    # 创建一个新的空报价单对象
    quotation = Quotation()
    quotation.details = []
    
    # 如果有预设的项目ID，设置默认选中项目
    selected_project = None
    if preset_project_id:
        selected_project = Project.query.get(preset_project_id)
    
    # 获取产品库中ID为1的产品的货币类型作为默认货币
    from app.models.product import Product
    default_currency = 'CNY'  # 默认为人民币
    try:
        reference_product = Product.query.get(1)
        if reference_product and reference_product.currency:
            default_currency = reference_product.currency
            current_app.logger.debug(f"使用产品ID=1的货币类型作为默认值: {default_currency}")
        else:
            current_app.logger.debug("产品ID=1不存在或没有货币信息，使用默认货币CNY")
    except Exception as e:
        current_app.logger.warning(f"获取默认货币时出错: {str(e)}，使用默认货币CNY")
    
    return render_template('quotation/create.html',
                         projects=projects,
                         today_date=datetime.now().strftime('%Y-%m-%d'),
                         quotation=quotation,
                         preset_project_id=preset_project_id,
                         selected_project=selected_project,
                         return_to=return_to,
                         default_currency=default_currency)

@quotation.route('/get_project/<int:project_id>')
def get_project(project_id):
    try:
        logger.debug(f"获取项目 {project_id} 的信息...")
        project = Project.query.get_or_404(project_id)
        logger.debug(f"项目信息: 阶段={project.current_stage}, 类型={project.project_type}")
        
        # 设置缓存控制头
        response = jsonify({
            'success': True,
            'current_stage': project.current_stage,
            'project_type': project.project_type,
            'project_name': project.project_name,
            'authorization_code': project.authorization_code
        })
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"获取项目信息时出错: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@quotation.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('quotation', 'edit')  # 添加编辑权限装饰器
def edit_quotation(id):
    try:
        quotation = Quotation.query.get_or_404(id)
        
        # 检查编辑权限
        if not can_edit_data(quotation, current_user):
            flash('您没有权限编辑此报价单', 'danger')
            return redirect(url_for('quotation.list_quotations'))
        
        # 检查报价单是否被锁定
        if quotation.is_locked:
            lock_info = quotation.lock_status_display
            flash(f'报价单已被锁定，无法编辑。锁定原因：{lock_info["reason"]}，锁定人：{lock_info["locked_by"]}', 'warning')
            return redirect(url_for('quotation.view_quotation', id=id))
        
        # 按产品库产品ID排序获取报价单明细
        from app.models.product import Product
        from sqlalchemy import case
        
        # 获取排序后的明细
        sorted_details = db.session.query(QuotationDetail)\
            .outerjoin(Product, Product.product_name == QuotationDetail.product_name)\
            .filter(QuotationDetail.quotation_id == quotation.id)\
            .order_by(case((Product.id.is_(None), 1), else_=0), Product.id.asc(), QuotationDetail.id.asc())\
            .all()
        
        # 替换原有的details
        quotation.details = sorted_details
        
        # 处理报价单明细数据
        for detail in quotation.details:
            # 确保total_price映射到subtotal
            detail.subtotal = detail.total_price
            # 确保discount映射到discount_rate（转换为百分比）
            detail.discount_rate = detail.discount * 100 if detail.discount is not None else 100.0
            # 确保正确设置product_mn字段
            if not hasattr(detail, 'product_mn') or detail.product_mn is None:
                # 尝试从产品表中获取MN号
                product = Product.query.filter_by(product_name=detail.product_name, model=detail.product_model).first()
                if product:
                    detail.product_mn = product.product_mn
                else:
                    detail.product_mn = ''
        
        # 准备报价单详情的JSON数据，以便在模板中使用
        quotation_details = []
        for detail in quotation.details:
            quotation_details.append({
                'product_name': detail.product_name,
                'product_model': detail.product_model,
                'product_desc': detail.product_desc,
                'brand': detail.brand,
                'unit': detail.unit,
                'market_price': detail.market_price,
                'discount_rate': detail.discount_rate,
                'unit_price': detail.unit_price,
                'quantity': detail.quantity,
                'subtotal': detail.subtotal,
                'product_mn': detail.product_mn if hasattr(detail, 'product_mn') else ''
            })
        
        quotation_details_json = json.dumps(quotation_details)
        
        # 获取所有项目
        projects = get_viewable_data(Project, current_user).all()
        
        if request.method == 'POST':
            try:
                # 捕获修改前的值
                from app.utils.change_tracker import ChangeTracker
                old_values = ChangeTracker.capture_old_values(quotation)
                
                # 捕获修改前的产品明细签名，用于检测变化
                old_product_signature = quotation.calculate_product_signature()
                
                # 验证必填字段
                if not request.form.get('project_id'):
                    raise ValueError('项目不能为空')
                
                # 获取关联的项目
                project = Project.query.get(request.form.get('project_id'))
                if project:
                    # 更新报价单的项目相关信息
                    quotation.project_id = project.id
                    quotation.project_stage = project.current_stage
                    quotation.project_type = project.project_type
                
                # 更新报价单货币
                currency = request.form.get('currency', 'CNY')
                quotation.currency = currency
                
                event.remove(QuotationDetail, 'after_delete', update_quotation_product_signature)
                
                try:
                    # 先移除旧的明细
                    for detail in quotation.details:
                        db.session.delete(detail)
                    quotation.details.clear()
                    
                    # 获取表单数据
                    product_names = request.form.getlist('product_name[]')
                    product_models = request.form.getlist('product_model[]')
                    product_descs = request.form.getlist('product_spec[]')
                    brands = request.form.getlist('product_brand[]')
                    units = request.form.getlist('product_unit[]')
                    discounts = request.form.getlist('discount_rate[]')
                    market_prices = request.form.getlist('product_price[]')
                    quantities = request.form.getlist('quantity[]')
                    product_mns = request.form.getlist('product_mn[]')  # 添加MN号字段
                    
                    # 获取报价单货币，用于明细记录
                    detail_currency = request.form.get('currency', 'CNY')
                    
                    # 验证是否有产品明细
                    if not product_names:
                        raise ValueError('请至少添加一个产品')
                    
                    # 验证所有列表长度是否一致
                    lists_length = [len(x) for x in [
                        product_names, product_models, product_descs, brands,
                        units, discounts, market_prices, quantities
                    ]]
                    if len(set(lists_length)) > 1:
                        raise ValueError('产品数据不完整，请检查后重试')
                    
                    total_amount = 0.0
                    for i in range(len(product_names)):
                        try:
                            # 验证必填字段
                            if not product_names[i].strip():
                                raise ValueError(f'第 {i+1} 行产品名称不能为空')
                            if not product_models[i].strip():
                                raise ValueError(f'第 {i+1} 行产品型号不能为空')
                            
                            # 清理并验证数值字段
                            try:
                                market_price = float(market_prices[i].replace(',', '') if market_prices[i] else '0')
                                discount = float(discounts[i].replace(',', '') if discounts[i] else '0')
                                quantity = int(quantities[i].replace(',', '') if quantities[i] else '0')
                                
                                if market_price < 0:
                                    raise ValueError(f'第 {i+1} 行市场价格不能为负数')
                                if discount < 0:
                                    raise ValueError(f'第 {i+1} 行折扣率不能为负数')
                                if quantity <= 0:
                                    raise ValueError(f'第 {i+1} 行数量必须大于0')
                            except ValueError as e:
                                if str(e).startswith('第'):
                                    raise e
                                raise ValueError(f'第 {i+1} 行数据格式错误：{str(e)}')
                            
                            # 计算价格
                            discounted_price = market_price * (discount / 100)
                            subtotal = discounted_price * quantity
                            total_amount += subtotal
                            
                            # 创建明细记录
                            detail = QuotationDetail(
                                product_name=product_names[i].strip(),
                                product_model=product_models[i].strip(),
                                product_desc=product_descs[i].strip() if product_descs[i] else None,
                                brand=brands[i].strip() if brands[i] else None,
                                unit=units[i].strip() if units[i] else None,
                                discount=discount/100,
                                market_price=market_price,
                                quantity=quantity,
                                unit_price=discounted_price,
                                total_price=subtotal,
                                product_mn=product_mns[i] if i < len(product_mns) else '',  # 添加MN号
                                currency=detail_currency  # 添加货币字段
                            )
                            
                            # 计算植入小计
                            detail.calculate_prices()
                            
                            quotation.details.append(detail)
                        except Exception as e:
                            raise ValueError(f'处理第 {i+1} 行数据时出错：{str(e)}')
                    
                    # 更新报价单总金额
                    quotation.amount = total_amount
                    # 手动更新时间戳，确保updated_at字段正确
                    quotation.updated_at = datetime.utcnow()
                    
                finally:
                    # 重新注册事件监听器
                    event.listen(QuotationDetail, 'after_insert', update_quotation_product_signature)
                    event.listen(QuotationDetail, 'after_update', update_quotation_product_signature)
                    event.listen(QuotationDetail, 'after_delete', update_quotation_product_signature)
                    
                    # 在重新注册事件监听器后立即进行签名检测和状态处理
                    try:
                        # 检测产品明细是否发生变化
                        new_product_signature = quotation.calculate_product_signature()
                        product_details_changed = old_product_signature != new_product_signature
                        
                        # 如果产品明细发生关键变化，手动清除确认状态
                        if product_details_changed and quotation.confirmation_badge_status == 'confirmed':
                            quotation.confirmation_badge_status = 'none'
                            quotation.confirmation_badge_color = None
                            quotation.confirmed_by = None
                            quotation.confirmed_at = None
                            current_app.logger.info(f"报价单 {quotation.id} 的产品明细发生关键变化（行数或MN号），已手动清除确认状态")
                        
                        # 更新产品签名
                        quotation.product_signature = new_product_signature
                        current_app.logger.debug(f"产品签名更新: {old_product_signature} -> {new_product_signature}, 变化: {product_details_changed}")
                        
                        # 临时再次禁用事件监听器，避免在提交时触发
                        event.remove(QuotationDetail, 'after_insert', update_quotation_product_signature)
                        event.remove(QuotationDetail, 'after_update', update_quotation_product_signature)
                        event.remove(QuotationDetail, 'after_delete', update_quotation_product_signature)
                        
                    except Exception as signature_error:
                        current_app.logger.error(f"处理产品签名和确认状态时出错: {str(signature_error)}")
                
                # 记录变更历史
                try:
                    new_values = ChangeTracker.get_new_values(quotation, old_values.keys())
                    ChangeTracker.log_update(quotation, old_values, new_values)
                except Exception as track_err:
                    current_app.logger.warning(f"记录报价单变更历史失败: {str(track_err)}")
                
                # 强制刷新项目金额
                project = Project.query.get(quotation.project_id)
                if project:
                    total = db.session.query(db.func.sum(Quotation.amount)).filter(Quotation.project_id==project.id).scalar() or 0.0
                    project.quotation_customer = total
                db.session.commit()
                
                flash('报价单更新成功！', 'success')
                return redirect(url_for('quotation.list_quotations'))
                
            except ValueError as e:
                db.session.rollback()
                flash(str(e), 'error')
                return render_template('quotation/edit.html', 
                                     quotation=quotation,
                                     other_projects=projects,
                                     today_date=datetime.now().strftime('%Y-%m-%d'),
                                     quotation_details_json=quotation_details_json)
            except Exception as e:
                db.session.rollback()
                flash(f'报价单更新失败：{str(e)}', 'danger')
                return render_template('quotation/edit.html', 
                                     quotation=quotation,
                                     other_projects=projects,
                                     today_date=datetime.now().strftime('%Y-%m-%d'),
                                     quotation_details_json=quotation_details_json)
        
        # GET请求
        return render_template('quotation/edit.html', 
                            quotation=quotation,
                            other_projects=projects,
                            today_date=datetime.now().strftime('%Y-%m-%d'),
                            quotation_details_json=quotation_details_json)
        
    except Exception as e:
        flash(f'加载报价单失败：{str(e)}', 'danger')
        return redirect(url_for('quotation.list_quotations'))

@quotation.route('/<int:id>/copy', methods=['POST'])
@login_required
@permission_required('quotation', 'create')
def copy_quotation(id):
    try:
        original_quotation = Quotation.query.get_or_404(id)
        if not can_view_quotation(current_user, original_quotation):
            logger.debug(f"{current_user.username} 无权复制报价单 {original_quotation.id}")
            flash('您没有权限复制此报价单', 'danger')
            return redirect(url_for('quotation.list_quotations'))
        # 创建新报价单
        new_quotation = Quotation(
            project_id=original_quotation.project_id,
            contact_id=original_quotation.contact_id,
            project_stage=original_quotation.project_stage,
            project_type=original_quotation.project_type,
            owner_id=current_user.id  # 设置当前用户为所有者
        )
        
        # 复制明细
        for detail in original_quotation.details:
            new_detail = QuotationDetail(
                product_name=detail.product_name,
                product_model=detail.product_model,
                product_desc=detail.product_desc,
                brand=detail.brand,
                unit=detail.unit,
                quantity=detail.quantity,
                discount=detail.discount,
                market_price=detail.market_price,
                unit_price=detail.unit_price,
                total_price=detail.total_price,
                product_mn=detail.product_mn if hasattr(detail, 'product_mn') else ''  # 添加MN号
            )
            
            # 计算植入小计
            new_detail.calculate_prices()
            
            new_quotation.details.append(new_detail)
        
        # 设置总金额
        new_quotation.amount = original_quotation.amount
        
        db.session.add(new_quotation)
        db.session.commit()
        
        # 强制刷新项目金额
        project = Project.query.get(new_quotation.project_id)
        if project:
            total = db.session.query(db.func.sum(Quotation.amount)).filter(Quotation.project_id==project.id).scalar() or 0.0
            project.quotation_customer = total
        db.session.commit()
        
        flash('报价单复制成功！', 'success')
        return redirect(url_for('quotation.edit_quotation', id=new_quotation.id))
    except Exception as e:
        db.session.rollback()
        flash(f'报价单复制失败：{str(e)}', 'danger')
        return redirect(url_for('quotation.list_quotations'))

@quotation.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('quotation', 'delete')
def delete_quotation(id):
    quotation = Quotation.query.get_or_404(id)
    
    # 检查删除权限
    if not can_edit_data(quotation, current_user):
        flash('您没有权限删除此报价单', 'danger')
        return redirect(url_for('quotation.list_quotations'))
    
    try:
        # 记录删除历史
        try:
            from app.utils.change_tracker import ChangeTracker
            ChangeTracker.log_delete(quotation)
        except Exception as track_err:
            current_app.logger.warning(f"记录报价单删除历史失败: {str(track_err)}")
        
        # === 新增：删除报价单审批实例和相关审批记录 ===
        from app.models.approval import ApprovalInstance, ApprovalRecord
        quotation_approvals = ApprovalInstance.query.filter_by(
            object_type='quotation', 
            object_id=id
        ).all()
        
        if quotation_approvals:
            approval_record_count = 0
            for approval in quotation_approvals:
                # 删除审批记录
                records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                approval_record_count += len(records)
                for record in records:
                    db.session.delete(record)
                # 删除审批实例
                db.session.delete(approval)
            
            current_app.logger.info(f"已删除 {len(quotation_approvals)} 个报价单审批实例和 {approval_record_count} 个审批记录")
        
        # === 新增：显式删除报价单明细 ===
        from app.models.quotation import QuotationDetail
        quotation_details = QuotationDetail.query.filter_by(quotation_id=id).all()
        
        if quotation_details:
            for detail in quotation_details:
                db.session.delete(detail)
            current_app.logger.info(f"已删除 {len(quotation_details)} 个报价单明细")
        
        db.session.delete(quotation)
        db.session.commit()
        flash('报价单删除成功！', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('quotation.list_quotations'))

@quotation.route('/batch-delete', methods=['POST'])
@login_required
@permission_required('quotation', 'delete')
def batch_delete_quotations():
    try:
        data = request.get_json()
        quotation_ids = data.get('quotation_ids', [])
        if not quotation_ids:
            return jsonify({'success': False, 'message': '未选择任何报价单'})
        deleted_count = 0
        error_ids = []
        project_ids = set()
        for quotation_id in quotation_ids:
            try:
                quotation = Quotation.query.get(quotation_id)
                if quotation:
                    if can_edit_data(quotation, current_user):
                        # 记录涉及的项目ID
                        if quotation.project_id:
                            project_ids.add(quotation.project_id)
                        
                        # === 新增：删除报价单审批实例和相关审批记录 ===
                        from app.models.approval import ApprovalInstance, ApprovalRecord
                        quotation_approvals = ApprovalInstance.query.filter_by(
                            object_type='quotation', 
                            object_id=quotation_id
                        ).all()
                        
                        if quotation_approvals:
                            for approval in quotation_approvals:
                                # 删除审批记录
                                records = ApprovalRecord.query.filter_by(instance_id=approval.id).all()
                                for record in records:
                                    db.session.delete(record)
                                # 删除审批实例
                                db.session.delete(approval)
                        
                        # === 新增：显式删除报价单明细 ===
                        from app.models.quotation import QuotationDetail
                        quotation_details = QuotationDetail.query.filter_by(quotation_id=quotation_id).all()
                        
                        if quotation_details:
                            for detail in quotation_details:
                                db.session.delete(detail)
                        
                        # 删除报价单
                        db.session.delete(quotation)
                        deleted_count += 1
                    else:
                        logger.warning(f"用户 {current_user.username} 无权删除报价单 {quotation_id}")
                        error_ids.append(quotation_id)
                else:
                    logger.warning(f"报价单 {quotation_id} 不存在")
                    error_ids.append(quotation_id)
            except Exception as item_error:
                logger.error(f"删除报价单 {quotation_id} 时出错: {str(item_error)}")
                error_ids.append(quotation_id)
        
        # 提交删除操作
        db.session.commit()
        
        # 注意：项目金额更新交由SQLAlchemy事件监听器处理，此处无需手动更新
        logger.info(f"批量删除涉及的项目IDs: {project_ids}，将由事件监听器自动更新金额")
        
        return jsonify({'success': True, 'deleted': deleted_count, 'error_ids': error_ids})
    except Exception as e:
        logger.error(f"批量删除报价单时出错: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@quotation.route('/get_project_customers/<int:project_id>')
def get_project_customers(project_id):
    try:
        print(f"开始获取项目 {project_id} 的客户列表...")
        
        # 获取项目
        project = Project.query.get_or_404(project_id)
        print(f"找到项目: {project.project_name}")
        
        # 获取与项目相关的公司
        companies = []
        
        # 添加直接用户公司（如果存在）
        if project.end_user:
            print(f"查找直接用户: {project.end_user}")
            end_user_company = Company.query.filter_by(company_name=project.end_user).first()
            if end_user_company:
                companies.append({
                    'id': end_user_company.id,
                    'name': end_user_company.company_name,
                    'type': '直接用户'
                })
        
        # 添加设计院公司（如果存在）
        if project.design_issues:
            print(f"查找设计院: {project.design_issues}")
            design_company = Company.query.filter_by(company_name=project.design_issues).first()
            if design_company:
                companies.append({
                    'id': design_company.id,
                    'name': design_company.company_name,
                    'type': '设计院'
                })
        
        # 添加总承包单位（如果存在）
        if project.contractor:
            print(f"查找总承包单位: {project.contractor}")
            contractor_company = Company.query.filter_by(company_name=project.contractor).first()
            if contractor_company:
                companies.append({
                    'id': contractor_company.id,
                    'name': contractor_company.company_name,
                    'type': '总承包单位'
                })
        
        # 添加系统集成商（如果存在）
        if project.system_integrator:
            print(f"查找系统集成商: {project.system_integrator}")
            si_company = Company.query.filter_by(company_name=project.system_integrator).first()
            if si_company:
                companies.append({
                    'id': si_company.id,
                    'name': si_company.company_name,
                    'type': '系统集成商'
                })
        
        # 添加经销商（如果存在）
        if project.dealer:
            print(f"查找经销商: {project.dealer}")
            dealer_company = Company.query.filter_by(company_name=project.dealer).first()
            if dealer_company:
                companies.append({
                    'id': dealer_company.id,
                    'name': dealer_company.company_name,
                    'type': '经销商'
                })
        
        # 去除重复项
        unique_companies = []
        company_ids = set()
        for company in companies:
            if company['id'] not in company_ids:
                unique_companies.append(company)
                company_ids.add(company['id'])
        
        print(f"找到 {len(unique_companies)} 个唯一客户")
        for company in unique_companies:
            print(f"- {company['name']} ({company['type']})")
        
        return jsonify({'customers': unique_companies})
    except Exception as e:
        print(f"获取项目客户列表时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

@quotation.route('/get_companies')
def get_companies():
    """获取所有公司列表的API，带权限控制"""
    try:
        print("正在获取所有公司列表...")
        
        # 使用访问控制过滤获取客户
        query = get_viewable_data(Company, current_user)
        
        # 如果有is_deleted字段，添加过滤条件
        if hasattr(Company, 'is_deleted'):
            query = query.filter_by(is_deleted=False)
            print("使用is_deleted过滤条件查询")
        
        companies = query.all()
        
        customers = []
        for company in companies:
            customers.append({
                'id': company.id,
                'name': company.company_name
            })
        
        print(f"成功获取到 {len(customers)} 个公司")
        if customers:
            print(f"公司示例: ID={customers[0]['id']}, 名称={customers[0]['name']}")
        
        return jsonify({'customers': customers})
    except Exception as e:
        print(f"获取公司列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': '获取公司列表失败',
            'message': str(e)
        }), 500

@quotation.route('/get_all_companies')
def get_all_companies():
    """获取所有公司列表的API（保持API兼容性）"""
    # 直接调用get_companies函数，避免代码重复
    return get_companies()

@quotation.route('/get_all_projects')
def get_all_projects():
    try:
        logger.debug("获取所有项目列表...")
        # 获取当前用户权限范围内可见的所有项目（不再限定owner_id）
        projects_query = get_viewable_data(Project, current_user)
        # 移除对已有报价单项目的过滤，因为一个项目可以有多个报价单
        projects = projects_query.all()
        # 构建项目列表，只返回必要的信息
        project_list = [{'id': p.id, 'name': p.project_name} for p in projects]
        logger.debug(f"找到 {len(project_list)} 个项目")
        # 设置缓存控制头
        response = jsonify({'projects': project_list})
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"获取项目列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': '获取项目列表失败',
            'message': str(e)
        }), 500

# 添加产品相关API接口
@quotation.route('/products', methods=['GET'])
def get_products():
    """获取产品列表API"""
    try:
        logger.debug('正在获取产品列表...')
        # 获取搜索词和查询类型
        term = request.args.get('term', '')
        query_type = request.args.get('type', 'search')  # 'search' 或 'exact'
        product_name = request.args.get('product_name', '')
        logger.debug(f'搜索词: {term}, 查询类型: {query_type}, 产品名称: {product_name}')
        
        # 根据查询类型执行不同的查询
        if query_type == 'exact':
            # 精确匹配产品名称
            products = Product.query.filter_by(
                product_name=product_name,
            ).filter(Product.status != '停产').all()
        else:
            # 模糊搜索
            query = Product.query.filter(Product.status != '停产')
            if term:
                search_term = f'%{term}%'
                query = query.filter(
                    db.or_(
                        Product.product_name.ilike(search_term),
                        Product.product_mn.ilike(search_term)
                    )
                )
            products = query.all()
            
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
            
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'type': p.type,
                    'category': p.category,
                    'product_mn': p.product_mn,
                    'product_name': p.product_name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        logger.debug(f'成功处理 {len(result)} 个产品')
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取产品列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品列表失败',
            'message': str(e)
        }), 500

@quotation.route('/products/categories', methods=['GET'])
def get_product_categories():
    """获取去重后的产品类别列表，按每个类别下最小产品ID升序排列"""
    try:
        logger.debug('正在获取产品类别列表...')
        from sqlalchemy import func
        # 查询每个类别下ID最小的产品ID
        min_id_per_category = db.session.query(
            Product.category,
            func.min(Product.id).label('min_id')
        ).filter(Product.status != '停产').group_by(Product.category).all()
        # 按min_id排序
        sorted_categories = sorted(
            [c for c in min_id_per_category if c[0]],
            key=lambda x: x[1]
        )
        category_list = [c[0] for c in sorted_categories]
        logger.debug(f'找到 {len(category_list)} 个类别')
        return jsonify(category_list)
    except Exception as e:
        logger.error(f'获取产品类别列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品类别列表失败',
            'message': str(e)
        }), 500

@quotation.route('/products/by-category', methods=['GET'])
def get_products_by_category():
    """获取指定类别的产品列表"""
    try:
        category = request.args.get('category', '')
        logger.debug(f'正在获取类别 "{category}" 的产品列表...')
        
        if not category:
            return jsonify([])
        
        # 查询指定类别的产品，添加按ID排序
        products = Product.query.filter_by(
            category=category
        ).filter(Product.status != '停产').order_by(Product.id).all()  # 添加按ID排序
        
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'product_name': p.product_name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn,
                    'currency': p.currency or 'CNY'  # 添加货币字段
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}, MN: {p.product_mn}, 货币: {p.currency}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取类别产品列表时出错: {str(e)}')
        return jsonify({
            'error': '获取类别产品列表失败',
            'message': str(e)
        }), 500

@quotation.route('/products/models', methods=['GET'])
def get_product_models():
    """获取指定类别和产品名称的型号列表"""
    try:
        category = request.args.get('category', '')
        product_name = request.args.get('product_name', '')
        logger.debug(f'正在获取产品型号，类别: "{category}", 产品名称: "{product_name}"')
        
        if not category or not product_name:
            return jsonify([])
        
        # 查询指定类别和产品名称的产品
        products = Product.query.filter_by(
            category=category,
            product_name=product_name
        ).filter(Product.status != '停产').order_by(Product.id).all()
        
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'product_name': p.product_name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn,
                    'currency': p.currency or 'CNY'  # 添加货币字段
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}, 型号: {p.model}, 货币: {p.currency}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取产品型号列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品型号列表失败',
            'message': str(e)
        }), 500

@quotation.route('/products/specs', methods=['GET'])
def get_product_specs():
    """获取指定类别、产品名称和型号的规格列表"""
    try:
        category = request.args.get('category', '')
        product_name = request.args.get('product_name', '')
        # 修复：同时支持 product_model 和 model 参数
        product_model = request.args.get('model', '') or request.args.get('product_model', '')
        logger.debug(f'正在获取产品规格，类别: "{category}", 产品名称: "{product_name}", 型号: "{product_model}"')
        
        if not category or not product_name or not product_model:
            return jsonify([])
        
        # 查询指定条件的产品
        products = Product.query.filter_by(
            category=category,
            product_name=product_name,
            model=product_model
        ).filter(Product.status != '停产').order_by(Product.id).all()
        
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = []
        for p in products:
            try:
                # 处理产品图片
                product_image = None
                if hasattr(p, 'image_path') and p.image_path:
                    # 确保图片路径是相对于static目录的
                    if p.image_path.startswith('/static/'):
                        product_image = p.image_path
                    elif p.image_path.startswith('static/'):
                        product_image = '/' + p.image_path
                    else:
                        product_image = '/static/' + p.image_path.lstrip('/')
                
                product_dict = {
                    'id': p.id,
                    'product_name': p.product_name,
                    'model': p.model,  # 修复：使用正确的字段名
                    'specification': p.specification,  # 修复：使用正确的字段名
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn,
                    'currency': p.currency or 'CNY',  # 添加货币字段
                    'image_path': product_image  # 添加图片路径
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}, 规格: {p.specification}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取产品规格列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品规格列表失败',
            'message': str(e)
        }), 500

@quotation.route('/<int:id>/detail')
@login_required
@permission_required_with_approval_context('quotation', 'view')
def view_quotation(id):
    try:
        quotation = Quotation.query.get_or_404(id)
        if not can_view_quotation(current_user, quotation):
            logger.debug(f"{current_user.username} 无权访问报价单 {quotation.id}")
            flash('您没有权限查看此报价单', 'danger')
            return redirect(url_for('quotation.list_quotations'))
        # 项目权限校验 - 使用动态权限检查而不是硬编码角色
        if quotation.project:
            # 统一处理角色字符串，去除空格
            user_role = current_user.role.strip() if current_user.role else ''
            
            # 特殊角色：财务总监、解决方案经理、产品经理可以查看所有项目的报价单
            is_special_role = user_role in ['finance_director', 'finace_director', 'solution_manager', 'solution', 'product_manager', 'product']
            
            # 渠道经理可以查看渠道跟进项目
            is_channel_manager = user_role == 'channel_manager'
            is_channel_project = quotation.project.project_type in ['channel_follow', '渠道跟进']
            
            # 营销总监可以查看销售重点和渠道跟进项目
            is_sales_director = user_role == 'sales_director'
            is_marketing_project = quotation.project.project_type in ['sales_focus', 'channel_follow', '销售重点', '渠道跟进']
            
            # 检查权限：特殊角色 OR (渠道经理 AND 渠道项目) OR (营销总监 AND 营销项目) OR 常规项目权限
            if not (is_special_role or (is_channel_manager and is_channel_project) or (is_sales_director and is_marketing_project) or can_view_project(current_user, quotation.project)):
                logger.debug(f"{current_user.username} 无权访问报价单 {quotation.id} 关联项目 {quotation.project_id}")
                flash('您没有权限查看该报价单关联的项目', 'danger')
                return redirect(url_for('quotation.list_quotations'))
        
        # 按产品库产品ID排序获取报价单明细
        from sqlalchemy import case
        
        # 获取排序后的明细
        sorted_details = db.session.query(QuotationDetail)\
            .outerjoin(Product, Product.product_name == QuotationDetail.product_name)\
            .filter(QuotationDetail.quotation_id == quotation.id)\
            .order_by(case((Product.id.is_(None), 1), else_=0), Product.id.asc(), QuotationDetail.id.asc())\
            .all()
        
        # 替换原有的details
        quotation.details = sorted_details
        
        # 查询可选新拥有人
        from app.models.user import User
        all_users = []
        if can_change_quotation_owner(current_user, quotation):
            from app.permissions import is_admin_or_ceo
            if is_admin_or_ceo():
                all_users = User.query.all()
            elif getattr(current_user, 'is_department_manager', False) or current_user.role == 'sales_director':
                # 部门负责人只能在本部门进行转移
                all_users = User.query.filter(
                    or_(User.role == 'admin', User._is_active == True),
                    User.department == current_user.department
                ).all()
            else:
                # 其他人只能改为自己
                all_users = User.query.filter(User.id.in_([current_user.id, quotation.owner_id])).all()
            if not all_users:
                all_users = User.query.filter(User.id.in_([current_user.id, quotation.owner_id])).all()
        has_change_owner_permission = can_change_quotation_owner(current_user, quotation)
        
        # 生成用户树状数据
        from app.utils.user_helpers import generate_user_tree_data
        user_tree_data = None
        if has_change_owner_permission:
            filter_by_dept = not is_admin_or_ceo()
            user_tree_data = generate_user_tree_data(filter_by_department=filter_by_dept)
        
        # 获取审批实例信息
        approval_instance = get_object_approval_instance('quotation', quotation.id)
        current_approval_step = None
        can_current_user_approve = False
        
        if approval_instance:
            current_approval_step = get_current_step_info(approval_instance)
            can_current_user_approve = can_user_approve(approval_instance.id, current_user.id)
            
        # 检查具体权限
        can_edit_this_quotation = can_edit_data(quotation, current_user)
        from app.utils.access_control import can_delete_quotation
        can_delete_this_quotation = can_delete_quotation(current_user, quotation)
        
        return render_template('quotation/detail.html', 
                             quotation=quotation, 
                             all_users=all_users, 
                             has_change_owner_permission=has_change_owner_permission, 
                             user_tree_data=user_tree_data,
                             approval_instance=approval_instance,
                             current_approval_step=current_approval_step,
                             can_current_user_approve=can_current_user_approve,
                             can_edit_this_quotation=can_edit_this_quotation,
                             can_delete_this_quotation=can_delete_this_quotation)
    except Exception as e:
        flash(f'加载报价单详情失败：{str(e)}', 'danger')
        return redirect(url_for('quotation.list_quotations'))

@quotation.route('/get_quotation_details/<int:id>')
@login_required
def get_quotation_details(id):
    try:
        quotation = Quotation.query.get_or_404(id)
        if not can_view_quotation(current_user, quotation):
            logger.debug(f"{current_user.username} 无权访问报价单 {quotation.id}")
            return jsonify({'success': False, 'error': '无权访问此报价单'}), 403
        # 处理报价单明细数据
        details = []
        detail_errors = []
        
        for detail in quotation.details:
            try:
                # 确保total_price映射到subtotal
                subtotal = detail.total_price if detail.total_price is not None else 0
                # 确保discount映射到discount_rate（转换为百分比）
                discount_rate = detail.discount * 100 if detail.discount is not None else 100.0
                # 确保正确设置product_mn字段
                product_mn = ''
                if hasattr(detail, 'product_mn') and detail.product_mn:
                    product_mn = detail.product_mn
                else:
                    # 尝试从产品表中获取MN号
                    try:
                        product = Product.query.filter_by(product_name=detail.product_name, model=detail.product_model).first()
                        if product:
                            product_mn = product.product_mn
                    except Exception as product_error:
                        current_app.logger.error(f"获取产品MN号失败: {str(product_error)}")
                
                # 安全地转换数值字段
                try:
                    market_price = float(detail.market_price) if detail.market_price is not None else 0
                except (ValueError, TypeError):
                    market_price = 0
                    current_app.logger.error(f"市场价格格式错误: {detail.market_price}")
                
                try:
                    unit_price = float(detail.unit_price) if detail.unit_price is not None else 0
                except (ValueError, TypeError):
                    unit_price = 0
                    current_app.logger.error(f"单价格式错误: {detail.unit_price}")
                
                try:
                    subtotal_value = float(subtotal) if subtotal is not None else 0
                except (ValueError, TypeError):
                    subtotal_value = 0
                    current_app.logger.error(f"小计格式错误: {subtotal}")
                
                detail_data = {
                    'product_name': detail.product_name or '',
                    'product_model': detail.product_model or '',
                    'product_desc': detail.product_desc or '',
                    'brand': detail.brand or '',
                    'unit': detail.unit or '',
                    'market_price': market_price,
                    'discount_rate': float(discount_rate),
                    'quantity': detail.quantity or 1,
                    'product_mn': product_mn
                }
                
                # 如果不是产品经理角色，添加单价和小计字段
                if current_user.role not in ['product_manager', 'product']:
                    detail_data['unit_price'] = unit_price
                    detail_data['subtotal'] = subtotal_value
                
                details.append(detail_data)
            except Exception as detail_error:
                # 记录明细处理错误但继续处理其他明细
                error_message = f"处理报价单明细错误: {str(detail_error)}"
                current_app.logger.error(error_message)
                detail_errors.append(error_message)
        
        # 安全获取总金额
        try:
            total_amount = float(quotation.amount) if quotation.amount is not None else 0
        except (ValueError, TypeError):
            total_amount = 0
            current_app.logger.error(f"总金额格式错误: {quotation.amount}")
        
        response_data = {
            'success': True, 
            'details': details,
            'total_amount': total_amount
        }
        
        # 如果有错误，添加到响应中，但不影响整体成功状态
        if detail_errors:
            response_data['warnings'] = detail_errors
            
        return jsonify(response_data)
    except Exception as e:
        current_app.logger.error(f"获取报价单明细时出错: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@quotation.route('/<int:id>/save', methods=['POST'])
@login_required
@permission_required('quotation', 'edit')  # 添加编辑权限装饰器
def save_quotation(id):
    try:
        quotation = Quotation.query.get_or_404(id)
        
        # 检查编辑权限
        if not can_edit_data(quotation, current_user):
            return jsonify({
                'status': 'error',
                'message': '您没有权限编辑此报价单'
            }), 403
        
        # 检查报价单是否被锁定
        if quotation.is_locked:
            lock_info = quotation.lock_status_display
            return jsonify({
                'status': 'error',
                'message': f'报价单已被锁定，无法编辑。锁定原因：{lock_info["reason"]}，锁定人：{lock_info["locked_by"]}'
            }), 403
        
        # 捕获修改前的值
        from app.utils.change_tracker import ChangeTracker
        old_values = ChangeTracker.capture_old_values(quotation)
        
        # 捕获修改前的产品明细签名，用于检测变化
        old_product_signature = quotation.calculate_product_signature()
        
        # 使用 request.get_json() 获取JSON数据
        data = request.get_json()
        
        # 记录请求数据结构
        current_app.logger.debug(f"请求数据结构: {data.keys() if isinstance(data, dict) else '非字典数据'}")
        
        # 验证数据是否为空
        if not data:
            current_app.logger.error("请求数据为空或格式错误")
            return jsonify({
                'status': 'error',
                'message': '请求数据为空或格式错误'
            }), 400
        
        # 验证项目ID
        if not data.get('project_id'):
            current_app.logger.error("请求数据中缺少project_id字段")
            return jsonify({
                'status': 'error',
                'message': '项目不能为空'
            }), 400
        
        # 日志记录详细的请求数据
        current_app.logger.info(f"项目ID验证 - 请求中的project_id: {data.get('project_id')}, 类型: {type(data.get('project_id'))}")
        
        # 确保项目ID是整数
        try:
            project_id = int(data.get('project_id'))
            current_app.logger.info(f"处理后的project_id: {project_id}")
            
            # 验证项目是否存在
            project = Project.query.get(project_id)
            if not project:
                current_app.logger.error(f"项目ID {project_id} 不存在")
                return jsonify({
                    'status': 'error',
                    'message': f'ID为{project_id}的项目不存在'
                }), 400
                
            # 设置报价单的项目ID
            quotation.project_id = project_id
            current_app.logger.info(f"设置报价单项目ID: {project_id}")
        except (ValueError, TypeError) as e:
            current_app.logger.error(f"项目ID类型转换错误: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': '项目ID格式错误，必须是整数'
            }), 400
        
        # 获取总金额，确保是有效的数值
        try:
            total_amount = float(data.get('total_amount', 0))
            current_app.logger.debug(f'解析到的总金额: {total_amount}')
            
            if total_amount < 0:
                current_app.logger.warning(f"总金额为负数: {total_amount}，已设置为0")
                total_amount = 0
        except (ValueError, TypeError) as amount_error:
            current_app.logger.error(f"解析总金额失败: {str(amount_error)}, 原始值: {data.get('total_amount')}")
            return jsonify({
                'status': 'error',
                'message': f'总金额格式错误: {str(amount_error)}'
            }), 400
        
        # 更新报价单基本信息
        quotation.amount = total_amount
        quotation.currency = data.get('currency', 'CNY')  # 添加货币字段更新
        # 手动更新时间戳，确保updated_at字段正确
        quotation.updated_at = datetime.utcnow()
        current_app.logger.debug(f'更新报价单总金额: {total_amount}, 货币: {quotation.currency}')
        
        # 临时禁用事件监听器，避免删除重建过程中触发不必要的签名变化
        event.remove(QuotationDetail, 'after_insert', update_quotation_product_signature)
        event.remove(QuotationDetail, 'after_update', update_quotation_product_signature)
        event.remove(QuotationDetail, 'after_delete', update_quotation_product_signature)
        
        try:
            # 先删除原有明细项
            try:
                old_details_count = QuotationDetail.query.filter_by(quotation_id=id).count()
                current_app.logger.debug(f'准备删除原有明细项，数量: {old_details_count}')
                
                for detail in quotation.details:
                    db.session.delete(detail)
                quotation.details.clear()
                current_app.logger.debug('成功删除原有明细项')
            except Exception as delete_error:
                current_app.logger.error(f"删除原有明细项失败: {str(delete_error)}")
                return jsonify({
                    'status': 'error',
                    'message': f'删除原有明细项失败: {str(delete_error)}'
                }), 500
            
            # 添加新的明细项
            details = data.get('details', [])
            detail_errors = []
            
            if not details:
                current_app.logger.warning("报价单没有明细项")
                return jsonify({
                    'status': 'error',
                    'message': '报价单必须包含至少一个明细项'
                }), 400
            
            if not isinstance(details, list):
                current_app.logger.error(f'明细项不是列表格式: {type(details)}')
                return jsonify({
                    'status': 'error',
                    'message': '明细项必须是数组格式'
                }), 400
            
            current_app.logger.debug(f'开始处理 {len(details)} 个明细项')
            
            for index, detail in enumerate(details):
                try:
                    current_app.logger.debug(f'处理第 {index+1} 个明细项: {detail}')
                    if not isinstance(detail, dict):
                        error_msg = f"第 {index+1} 行数据格式错误，必须是对象格式"
                        current_app.logger.error(error_msg)
                        detail_errors.append(error_msg)
                        continue
                    # 验证必填字段
                    product_name = detail.get('product_name', '').strip()
                    if not product_name:
                        error_msg = f"第 {index+1} 行产品名称不能为空"
                        current_app.logger.warning(error_msg)
                        detail_errors.append(error_msg)
                        continue
                    # 安全地获取数值字段
                    try:
                        market_price = float(detail.get('market_price', 0))
                        current_app.logger.debug(f'第 {index+1} 行市场价格: {market_price}')
                    except (ValueError, TypeError) as e:
                        market_price = 0
                        error_msg = f"第 {index+1} 行市场价格格式无效"
                        current_app.logger.warning(f"{error_msg}: {str(e)}")
                        detail_errors.append(error_msg)
                    
                    try:
                        discount = float(detail.get('discount_rate', 100)) / 100
                        # 确保折扣率不小于0，不限制上限
                        if discount < 0:
                            error_msg = f"第 {index+1} 行折扣率不能为负数"
                            current_app.logger.warning(error_msg)
                            detail_errors.append(error_msg)
                            discount = 0
                    except (ValueError, TypeError) as e:
                        discount = 1.0
                        error_msg = f"第 {index+1} 行折扣率格式无效，已设为100%"
                        current_app.logger.warning(f"{error_msg}: {str(e)}")
                        detail_errors.append(error_msg)
                    
                    try:
                        quantity = int(detail.get('quantity', 1))
                        current_app.logger.debug(f'第 {index+1} 行数量: {quantity}')
                        
                        if quantity <= 0:
                            quantity = 1
                            error_msg = f"第 {index+1} 行数量必须大于0，已设为1"
                            current_app.logger.warning(error_msg)
                            detail_errors.append(error_msg)
                    except (ValueError, TypeError) as e:
                        quantity = 1
                        error_msg = f"第 {index+1} 行数量格式无效，已设为1"
                        current_app.logger.warning(f"{error_msg}: {str(e)}")
                        detail_errors.append(error_msg)
                    
                    try:
                        unit_price = float(detail.get('unit_price', 0))
                        current_app.logger.debug(f'第 {index+1} 行单价: {unit_price}')
                        
                        if unit_price < 0:
                            unit_price = 0
                            error_msg = f"第 {index+1} 行单价不能为负数，已设为0"
                            current_app.logger.warning(error_msg)
                            detail_errors.append(error_msg)
                    except (ValueError, TypeError) as e:
                        unit_price = 0
                        error_msg = f"第 {index+1} 行单价格式无效，已设为0"
                        current_app.logger.warning(f"{error_msg}: {str(e)}")
                        detail_errors.append(error_msg)
                    
                    try:
                        total_price = float(detail.get('total_price', 0))
                        current_app.logger.debug(f'第 {index+1} 行小计: {total_price}')
                        
                        if total_price < 0:
                            total_price = 0
                            error_msg = f"第 {index+1} 行小计不能为负数，已设为0"
                            current_app.logger.warning(error_msg)
                            detail_errors.append(error_msg)
                    except (ValueError, TypeError) as e:
                        # 如果小计无效，从单价和数量重新计算
                        total_price = unit_price * quantity
                        error_msg = f"第 {index+1} 行小计格式无效，已重新计算为: {total_price}"
                        current_app.logger.warning(f"{error_msg}: {str(e)}")
                        detail_errors.append(error_msg)
                    
                    # 创建新明细
                    new_detail = QuotationDetail(
                        quotation_id=id,
                        product_name=product_name,
                        product_model=detail.get('product_model', ''),
                        product_desc=detail.get('product_desc', ''),
                        brand=detail.get('brand', ''),
                        unit=detail.get('unit', ''),
                        quantity=quantity,
                        discount=discount,
                        market_price=market_price,
                        unit_price=unit_price,
                        total_price=total_price,
                        product_mn=detail.get('product_mn', ''),
                        currency=data.get('currency', 'CNY')  # 添加明细货币字段
                    )
                    current_app.logger.debug(f'创建第 {index+1} 行明细项')
                    quotation.details.append(new_detail)
                except Exception as item_error:
                    error_msg = f"处理第 {index+1} 行明细时出错: {str(item_error)}"
                    current_app.logger.error(error_msg)
                    detail_errors.append(error_msg)
            
            # 在提交前进行签名检测和状态处理
            try:
                # 检测产品明细是否发生变化
                new_product_signature = quotation.calculate_product_signature()
                product_details_changed = old_product_signature != new_product_signature
                
                # 如果产品明细发生关键变化，手动清除确认状态
                if product_details_changed and quotation.confirmation_badge_status == 'confirmed':
                    quotation.confirmation_badge_status = 'none'
                    quotation.confirmation_badge_color = None
                    quotation.confirmed_by = None
                    quotation.confirmed_at = None
                    current_app.logger.info(f"报价单 {quotation.id} 的产品明细发生关键变化（行数或MN号），已手动清除确认状态")
                
                # 更新产品签名
                quotation.product_signature = new_product_signature
                current_app.logger.debug(f"产品签名更新: {old_product_signature} -> {new_product_signature}, 变化: {product_details_changed}")
                
            except Exception as signature_error:
                current_app.logger.error(f"处理产品签名和确认状态时出错: {str(signature_error)}")
            
            # 提交更改（在事件监听器被禁用的情况下）
            try:
                current_app.logger.info('准备提交所有更改到数据库...')
                db.session.commit()
                current_app.logger.info('数据库更改提交成功')
            except Exception as commit_error:
                db.session.rollback()
                error_type = type(commit_error).__name__
                current_app.logger.error(f"提交更改时出错: {error_type} - {str(commit_error)}")
                return jsonify({
                    'status': 'error',
                    'message': f'保存失败: {error_type} - {str(commit_error)}'
                }), 500
                    
        finally:
            # 确保事件监听器在任何情况下都能恢复
            try:
                event.listen(QuotationDetail, 'after_insert', update_quotation_product_signature)
                event.listen(QuotationDetail, 'after_update', update_quotation_product_signature)
                event.listen(QuotationDetail, 'after_delete', update_quotation_product_signature)
                current_app.logger.debug("事件监听器已恢复")
            except Exception as restore_error:
                current_app.logger.error(f"恢复事件监听器时出错: {str(restore_error)}")
        
        # 记录变更历史
        try:
            new_values = ChangeTracker.get_new_values(quotation, old_values.keys())
            ChangeTracker.log_update(quotation, old_values, new_values)
        except Exception as track_err:
            current_app.logger.warning(f"记录报价单变更历史失败: {str(track_err)}")
        
        # 强制刷新项目金额
        try:
            project = Project.query.get(quotation.project_id)
            if project:
                total = db.session.query(db.func.sum(Quotation.amount)).filter(Quotation.project_id==project.id).scalar() or 0.0
                project.quotation_customer = total
            db.session.commit()
        except Exception as project_update_error:
            current_app.logger.warning(f"更新项目金额失败: {str(project_update_error)}")
        
        # 异步触发通知，避免阻塞保存操作
        try:
            from app.utils.notification_helpers import trigger_event_notification
            from flask import url_for
            import threading
            from app.utils.solution_manager_notifications import notify_solution_managers_quotation_created
            
            # 在线程外获取app实例和必要数据
            app = current_app._get_current_object()
            quotation_owner_id = quotation.owner_id
            quotation_id = quotation.id
            
            def send_notifications_async():
                """异步发送通知"""
                with app.app_context():
                    try:
                        # 重新查询quotation对象以获取最新状态
                        fresh_quotation = Quotation.query.get(quotation_id)
                        if fresh_quotation:
                            # 构建URL而不使用url_for
                            quotation_url = f"http://localhost:10000/quotation/{quotation_id}/detail"
                            
                            # 触发报价单更新通知（而不是创建通知）
                            trigger_event_notification(
                                event_key='quotation_updated',
                                target_user_id=quotation_owner_id,
                                context={
                                    'quotation': fresh_quotation,
                                    'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'quotation_url': quotation_url,
                                    'current_year': datetime.now().year
                                }
                            )
                            app.logger.debug('异步事件通知已触发')
                    except Exception as notify_err:
                        app.logger.warning(f"异步触发通知失败: {str(notify_err)}")
            
            # 启动异步通知线程
            threading.Thread(target=send_notifications_async, daemon=True).start()
            current_app.logger.debug('异步通知线程已启动')
            
        except Exception as notify_err:
            current_app.logger.warning(f"启动异步通知失败: {str(notify_err)}")
        
        # 快速返回成功响应
        if detail_errors:
            current_app.logger.warning(f"报价单保存成功，但有以下警告: {', '.join(detail_errors)}")
            response_data = {
                'status': 'success',
                'message': '报价单更新成功',
                'warnings': detail_errors,
                'quotation_id': id
            }
            
            return jsonify(response_data), 200
        
        current_app.logger.info('报价单更新成功，无警告信息')
        response_data = {
            'status': 'success',
            'message': '报价单更新成功',
            'quotation_id': id
        }
        
        return jsonify(response_data)
                
    except Exception as e:
        error_type = type(e).__name__
        current_app.logger.exception(f'处理POST请求时发生错误: {error_type}')
        return jsonify({
            'status': 'error',
            'message': f'{error_type}: {str(e)}'
        }), 500

@quotation.route('/<int:id>/change_owner', methods=['POST'])
@login_required
@permission_required('quotation', 'edit')
def change_quotation_owner(id):
    quotation = Quotation.query.get_or_404(id)
    if not can_change_quotation_owner(current_user, quotation):
        flash('您没有权限修改该报价单的拥有人', 'danger')
        return redirect(url_for('quotation.view_quotation', id=id))
    new_owner_id = request.form.get('new_owner_id', type=int)
    if not new_owner_id:
        flash('请选择新的拥有人', 'danger')
        return redirect(url_for('quotation.view_quotation', id=id))
    from app.models.user import User
    new_owner = User.query.get(new_owner_id)
    if not new_owner:
        flash('新拥有人不存在', 'danger')
        return redirect(url_for('quotation.view_quotation', id=id))
    quotation.owner_id = new_owner_id
    db.session.commit()
    flash('报价单拥有人已更新', 'success')
    return redirect(url_for('quotation.view_quotation', id=id))

def can_view_quotation(user, quotation):
    """
    判断用户是否有权查看该报价单：
    1. 归属人
    2. 厂商负责人（项目的厂商负责人可以查看项目相关的报价单）
    3. 归属链
    4. 渠道经理可以查看渠道跟进项目的报价单
    5. 营销总监可以查看销售重点和渠道跟进项目的报价单
    6. 财务总监、解决方案经理、产品经理可以查看所有报价单
    暂不考虑共享
    """
    if user.role == 'admin':
        return True
    if user.id == quotation.owner_id:
        return True
    
    # 厂商负责人可以查看项目相关的报价单
    if (hasattr(quotation, 'project') and quotation.project and 
        hasattr(quotation.project, 'vendor_sales_manager_id') and 
        quotation.project.vendor_sales_manager_id == user.id):
        return True
    
    # 统一处理角色字符串，去除空格
    user_role = user.role.strip() if user.role else ''
    
    # 财务总监、解决方案经理、产品经理可以查看所有报价单
    if user_role in ['finance_director', 'finace_director', 'solution_manager', 'solution', 'product_manager', 'product']:
        return True
    
    from app.models.user import Affiliation
    affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
    if quotation.owner_id in affiliation_owner_ids:
        return True
        
    # 营销总监特殊处理：可以查看销售重点和渠道跟进项目的报价单
    if user_role == 'sales_director':
        # 获取关联项目
        from app.models.project import Project
        project = Project.query.get(quotation.project_id)
        if project and project.project_type in ['sales_focus', 'channel_follow', '销售重点', '渠道跟进']:
            return True
        
    # 渠道经理特殊处理：可以查看所有渠道跟进项目的报价单
    if user_role == 'channel_manager':
        # 获取关联项目
        from app.models.project import Project
        project = Project.query.get(quotation.project_id)
        if project and project.project_type in ['channel_follow', '渠道跟进']:
            return True
    
    return False

# 已在全局context_processor中注册，此处不再重复注册
# @quotation.app_context_processor
# def inject_permission_funcs():
#     from app.utils.access_control import can_edit_data, can_view_project
#     return dict(
#         can_edit_data=can_edit_data,
#         can_view_project=can_view_project,
#         can_view_quotation=can_view_quotation
#     )

@quotation.route('/detail/<int:detail_id>/toggle_confirmation', methods=['POST'])
@login_required
def toggle_detail_confirmation(detail_id):
    """切换产品明细的确认状态 - 只有解决方案经理和admin可以操作"""
    try:
        # 检查权限
        if current_user.role not in ['solution_manager', 'admin']:
            return jsonify({
                'success': False,
                'message': '权限不足，只有解决方案经理和管理员可以操作确认状态'
            }), 403
        
        # 查找产品明细
        detail = QuotationDetail.query.get_or_404(detail_id)
        
        # 检查报价单是否可编辑（锁定状态检查）
        if detail.quotation.is_locked:
            return jsonify({
                'success': False,
                'message': '报价单已被锁定，无法修改确认状态'
            }), 400
        
        # 暂时使用会话存储确认状态，避免数据库字段依赖
        session_key = f'detail_confirmation_{detail_id}'
        current_status = session.get(session_key, False)
        
        # 切换确认状态
        if current_status:
            # 取消确认
            session[session_key] = False
            action = 'unconfirmed'
            message = '已取消确认'
        else:
            # 确认
            session[session_key] = True
            action = 'confirmed'
            message = '已确认'
        
        return jsonify({
            'success': True,
            'message': message,
            'action': action,
            'is_confirmed': session[session_key],
            'confirmed_by': current_user.real_name or current_user.username,
            'confirmed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'操作失败：{str(e)}'
        }), 500

@quotation.route('/<int:quotation_id>/toggle_product_detail_confirmation', methods=['POST'])
@login_required
def toggle_product_detail_confirmation(quotation_id):
    """切换报价单产品明细的整体确认状态 - 只有解决方案经理和admin可以操作"""
    try:
        # 检查权限
        if current_user.role not in ['solution_manager', 'admin']:
            return jsonify({
                'success': False,
                'message': '权限不足，只有解决方案经理和管理员可以操作确认状态'
            }), 403
        
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查报价单是否可编辑（锁定状态检查）
        if quotation.is_locked:
            return jsonify({
                'success': False,
                'message': '报价单已被锁定，无法修改确认状态'
            }), 400
        
        # 使用数据库确认徽章字段而不是会话存储
        current_status = quotation.confirmation_badge_status == 'confirmed'
        
        # 切换确认状态
        if current_status:
            # 取消确认
            quotation.clear_confirmation_badge()
            action = 'unconfirmed'
            message = '已取消产品明细确认'
        else:
            # 确认 - 使用绿色徽章
            quotation.set_confirmation_badge('#28a745', current_user.id)
            action = 'confirmed'
            message = '已确认产品明细'
        
        # 保存到数据库
        db.session.commit()
        
        # 记录确认信息
        confirmed_by = current_user.real_name or current_user.username
        confirmed_at = quotation.confirmed_at.strftime('%Y-%m-%d %H:%M') if quotation.confirmed_at else None
        
        return jsonify({
            'success': True,
            'message': message,
            'action': action,
            'is_confirmed': quotation.confirmation_badge_status == 'confirmed',
            'confirmed_by': confirmed_by if quotation.confirmation_badge_status == 'confirmed' else None,
            'confirmed_at': confirmed_at if quotation.confirmation_badge_status == 'confirmed' else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'操作失败：{str(e)}'
        }), 500

@quotation.route('/<int:quotation_id>/product_detail_confirmation_status', methods=['GET'])
@login_required
def get_product_detail_confirmation_status(quotation_id):
    """获取报价单产品明细的确认状态"""
    try:
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            return jsonify({
                'success': False,
                'message': '权限不足，无法查看该报价单'
            }), 403
        
        # 从数据库获取确认状态
        is_confirmed = quotation.confirmation_badge_status == 'confirmed'
        
        # 获取确认信息
        confirmed_by = None
        confirmed_at = None
        
        if is_confirmed and quotation.confirmer:
            confirmed_by = quotation.confirmer.real_name or quotation.confirmer.username
            confirmed_at = quotation.confirmed_at.strftime('%Y-%m-%d %H:%M') if quotation.confirmed_at else None
        
        return jsonify({
            'success': True,
            'is_confirmed': is_confirmed,
            'confirmed_by': confirmed_by,
            'confirmed_at': confirmed_at
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取状态失败：{str(e)}'
        }), 500

@quotation.route('/export_pdf/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def export_pdf(quotation_id):
    """导出报价单PDF"""
    try:
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            flash('权限不足，无法导出该报价单', 'danger')
            return redirect(url_for('quotation.list_quotations'))
        
        from app.services.pdf_generator import PDFGenerator
        
        # 生成PDF
        pdf_generator = PDFGenerator()
        pdf_result = pdf_generator.generate_quotation_pdf(quotation)
        pdf_content = pdf_result['content']
        filename = pdf_result['filename']
        
        # 返回PDF文件
        from flask import make_response
        from urllib.parse import quote
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        
        return response
        
    except Exception as e:
        logger.error(f"导出报价单PDF失败: {str(e)}", exc_info=True)
        flash(f'导出PDF失败：{str(e)}', 'danger')
        return redirect(url_for('quotation.view_quotation', id=quotation_id))

@quotation.route('/export_excel/<int:quotation_id>')
@login_required
@permission_required('quotation', 'view')
def export_excel(quotation_id):
    """导出报价单Excel"""
    try:
        # 查找报价单
        quotation = Quotation.query.get_or_404(quotation_id)
        
        # 检查查看权限
        if not can_view_quotation(current_user, quotation):
            flash('权限不足，无法导出该报价单', 'danger')
            return redirect(url_for('quotation.list_quotations'))
        
        from app.services.excel_generator import ExcelGenerator
        
        # 生成Excel
        excel_generator = ExcelGenerator()
        excel_content = excel_generator.generate_quotation_excel(quotation)
        
        # 设置文件名：报价单编号 & 项目名称
        project_name = quotation.project.project_name if quotation.project else "未知项目"
        # 清理文件名中的特殊字符
        safe_project_name = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{quotation.quotation_number} & {safe_project_name}.xlsx"
        
        # 返回Excel文件
        from flask import make_response
        from urllib.parse import quote
        response = make_response(excel_content)
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        
        return response
        
    except Exception as e:
        logger.error(f"导出报价单Excel失败: {str(e)}", exc_info=True)
        flash(f'导出Excel失败：{str(e)}', 'danger')
        return redirect(url_for('quotation.view_quotation', id=quotation_id))
