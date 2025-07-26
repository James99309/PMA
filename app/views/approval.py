from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.permissions import admin_required, has_permission
from app.helpers.approval_helpers import (
    get_user_created_approvals,
    get_user_pending_approvals,
    get_all_approvals,
    get_approval_details,
    get_approval_object_url,
    start_approval_process,
    process_approval,
    process_approval_with_project_type,
    get_template_steps,
    get_approval_records_by_instance,
    get_current_step_info,
    get_last_approver,
    delete_approval_instance,
    can_user_approve,
    get_template_details,
    get_object_type_display,
    _get_field_display_name,
    rollback_order_approval,
    can_rollback_order_approval
)
from app.models.approval import (
    ApprovalStatus, 
    ApprovalAction,
    ApprovalProcessTemplate,
    ApprovalStep,
    ApprovalInstance
)
from app.helpers.project_helpers import lock_project, unlock_project, is_project_editable
from flask import session
import json
from app.utils.access_control import can_start_approval
from app import db
from datetime import datetime

# 创建Blueprint
approval_bp = Blueprint('approval', __name__, url_prefix='/approval')


@approval_bp.route('/center')
@login_required
def center():
    """审批中心视图"""
    try:
        # 基础参数
        tab = request.args.get('tab', 'created')
        object_type = request.args.get('object_type')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 获取统计数据
        from app.helpers.approval_helpers import (
            get_pending_approval_count,
            get_pending_created_count, 
            get_pricing_order_pending_count,
            get_order_pending_count
        )
        
        pending_count = get_pending_approval_count(current_user.id)
        created_pending_count = get_pending_created_count(current_user.id)
        pricing_order_pending_count = get_pricing_order_pending_count(current_user.id)
        order_pending_count = get_order_pending_count(current_user.id)
        
        # 构建通用列表配置
        list_config = build_approval_list_config(
            tab=tab,
            object_type=object_type,
            status=status,
            pending_count=pending_count,
            created_pending_count=created_pending_count,
            pricing_order_pending_count=pricing_order_pending_count,
            order_pending_count=order_pending_count
        )
        
        # 渲染模板
        return render_template(
            'approval/center.html',
            current_tab=tab,
            object_type=object_type,
            status=status,
            pending_count=pending_count,
            created_pending_count=created_pending_count,
            pricing_order_pending_count=pricing_order_pending_count,
            order_pending_count=order_pending_count,
            list_config=list_config
        )
    except Exception as e:
        # 捕获任何错误并显示
        import traceback
        error_detail = traceback.format_exc()
        return f"<h1>Error in approval center:</h1><pre>{error_detail}</pre>", 500



@approval_bp.route('/detail/<int:instance_id>')
@login_required
def detail(instance_id):
    """审批详情视图
    
    显示审批流程的详细信息，包括流程图、当前步骤和所有审批步骤
    """
    # 获取审批实例
    instance = get_approval_details(instance_id)
    
    # 获取对应业务对象的URL
    object_url = get_approval_object_url(instance)
    
    # 获取审批记录和当前步骤信息
    records = get_approval_records_by_instance(instance_id)
    current_step = get_current_step_info(instance) if instance.status == ApprovalStatus.PENDING else None
    
    # 获取所有模板步骤
    all_steps = get_template_steps(instance.process_id)
    
    # 构建完整的审批步骤信息
    completed_step_ids = [record.step_id for record in records]
    
    workflow_steps = []
    for step in all_steps:
        # 获取审批人真实姓名
        approver_name = step.approver.real_name if step.approver and hasattr(step.approver, 'real_name') and step.approver.real_name else step.approver.username if step.approver else '未指定'
        
        step_info = {
            'id': step.id,
            'name': step.step_name,
            'order': step.step_order,
            'approver': approver_name,
            'is_completed': step.id in completed_step_ids,
            'is_current': current_step and current_step.id == step.id,
        }
        
        # 查找对应的审批记录
        for record in records:
            if record.step_id == step.id:
                step_info['action'] = record.action
                step_info['comment'] = record.comment
                step_info['timestamp'] = record.timestamp
                break
                
        workflow_steps.append(step_info)
    
    # 导入工具函数
    from app.utils.dictionary_helpers import project_type_label, project_stage_label
    from app.models.project import Project
    
    # 获取项目数据的辅助函数
    def get_project_by_id(project_id):
        return Project.query.get(project_id)
    
    # 获取报价单数据的辅助函数
    def get_quotation_by_id(quotation_id):
        from app.models.quotation import Quotation
        return Quotation.query.get(quotation_id)
    
    # 渲染审批详情模板
    return render_template(
        'approval/detail.html',
        instance=instance,
        records=records,
        current_step=current_step,
        workflow_steps=workflow_steps,
        object_url=object_url,
        ApprovalStatus=ApprovalStatus,
        total_steps=len(all_steps),
        # 添加工具函数到模板上下文
        project_type_label=project_type_label,
        project_stage_label=project_stage_label,
        get_project_by_id=get_project_by_id,
        get_quotation_by_id=get_quotation_by_id
    )


@approval_bp.route('/start', methods=['POST'])
@login_required
def start_approval():
    """发起审批流程
    
    从业务对象详情页调用，创建新的审批实例
    """
    # 获取表单数据
    object_type = request.form.get('object_type')
    object_id = request.form.get('object_id', type=int)
    template_id = request.form.get('template_id', type=int)
    
    # 参数验证
    if not all([object_type, object_id, template_id]):
        flash('参数不完整，无法发起审批', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 获取业务对象并检查权限
    business_obj = None
    if object_type == 'project':
        from app.models.project import Project
        business_obj = Project.query.get(object_id)
    elif object_type == 'quotation':
        from app.models.quotation import Quotation
        business_obj = Quotation.query.get(object_id)
    elif object_type == 'customer':
        from app.models.customer import Company
        business_obj = Company.query.filter_by(id=object_id, is_deleted=False).first()
    
    if not business_obj:
        flash(f'找不到业务对象: {object_type}:{object_id}', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 检查发起审批的权限
    if not can_start_approval(business_obj, current_user):
        flash('您没有权限发起此审批流程', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 获取审批流程模板
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        flash('审批流程模板不存在', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 检查模板是否适用于当前业务对象类型
    if template.object_type != object_type:
        flash(f'审批模板不适用于当前业务类型: {object_type}', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 获取业务对象的特定类型信息
    business_type = None
    if object_type == 'project':
        business_type = business_obj.project_type
    
    # 检查是否包含授权编号步骤
    has_authorization_step = any(
        step.action_type == 'authorization' 
        for step in ApprovalStep.query.filter_by(process_id=template_id).all()
        if hasattr(step, 'action_type') and step.action_type
    )
    
    # 检查必填字段是否已填写
    missing_fields = []
    if hasattr(template, 'required_fields') and template.required_fields and len(template.required_fields) > 0:
        # 根据业务对象类型获取对象
        if object_type == 'project':
            from app.models.project import Project
            obj = Project.query.get(object_id)
        elif object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(object_id)
        elif object_type == 'customer':
            from app.models.customer import Company
            obj = Company.query.filter_by(id=object_id, is_deleted=False).first()
        else:
            obj = None
        
        if not obj:
            flash(f'找不到业务对象: {object_type}:{object_id}', 'danger')
            return redirect(request.referrer or url_for('index'))
        
        # 检查每个必填字段
        for field in template.required_fields:
            if hasattr(obj, field):
                field_value = getattr(obj, field)
                if field_value is None or field_value == '' or (isinstance(field_value, list) and len(field_value) == 0):
                    field_display = _get_field_display_name(field)
                    missing_fields.append({'code': field, 'name': field_display})
            else:
                current_app.logger.warning(f"业务对象 {object_type} 没有字段 {field}")
                field_display = _get_field_display_name(field)
                missing_fields.append({'code': field, 'name': field_display})
        
        if missing_fields:
            # 构建错误信息JSON并传递给前端
            missing_fields_json = json.dumps(missing_fields)
            readable_fields = [field['name'] for field in missing_fields]
            error_msg = f"发起审批失败: 以下字段必填但未填写: {', '.join(readable_fields)}"
            flash(error_msg, 'danger')
            
            # 将缺失字段信息保存到会话中，以便前端能够高亮显示
            session['missing_fields'] = missing_fields_json
            session['failed_approval_template_id'] = template_id
            
            # 重定向回业务对象详情页
            if object_type == 'project':
                return redirect(url_for('project.view_project', project_id=object_id, missing_fields=missing_fields_json))
            elif object_type == 'quotation':
                return redirect(url_for('quotation.view_quotation', id=object_id, missing_fields=missing_fields_json))
            elif object_type == 'customer':
                return redirect(url_for('customer.view_company', company_id=object_id, missing_fields=missing_fields_json))
            else:
                return redirect(url_for('index'))
    
    # 如果是项目类型且包含授权步骤，先锁定项目
    if object_type == 'project' and has_authorization_step:
        lock_result = lock_project(
            project_id=object_id, 
            reason=f"授权编号审批锁定: {template.name}",
            user_id=current_user.id
        )
        if not lock_result:
            flash('无法锁定项目，可能已被其他流程锁定', 'warning')
            # 继续处理，因为锁定失败可能是由于项目已经被锁定
    
    # 创建审批实例
    instance = start_approval_process(object_type, object_id, template_id, user_id=current_user.id)
    
    if instance:
        flash('审批流程已成功发起', 'success')
        # 重定向到审批详情页面，显示完整的审批流程图
        return redirect(url_for('approval.detail', instance_id=instance.id))
    else:
        # 如果创建失败且项目已锁定，则解锁项目
        if object_type == 'project' and has_authorization_step:
            unlock_project(object_id, current_user.id)
        flash('发起审批失败，请检查是否已存在审批流程或模板是否有效', 'danger')
    
    # 重定向回业务对象详情页
    if object_type == 'project':
        return redirect(url_for('project.view_project', project_id=object_id))
    elif object_type == 'quotation':
        return redirect(url_for('quotation.view_quotation', id=object_id))
    elif object_type == 'customer':
        return redirect(url_for('customer.view_company', company_id=object_id))
    else:
        return redirect(url_for('index'))


@approval_bp.route('/approve/<int:instance_id>', methods=['POST'])
@login_required
def approve(instance_id):
    """处理审批
    
    处理用户对审批实例的同意/拒绝操作
    """
    # 获取表单数据
    action_value = request.form.get('action')
    comment = request.form.get('comment', '')
    project_type = request.form.get('project_type')  # 获取项目类型，如果有的话
    
    # 调试：记录请求头信息
    current_app.logger.info(f"审批请求 - 请求头: {dict(request.headers)}")
    current_app.logger.info(f"审批请求 - Content-Type: {request.headers.get('Content-Type')}")
    current_app.logger.info(f"审批请求 - X-Requested-With: {request.headers.get('X-Requested-With')}")
    current_app.logger.info(f"审批请求 - X-CSRFToken存在: {'X-CSRFToken' in request.headers}")
    current_app.logger.info(f"审批请求 - Accept: {request.headers.get('Accept')}")
    
    # 检查是否是AJAX请求 - 修复检测逻辑
    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        'X-CSRFToken' in request.headers or
        request.is_json or
        request.headers.get('Accept', '').find('application/json') != -1
    )
    
    current_app.logger.info(f"审批请求 - 检测为AJAX: {is_ajax}")
    
    # 参数验证
    if not action_value or action_value not in ('approve', 'reject'):
        if is_ajax:
            return jsonify({
                'success': False,
                'message': '无效的审批操作'
            }), 400
        flash('无效的审批操作', 'danger')
        return redirect(request.referrer or url_for('approval.center'))
    
    # 转换为枚举值
    if action_value == 'approve':
        action = ApprovalAction.APPROVE
    else:
        action = ApprovalAction.REJECT
    
    # 获取审批实例，检查当前步骤是否是授权步骤
    instance = ApprovalInstance.query.get(instance_id)
    if not instance:
        if is_ajax:
            return jsonify({
                'success': False,
                'message': '找不到审批实例'
            }), 404
        flash('找不到审批实例', 'danger')
        return redirect(url_for('approval.center'))
    
    current_step = get_current_step_info(instance)
    is_authorization_step = (
        current_step and 
        hasattr(current_step, 'action_type') and 
        current_step.action_type == 'authorization'
    )
    
    try:
        # 执行审批操作，如果是授权步骤并且提供了项目类型，则传递项目类型
        from app.helpers.approval_helpers import process_approval as helper_process_approval
        
        if is_authorization_step and project_type and instance.object_type == 'project':
            success = helper_process_approval(instance_id, action, comment, project_type=project_type)
        else:
            success = helper_process_approval(instance_id, action, comment)
        
        if success:
            if action == ApprovalAction.APPROVE:
                success_message = '已同意此审批'
                # 记录日志
                current_app.logger.info(f"用户 {current_user.username} 同意了审批 {instance_id}")
                # 如果是最后一步和授权步骤，显示授权成功信息
                if instance.object_type == 'project' and is_authorization_step:
                    from app.models.project import Project
                    project = Project.query.get(instance.object_id)
                    if project and project.authorization_code:
                        success_message += f'，已成功生成授权编号: {project.authorization_code}'
                        current_app.logger.info(f"为项目 {project.id} 生成授权编号: {project.authorization_code}")
            else:
                success_message = '已拒绝此审批'
                current_app.logger.info(f"用户 {current_user.username} 拒绝了审批 {instance_id}")
            
            if is_ajax:
                current_app.logger.info(f"返回JSON响应: {success_message}")
                return jsonify({
                    'success': True,
                    'message': success_message
                })
            flash(success_message, 'success' if action == ApprovalAction.APPROVE else 'warning')
        else:
            error_message = '处理审批失败，请检查您是否有权限或该审批是否有效'
            current_app.logger.error(f"用户 {current_user.username} 处理审批 {instance_id} 失败")
            
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': error_message
                }), 400
            flash(error_message, 'danger')
            
    except Exception as e:
        error_message = f'处理审批时发生错误: {str(e)}'
        current_app.logger.error(f"用户 {current_user.username} 处理审批 {instance_id} 时发生异常: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        if is_ajax:
            return jsonify({
                'success': False,
                'message': error_message
            }), 500
        flash(error_message, 'danger')
    
    # 对于非AJAX请求，返回到审批详情页面
    current_app.logger.info(f"返回重定向响应到审批详情页面")
    return redirect(url_for('approval.detail', instance_id=instance_id))


@approval_bp.route('/api/template-steps/<int:template_id>')
def get_template_steps_api(template_id):
    """API端点：获取审批模板的步骤信息
    
    Returns:
        JSON格式的模板步骤信息
    """
    try:
        # 获取模板信息
        template = ApprovalProcessTemplate.query.get(template_id)
        if not template:
            return jsonify({
                'success': False,
                'message': '未找到模板'
            }), 404
            
        # 获取模板步骤
        steps = get_template_steps(template_id)
        if not steps:
            return jsonify({
                'success': False,
                'message': '该模板没有配置步骤'
            }), 404
        
        # 转换为JSON格式
        steps_data = []
        for step in steps:
            steps_data.append({
                'id': step.id,
                'step_order': step.step_order,
                'step_name': step.step_name,
                'approver_id': step.approver_user_id,
                'approver_name': step.approver.username if step.approver else '未指定',
                'send_email': step.send_email
            })
        
        # 构建模板信息，确保包含required_fields字段
        required_fields = []
        if hasattr(template, 'required_fields') and template.required_fields:
            # 确保处理JSON字符串或已经是列表的情况
            if isinstance(template.required_fields, str):
                try:
                    required_fields = json.loads(template.required_fields)
                except:
                    current_app.logger.error(f"解析required_fields失败: {template.required_fields}")
                    required_fields = []
            else:
                required_fields = template.required_fields
        
        template_data = {
            'id': template.id,
            'name': template.name,
            'object_type': template.object_type,
            'required_fields': required_fields
        }
        
        # 将字段转换为可读名称
        field_display_names = {}
        for field in required_fields:
            field_display_names[field] = _get_field_display_name(field)
        
        return jsonify({
            'success': True,
            'steps': steps_data,
            'template': template_data,
            'field_display_names': field_display_names
        })
    except Exception as e:
        current_app.logger.error(f"获取模板步骤出错: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取模板步骤出错: {str(e)}'
        }), 500 


@approval_bp.route('/api/check-required-fields', methods=['POST'])
def check_required_fields_api():
    """API端点：检查业务对象是否已填写必填字段
    
    Returns:
        JSON格式的字段检查结果
    """
    try:
        # 获取请求数据
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
            
        object_type = data.get('object_type')
        object_id = data.get('object_id')
        required_fields = data.get('required_fields', [])
        
        if not all([object_type, object_id]) or not isinstance(required_fields, list):
            return jsonify({
                'success': False,
                'message': '参数不完整或格式错误'
            }), 400
            
        # 根据业务对象类型获取对象
        if object_type == 'project':
            from app.models.project import Project
            obj = Project.query.get(object_id)
        elif object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(object_id)
        elif object_type == 'customer':
            from app.models.customer import Company
            obj = Company.query.filter_by(id=object_id, is_deleted=False).first()
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的业务对象类型: {object_type}'
            }), 400
        
        if not obj:
            return jsonify({
                'success': False,
                'message': f'找不到业务对象: {object_type}:{object_id}'
            }), 404
        
        # 检查每个必填字段
        missing_fields = []
        for field in required_fields:
            if hasattr(obj, field):
                field_value = getattr(obj, field)
                if field_value is None or field_value == '' or (isinstance(field_value, list) and len(field_value) == 0):
                    missing_fields.append(field)
            else:
                current_app.logger.warning(f"业务对象 {object_type} 没有字段 {field}")
                missing_fields.append(field)
        
        # 转换字段名为可读名称
        missing_fields_display = []
        for field in missing_fields:
            display_name = _get_field_display_name(field)
            missing_fields_display.append({
                'code': field,
                'name': display_name
            })
        
        return jsonify({
            'success': True,
            'missing_fields': missing_fields,
            'missing_fields_display': missing_fields_display,
            'is_valid': len(missing_fields) == 0
        })
    except Exception as e:
        current_app.logger.error(f"检查必填字段出错: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'检查必填字段出错: {str(e)}'
        }), 500


@approval_bp.route('/delete/<int:instance_id>', methods=['POST'])
@login_required
@admin_required
def delete_approval(instance_id):
    """删除审批实例
    
    仅管理员可以删除审批实例
    """
    # 获取审批实例信息
    instance = get_approval_details(instance_id)
    if not instance:
        flash('找不到审批实例', 'danger')
        return redirect(url_for('approval.center'))
    
    # 获取原业务对象的URL
    object_url = get_approval_object_url(instance)
    
    # 执行删除操作
    result = delete_approval_instance(instance_id)
    
    if result:
        flash('审批实例已成功删除', 'success')
    else:
        flash('删除审批实例失败', 'danger')
    
    # 返回到审批中心
    return redirect(url_for('approval.center'))


@approval_bp.route('/api/preview-authorization-code', methods=['POST'])
def preview_authorization_code():
    """API端点：预览项目授权编号
    
    根据项目类型预览可能生成的授权编号格式
    """
    project_type = request.json.get('project_type')
    if not project_type:
        return jsonify({'success': False, 'message': '未提供项目类型'}), 400
    
    # 将项目类型映射为中文
    from app.utils.dictionary_helpers import project_type_label
    from app.utils.i18n import get_current_language
    lang_code = get_current_language()
    project_type_zh = project_type_label(project_type, lang_code)
    
    # 从utils中获取前缀
    from app.utils.authorization import PROJECT_TYPE_PREFIXES
    prefix = PROJECT_TYPE_PREFIXES.get(project_type_zh)
    
    if not prefix:
        return jsonify({'success': False, 'message': '无效的项目类型'}), 400
    
    # 构建预览格式（不实际生成，避免数据库查询）
    year_month = datetime.now().strftime('%Y%m')
    preview_code = f"{prefix}{year_month}-001"
    
    return jsonify({
        'success': True, 
        'preview_code': preview_code,
        'prefix': prefix,
        'year_month': year_month
    })


@approval_bp.route('/authorize/<int:instance_id>', methods=['GET'])
@login_required
def authorize(instance_id):
    """显示授权编号审批页面
    
    仅对含有authorization动作的步骤显示特殊界面
    """
    instance = ApprovalInstance.query.get_or_404(instance_id)
    
    # 检查当前用户是否可以审批
    if not can_user_approve(instance_id):
        flash('您没有权限进行此审批操作', 'danger')
        return redirect(url_for('approval.detail', instance_id=instance_id))
    
    # 获取当前步骤信息
    current_step = get_current_step_info(instance)
    
    # 检查是否是授权步骤
    if not (hasattr(current_step, 'action_type') and current_step.action_type == 'authorization'):
        # 如果不是授权步骤，重定向到普通审批页面
        return redirect(url_for('approval.detail', instance_id=instance_id))
    
    # 确认是项目类型
    if instance.object_type != 'project':
        flash('此授权步骤仅适用于项目', 'warning')
        return redirect(url_for('approval.detail', instance_id=instance_id))
    
    # 获取项目信息
    from app.models.project import Project
    project = Project.query.get(instance.object_id)
    if not project:
        flash('找不到相关项目', 'danger')
        return redirect(url_for('approval.center'))
    
    # 获取项目类型选项
    from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS, project_type_label
    
    # 获取当前日期信息，用于预览
    today = datetime.now()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    
    # 获取项目类型对应的前缀
    from app.utils.authorization import PROJECT_TYPE_PREFIXES
    
    # 生成当前类型的预览授权编号 
    from app.utils.i18n import get_current_language
    lang_code = get_current_language()
    
    project_type_zh = project_type_label(project.project_type, lang_code) if project.project_type else ''
    prefix = PROJECT_TYPE_PREFIXES.get(project_type_zh, '')
    preview_code = f"{prefix}{year}{month}-001" if prefix else ''
    
    # 为模板传递当前项目类型的中文显示名称
    current_project_type_display = project_type_label(project.project_type, lang_code) if project.project_type else project.project_type
    
    return render_template('approval/authorization_step.html',
                          instance=instance,
                          project=project,
                          project_types=PROJECT_TYPE_LABELS,
                          type_prefixes=PROJECT_TYPE_PREFIXES,
                          today_date=today.strftime('%Y-%m-%d'),
                          year=year,
                          month=month,
                          prefix=prefix,
                          preview_code=preview_code,
                          current_project_type_display=current_project_type_display)


@approval_bp.route('/quotation/<int:quotation_id>/approve', methods=['POST'])
@login_required
def approve_quotation(quotation_id):
    """报价审核API - 对指定报价单进行审核操作"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
            
        action = data.get('action')  # approve 或 reject
        comment = data.get('comment', '')
        
        if action not in ['approve', 'reject']:
            return jsonify({'success': False, 'message': '无效的审核动作'}), 400
        
        # 获取报价单
        from app.models.quotation import Quotation
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return jsonify({'success': False, 'message': '报价单不存在'}), 404
        
        # 检查用户权限 - 只有管理员和有审批权限的用户可以执行审核
        from app.permissions import has_permission
        if not (has_permission('quotation', 'admin') or has_permission('quotation_approval', 'create')):
            return jsonify({'success': False, 'message': '无权限执行审核操作'}), 403
        
        # 获取项目当前阶段
        project_stage = quotation.project.current_stage if quotation.project else None
        if not project_stage:
            return jsonify({'success': False, 'message': '项目阶段未设置，无法执行审核'}), 400
        
        # 检查是否已经在该阶段获得审核
        from app.models.quotation import QuotationApprovalStatus
        target_approval_status = QuotationApprovalStatus.STAGE_TO_APPROVAL.get(project_stage)
        if not target_approval_status:
            return jsonify({'success': False, 'message': f'项目阶段 {project_stage} 不支持审核'}), 400
        
        # 检查是否已经通过该阶段审核
        if quotation.approved_stages and target_approval_status in quotation.approved_stages:
            return jsonify({'success': False, 'message': f'该报价单已在 {project_stage} 阶段获得审核，不允许重复审核'}), 400
        
        # 执行审核操作
        if action == 'approve':
            # 通过审核
            quotation.approval_status = target_approval_status
            
            # 添加到已审核阶段列表
            if not quotation.approved_stages:
                quotation.approved_stages = []
            quotation.approved_stages.append(target_approval_status)
            
            # 添加审核历史
            if not quotation.approval_history:
                quotation.approval_history = []
            quotation.approval_history.append({
                'action': 'approve',
                'stage': project_stage,
                'approval_status': target_approval_status,
                'approver_id': current_user.id,
                'approver_name': current_user.username,
                'comment': comment,
                'timestamp': datetime.now().isoformat()
            })
            
            # 添加待确认徽章（新增逻辑）
            quotation.set_pending_confirmation_badge()
            
            message = f'报价单已通过 {QuotationApprovalStatus.APPROVAL_STATUS_LABELS.get(target_approval_status, {}).get("zh", target_approval_status)} 审核'
            
        else:  # action == 'reject'
            # 拒绝审核
            quotation.approval_status = QuotationApprovalStatus.REJECTED
            
            # 添加审核历史
            if not quotation.approval_history:
                quotation.approval_history = []
            quotation.approval_history.append({
                'action': 'reject',
                'stage': project_stage,
                'approver_id': current_user.id,
                'approver_name': current_user.username,
                'comment': comment,
                'timestamp': datetime.now().isoformat()
            })
            
            message = '报价单审核被拒绝'
        
        # 保存到数据库
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message,
            'approval_status': quotation.approval_status
        })
        
    except Exception as e:
        current_app.logger.error(f"报价审核操作失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        from app import db
        db.session.rollback()
        return jsonify({'success': False, 'message': f'审核操作失败: {str(e)}'}), 500


@approval_bp.route('/quotation/<int:quotation_id>/approval-status', methods=['GET'])
@login_required  
def get_quotation_approval_status(quotation_id):
    """获取报价单审核状态API"""
    try:
        # 获取报价单
        from app.models.quotation import Quotation
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return jsonify({'success': False, 'message': '报价单不存在'}), 404
        
        # 获取项目当前阶段
        project_stage = quotation.project.current_stage if quotation.project else None
        
        # 检查当前阶段是否可以审核
        from app.models.quotation import QuotationApprovalStatus
        target_approval_status = QuotationApprovalStatus.STAGE_TO_APPROVAL.get(project_stage) if project_stage else None
        can_approve_current_stage = (
            project_stage and 
            target_approval_status and 
            (not quotation.approved_stages or target_approval_status not in quotation.approved_stages)
        )
        
        # 检查用户权限
        from app.permissions import has_permission
        can_user_approve = has_permission('quotation', 'admin') or has_permission('quotation_approval', 'create')
        
        return jsonify({
            'success': True,
            'quotation_id': quotation_id,
            'approval_status': quotation.approval_status,
            'approved_stages': quotation.approved_stages or [],
            'approval_history': quotation.approval_history or [],
            'project_stage': project_stage,
            'target_approval_status': target_approval_status,
            'can_approve_current_stage': can_approve_current_stage,
            'can_user_approve': can_user_approve
        })
        
    except Exception as e:
        current_app.logger.error(f"获取报价审核状态失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取审核状态失败: {str(e)}'}), 500 


@approval_bp.route('/batch-delete', methods=['POST'])
@login_required
def batch_delete():
    """批量删除审批流程
    
    只有管理员或审批发起人可以删除审批流程
    """
    approval_ids = request.form.getlist('approval_ids')
    
    if not approval_ids:
        flash('请选择要删除的审批流程', 'warning')
        return redirect(url_for('approval.center'))
    
    try:
        deleted_count = 0
        failed_count = 0
        
        for approval_id in approval_ids:
            try:
                # 检查是否是批价单ID（格式：po_123）
                if approval_id.startswith('po_'):
                    # 处理批价单删除
                    pricing_order_id = int(approval_id.split('_')[1])
                    from app.models.pricing_order import PricingOrder
                    pricing_order = PricingOrder.query.get(pricing_order_id)
                    
                    if not pricing_order:
                        failed_count += 1
                        continue
                    
                    # 检查权限：只有管理员或发起人可以删除
                    if current_user.role != 'admin' and pricing_order.created_by != current_user.id:
                        failed_count += 1
                        continue
                    
                    # 删除批价单（只允许删除草稿状态的批价单）
                    if pricing_order.status == 'draft':
                        db.session.delete(pricing_order)
                        deleted_count += 1
                    else:
                        failed_count += 1
                        continue
                        
                else:
                    # 处理通用审批实例删除
                    instance = ApprovalInstance.query.get(int(approval_id))
                    if not instance:
                        failed_count += 1
                        continue
                    
                    # 检查权限：只有管理员或发起人可以删除
                    if current_user.role != 'admin' and instance.creator_id != current_user.id:
                        failed_count += 1
                        continue
                    
                    # 删除审批实例
                    delete_approval_instance(instance.id)
                    deleted_count += 1
                
            except Exception as e:
                current_app.logger.error(f"删除审批流程 {approval_id} 失败: {str(e)}")
                failed_count += 1
        
        # 统一提交数据库事务
        if deleted_count > 0:
            db.session.commit()
        
        # 显示结果消息
        if deleted_count > 0:
            flash(f'成功删除 {deleted_count} 个审批流程', 'success')
        
        if failed_count > 0:
            flash(f'{failed_count} 个审批流程删除失败（权限不足或不存在）', 'warning')
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量删除审批流程失败: {str(e)}")
        flash('批量删除操作失败，请稍后重试', 'danger')
    
    return redirect(url_for('approval.center')) 


@approval_bp.route('/process/<int:instance_id>', methods=['POST'])
@login_required
def process_approval(instance_id):
    """处理审批 - JSON API版本
    
    用于支持前端AJAX请求的审批处理
    """
    try:
        # 获取JSON数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'})
        
        action = data.get('action')
        comment = data.get('comment', '')
        
        if action not in ['approve', 'reject']:
            return jsonify({'success': False, 'message': '无效的操作类型'})
        
        # 获取审批实例
        instance = ApprovalInstance.query.get_or_404(instance_id)
        
        # 检查用户权限
        if not can_user_approve(instance_id, current_user.id):
            return jsonify({'success': False, 'message': '您没有权限审批此流程'})
        
        # 检查是否是授权步骤
        current_step = get_current_step_info(instance)
        is_authorization_step = (
            current_step and 
            hasattr(current_step, 'action_type') and 
            current_step.action_type == 'authorization'
        )
        
        # 处理审批
        approval_action = ApprovalAction.APPROVE if action == 'approve' else ApprovalAction.REJECT
        success = process_approval_with_project_type(
            instance_id, 
            approval_action,
            project_type=None,
            comment=comment,
            user_id=current_user.id
        )
        
        if success:
            message = '审批通过' if action == 'approve' else '审批拒绝'
            
            # 如果是项目授权步骤，添加授权信息
            if instance.object_type == 'project' and is_authorization_step and action == 'approve':
                from app.models.project import Project
                project = Project.query.get(instance.object_id)
                if project and project.authorization_code:
                    message += f'，已生成授权编号: {project.authorization_code}'
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': '审批处理失败，请检查您的权限或审批状态'})
            
    except Exception as e:
        current_app.logger.error(f"处理审批请求失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': '服务器错误，请稍后重试'}), 500


@approval_bp.route('/test-links')
@login_required
def test_links():
    """测试审批链接生成"""
    return render_template('test_approval_links.html') 


@approval_bp.route('/test-center-links')
@login_required
def test_center_links():
    """测试审批中心链接生成"""
    return render_template('test_approval_center.html') 


@approval_bp.route('/recall/<int:instance_id>', methods=['POST'])
@login_required
def recall_approval(instance_id):
    """召回审批流程
    
    只有发起人可以召回正在进行中的审批流程
    """
    try:
        # 获取审批实例
        instance = ApprovalInstance.query.get_or_404(instance_id)
        
        # 检查权限：只有发起人可以召回
        if current_user.id != instance.created_by:
            return jsonify({'success': False, 'message': '只有发起人可以召回审批流程'}), 403
        
        # 检查状态：只有进行中的审批可以召回
        if instance.status != ApprovalStatus.PENDING:
            return jsonify({'success': False, 'message': '只有进行中的审批流程可以召回'}), 400
        
        # 获取召回原因
        data = request.get_json()
        reason = data.get('reason', '') if data else ''
        
        # 更新审批实例状态
        instance.status = ApprovalStatus.REJECTED
        instance.ended_at = datetime.now()
        
        # 获取当前步骤ID（用于记录是在哪个步骤被召回的）
        current_step = get_current_step_info(instance)
        current_step_id = current_step.id if current_step else None
        
        # 如果无法获取当前步骤ID，使用实例对应流程的第一个步骤
        if not current_step_id:
            from app.models.approval import ApprovalStep
            first_step = ApprovalStep.query.filter_by(
                process_id=instance.process_id,
                step_order=1
            ).first()
            current_step_id = first_step.id if first_step else None
        
        # 如果仍然无法获取步骤ID，创建一个临时记录步骤
        if not current_step_id:
            current_app.logger.error(f"无法为召回操作找到合适的步骤ID，审批实例: {instance_id}")
            return jsonify({'success': False, 'message': '召回失败：无法确定当前审批步骤'}), 500
        
        # 添加召回记录
        from app.models.approval import ApprovalRecord
        recall_record = ApprovalRecord(
            instance_id=instance_id,
            step_id=current_step_id,  # 使用当前步骤ID或第一个步骤ID
            approver_id=current_user.id,
            action='recall',
            comment=f"发起人召回审批流程。原因：{reason}" if reason else "发起人召回审批流程",
            timestamp=datetime.now()
        )
        
        db.session.add(recall_record)
        
        # 解锁对象（重要：召回后需要解锁对象，允许用户重新编辑）
        if instance.object_type == 'project':
            unlock_project(instance.object_id, current_user.id)
            current_app.logger.info(f"召回审批后已解锁项目: {instance.object_id}")
        elif instance.object_type == 'quotation':
            from app.helpers.quotation_helpers import unlock_quotation
            unlock_quotation(instance.object_id, current_user.id)
            current_app.logger.info(f"召回审批后已解锁报价单: {instance.object_id}")
        
        db.session.commit()
        
        # 记录日志
        current_app.logger.info(f"用户 {current_user.username} 召回了审批实例 {instance_id}")
        
        return jsonify({
            'success': True,
            'message': '审批流程已成功召回'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"召回审批失败: {str(e)}")
        return jsonify({'success': False, 'message': f'召回失败: {str(e)}'}), 500


@approval_bp.route('/rollback-order/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def rollback_order(order_id):
    """管理员退回已通过的订单审批"""
    try:
        # 检查权限
        if not can_rollback_order_approval(order_id, current_user.id):
            return jsonify({
                'success': False,
                'message': '权限不足或订单状态不允许退回'
            })
        
        # 获取退回原因
        data = request.get_json()
        reason = data.get('reason', '') if data else ''
        
        # 执行退回操作
        success, message = rollback_order_approval(order_id, current_user.id, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            })
            
    except Exception as e:
        current_app.logger.error(f"退回订单审批失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'退回失败：{str(e)}'
        }) 


def get_tab_display_name(tab):
    """获取标签页显示名称"""
    tab_names = {
        'created': '我发起的',
        'pending': '待我审批的',
        'pricing_order': '批价单审批',
        'order': '订单审批',
        'department': '部门审批',
        'all': '全部审批'
    }
    return tab_names.get(tab, '审批列表')


def build_approval_list_config(tab, object_type=None, status=None, pending_count=0, created_pending_count=0, pricing_order_pending_count=0, order_pending_count=0):
    """构建审批中心的通用列表配置"""
    from flask import url_for
    
    # 筛选配置
    filter_config = {
        'action_url': url_for('approval.center'),
        'form_id': 'approvalFilterForm',
        'reset_url': url_for('approval.center'),
        
        'search_field': {
            'name': 'search',
            'label': '搜索',
            'placeholder': '审批编号、流程名称或业务关键词',
            'value': '',
            'col_width': 4
        },
        
        'filter_fields': [
            {
                'name': 'object_type',
                'label': '业务类型',
                'all_option_text': '全部类型',
                'current_value': object_type,
                'col_width': 3,
                'options': [
                    {'value': 'project', 'label': '项目', 'translate': True},
                    {'value': 'quotation', 'label': '报价单', 'translate': True},
                    {'value': 'customer', 'label': '客户', 'translate': True},
                    {'value': 'pricing_order', 'label': '批价单', 'translate': True},
                    {'value': 'purchase_order', 'label': '订单', 'translate': True}
                ]
            }
        ],
        
        'search_button_text': '搜索',
        'reset_button_text': '重置'
    }
    
    # 根据标签页添加不同的状态筛选
    if tab == 'created':
        filter_config['filter_fields'].append({
            'name': 'status',
            'label': '审批状态',
            'all_option_text': '全部状态',
            'current_value': status,
            'col_width': 3,
            'options': [
                {'value': 'draft', 'label': '草稿', 'translate': True},
                {'value': 'pending', 'label': '审批中', 'translate': True},
                {'value': 'approved', 'label': '已通过', 'translate': True},
                {'value': 'rejected', 'label': '已拒绝', 'translate': True}
            ]
        })
    elif tab == 'order':
        filter_config['filter_fields'].append({
            'name': 'status',
            'label': '订单状态',
            'all_option_text': '全部状态',
            'current_value': status,
            'col_width': 3,
            'options': [
                {'value': 'draft', 'label': '草稿', 'translate': True},
                {'value': 'pending', 'label': '审批中', 'translate': True},
                {'value': 'approved', 'label': '已通过', 'translate': True},
                {'value': 'rejected', 'label': '已拒绝', 'translate': True},
                {'value': 'confirmed', 'label': '已确认', 'translate': True},
                {'value': 'shipped', 'label': '已发货', 'translate': True},
                {'value': 'completed', 'label': '已完成', 'translate': True},
                {'value': 'cancelled', 'label': '已取消', 'translate': True}
            ]
        })
    
    # 统计卡片配置
    stats_config = {
        'cards': [
            {
                'id': 'total',
                'title': '全部审批',
                'icon': 'fas fa-clipboard-check',
                'value': pending_count + created_pending_count + pricing_order_pending_count + order_pending_count,
                'unit': '项',
                'color': 'primary',
                'clickable': True,
                'click_params': {}
            },
            {
                'id': 'pending',
                'title': '待我审批',
                'icon': 'fas fa-hourglass-half',
                'value': pending_count,
                'unit': '项',
                'color': 'warning',
                'clickable': True,
                'click_params': {'tab': 'pending'}
            },
            {
                'id': 'created',
                'title': '我发起的',
                'icon': 'fas fa-file-export',
                'value': created_pending_count,
                'unit': '项',
                'color': 'info',
                'clickable': True,
                'click_params': {'tab': 'created'}
            },
            {
                'id': 'pricing_order',
                'title': '批价单审批',
                'icon': 'fas fa-file-invoice-dollar',
                'value': pricing_order_pending_count,
                'unit': '项',
                'color': 'success',
                'clickable': True,
                'click_params': {'tab': 'pricing_order'}
            }
        ]
    }
    
    # 表格配置
    table_config = {
        'ajax_target': 'approvalTableBody',
        'title': f'审批列表 - {get_tab_display_name(tab)}',
        'icon': 'fas fa-table',
        'enhanced_striping': True,
        'infinite_scroll': True,
        'max_height': '600px',
        'columns': [
            {
                'key': 'approval_number',
                'label': '审批编号',
                'type': 'link',
                'url_template': '/approval/detail/{id}',
                'width': '200px',
                'render': 'render_approval_code'
            },
            {
                'key': 'process_name',
                'label': '流程名称',
                'type': 'text',
                'width': '200px'
            },
            {
                'key': 'business_info',
                'label': '关联业务',
                'type': 'badge',
                'render': 'render_business_object_badge',
                'width': '180px'
            },
            {
                'key': 'creator',
                'label': '提交人',
                'type': 'badge',
                'render': 'render_owner',
                'width': '150px'
            },
            {
                'key': 'current_approver',
                'label': '当前审批人',
                'type': 'badge',
                'render': 'render_owner',
                'width': '150px'
            },
            {
                'key': 'status',
                'label': '状态',
                'type': 'badge',
                'render': 'render_approval_status_badge',
                'width': '120px'
            },
            {
                'key': 'started_at',
                'label': '发起时间',
                'type': 'date',
                'format': '%Y-%m-%d %H:%M',
                'width': '180px'
            }
        ]
    }
    
    # 根据标签页调整列配置
    if tab == 'pricing_order':
        table_config['columns'][0] = {
            'key': 'pricing_order_number',
            'label': '批价单编号',
            'type': 'link',
            'url_template': '/pricing_order/detail/{id}',
            'width': '200px',
            'render': 'render_pricing_order_number'
        }
    elif tab == 'order':
        table_config['columns'][0] = {
            'key': 'order_number',
            'label': '订单编号',
            'type': 'link',
            'url_template': '/inventory/order/{id}',
            'width': '200px'
        }
        table_config['columns'][2] = {
            'key': 'company_name',
            'label': '供应商/客户',
            'type': 'text',
            'width': '180px'
        }
    
    return {
        'module_name': 'approval',
        'title': '审批中心',
        'ajax_mode': True,
        'stats': stats_config,
        'filter': filter_config,
        'table': table_config,
        'infinite_scroll': {
            'enabled': True,
            'per_page': 20,
            'threshold': 200
        }
    }



@approval_bp.route('/center_ajax')
@login_required
def center_ajax():
    """审批中心AJAX端点 - 支持通用数据列表组件"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = request.args.get('offset', 0, type=int) 
        limit = request.args.get('limit', 20, type=int)
        object_type = request.args.get('object_type')
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        tab = request.args.get('tab', 'created')
        
        # 计算分页参数
        if offset > 0:
            page = (offset // limit) + 1
            per_page = limit
        
        # 获取审批数据（复用原有逻辑）
        if tab == 'pending':
            approvals = get_user_pending_approvals(
                user_id=current_user.id,
                object_type=object_type,
                page=page,
                per_page=per_page
            )
        elif tab == 'pricing_order':
            from app.helpers.approval_helpers import get_user_pricing_order_approvals
            approvals = get_user_pricing_order_approvals(
                user_id=current_user.id,
                status=status,
                page=page,
                per_page=per_page
            )
        elif tab == 'order':
            from app.helpers.approval_helpers import get_user_order_approvals
            approvals = get_user_order_approvals(
                user_id=current_user.id,
                status_filter=status,
                page=page,
                per_page=per_page
            )
        elif tab == 'department':
            from app.helpers.approval_helpers import get_user_department_approvals
            approvals = get_user_department_approvals(
                user_id=current_user.id,
                object_type=object_type,
                status=status,
                page=page,
                per_page=per_page
            )
        elif tab == 'all' and has_permission('approval_management', 'all'):
            status_param = None
            if status:
                try:
                    status_param = ApprovalStatus[status.upper()]
                except (KeyError, AttributeError):
                    status_param = status
            
            approvals = get_all_approvals(
                object_type=object_type,
                status=status_param,
                page=page,
                per_page=per_page
            )
        else:
            # 我发起的
            status_param = None
            if status:
                try:
                    status_param = ApprovalStatus[status.upper()]
                except (KeyError, AttributeError):
                    status_param = status
                    
            approvals = get_user_created_approvals(
                user_id=current_user.id,
                object_type=object_type,
                status=status_param,
                page=page,
                per_page=per_page
            )
        
        # 应用搜索过滤（简单实现）
        items = approvals.items if hasattr(approvals, 'items') else approvals
        if search:
            # 这里可以实现搜索逻辑
            pass
        
        # 渲染行模板（需要创建）
        html_rows = []
        for item in items:
            # 根据标签页渲染不同的行内容
            if tab == 'pricing_order':
                # 批价单行渲染
                html_row = render_pricing_order_row(item)
            elif tab == 'order':
                # 订单行渲染
                html_row = render_order_row(item)
            else:
                # 通用审批行渲染
                html_row = render_approval_row(item, tab)
            html_rows.append(html_row)
        
        # 计算统计数据
        from app.helpers.approval_helpers import get_pending_approval_count, get_pending_created_count, get_pricing_order_pending_count, get_order_pending_count
        statistics = {
            'total_count': len(items),
            'pending_count': get_pending_approval_count(current_user.id),
            'created_count': get_pending_created_count(current_user.id),
            'pricing_order_count': get_pricing_order_pending_count(current_user.id),
            'order_count': get_order_pending_count(current_user.id)
        }
        
        return jsonify({
            'success': True,
            'html': '\n'.join(html_rows),
            'total_count': approvals.total if hasattr(approvals, 'total') else len(items),
            'loaded_count': len(items),
            'has_more': approvals.has_next if hasattr(approvals, 'has_next') else False,
            'statistics': statistics
        })
    
    except Exception as e:
        current_app.logger.error(f"审批中心AJAX加载失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'数据加载失败: {str(e)}',
            'html': '<tr><td colspan="7" class="text-center text-danger py-4"><i class="fas fa-exclamation-triangle"></i> 数据加载失败，请刷新页面重试</td></tr>'
        }), 500


def render_approval_row(item, tab='created'):
    """渲染审批行HTML"""
    from app.helpers.approval_helpers import get_current_step_info, get_last_approver
    
    # 获取当前步骤和审批人信息
    current_step = get_current_step_info(item)
    last_approver = get_last_approver(item) if item.status.name in ['APPROVED', 'REJECTED'] else None
    current_approver = last_approver or (current_step.approver if current_step else None)
    
    # 状态徽章
    status_badge = f'<span class="badge badge-pill badge-transparent approval-status-{item.status.name.lower()}">'
    if item.status.name == 'PENDING':
        status_badge += '审批中'
    elif item.status.name == 'APPROVED':  
        status_badge += '已通过'
    elif item.status.name == 'REJECTED':
        status_badge += '已拒绝'
    elif item.status.name == 'DRAFT':
        status_badge += '草稿'
    else:
        status_badge += item.status.name
    status_badge += '</span>'
    
    # 审批编号
    approval_code = f'<span class="badge badge-pill badge-transparent approval-code-badge">APV-{item.id:04d}</span>'
    
    # 业务对象信息
    business_info = get_business_object_display(item)
    
    # 创建人和当前审批人
    creator_name = item.creator.real_name if item.creator and hasattr(item.creator, 'real_name') and item.creator.real_name else (item.creator.username if item.creator else '未知')
    approver_name = current_approver.real_name if current_approver and hasattr(current_approver, 'real_name') and current_approver.real_name else (current_approver.username if current_approver else '待分配')
    
    # 发起时间
    started_time = item.started_at.strftime('%Y-%m-%d %H:%M') if item.started_at else ''
    
    return f'''
    <tr>
        <td><a href="/approval/detail/{item.id}" class="text-decoration-none">{approval_code}</a></td>
        <td>{item.process.name if item.process else '未知流程'}</td>
        <td>{business_info}</td>
        <td><span class="badge badge-pill badge-transparent business-object-none">{creator_name}</span></td>
        <td><span class="badge badge-pill badge-transparent business-object-none">{approver_name}</span></td>
        <td>{status_badge}</td>
        <td>{started_time}</td>
    </tr>
    '''


def render_pricing_order_row(item):
    """渲染批价单行HTML"""
    # 这里实现批价单特定的行渲染逻辑
    return render_approval_row(item, 'pricing_order')


def render_order_row(item):
    """渲染订单行HTML"""
    # 这里实现订单特定的行渲染逻辑  
    return render_approval_row(item, 'order')


def get_business_object_display(approval_item):
    """获取业务对象显示信息"""
    if approval_item.object_type == 'project' and approval_item.object_id:
        from app.helpers.approval_helpers import get_project_by_id
        project = get_project_by_id(approval_item.object_id)
        if project and project.project_name:
            return f'<span class="badge badge-pill badge-transparent business-object-project" title="{project.project_name}">{project.project_name[:20]}{"..." if len(project.project_name) > 20 else ""}</span>'
    elif approval_item.object_type == 'quotation' and approval_item.object_id:
        from app.helpers.approval_helpers import get_quotation_by_id
        quotation = get_quotation_by_id(approval_item.object_id)
        if quotation and quotation.project and quotation.project.authorization_code:
            return f'<span class="badge badge-pill badge-transparent business-object-project">{quotation.project.authorization_code}</span>'
    elif approval_item.object_type == 'customer' and approval_item.object_id:
        from app.helpers.approval_helpers import get_customer_by_id
        customer = get_customer_by_id(approval_item.object_id)
        if customer and customer.company_name:
            return f'<span class="badge badge-pill badge-transparent business-object-customer">{customer.company_name[:10]}...</span>'
    
    return f'<span class="badge badge-pill badge-transparent business-object-none">{approval_item.object_type or "未知类型"}</span>'