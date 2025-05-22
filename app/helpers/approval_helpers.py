from flask import current_app
from flask_login import current_user
from app import db
from app.models.approval import (
    ApprovalProcessTemplate, 
    ApprovalStep, 
    ApprovalInstance, 
    ApprovalRecord, 
    ApprovalStatus, 
    ApprovalAction
)
from app.models.user import User
from app.utils.dictionary_helpers import project_type_label
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime
from flask import url_for

def get_user_created_approvals(user_id=None, object_type=None, status=None, page=1, per_page=20):
    """获取指定用户发起的审批列表
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        object_type: 过滤特定类型的审批对象
        status: 过滤特定状态的审批
        page: 页码
        per_page: 每页数量
        
    Returns:
        分页对象，包含审批实例列表
    """
    if user_id is None:
        user_id = current_user.id
        
    query = ApprovalInstance.query.options(db.joinedload(ApprovalInstance.process)).filter(ApprovalInstance.created_by == user_id)
    
    if object_type:
        query = query.filter(ApprovalInstance.object_type == object_type)
        
    if status:
        query = query.filter(ApprovalInstance.status == status)
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalInstance.started_at.desc())
    
    # 返回分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_user_pending_approvals(user_id=None, object_type=None, page=1, per_page=20):
    """获取待用户审批的列表
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        object_type: 过滤特定类型的审批对象
        page: 页码
        per_page: 每页数量
        
    Returns:
        分页对象，包含待该用户审批的审批实例列表
    """
    if user_id is None:
        user_id = current_user.id
    
    # 复杂查询：找出当前用户是审批人且处于当前审批步骤的所有实例
    query = ApprovalInstance.query.options(db.joinedload(ApprovalInstance.process)).join(
        ApprovalStep, 
        and_(
            ApprovalStep.process_id == ApprovalInstance.process_id,
            ApprovalStep.step_order == ApprovalInstance.current_step
        )
    ).filter(
        ApprovalStep.approver_user_id == user_id,
        ApprovalInstance.status == ApprovalStatus.PENDING
    )
    
    if object_type:
        query = query.filter(ApprovalInstance.object_type == object_type)
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalInstance.started_at.desc())
    
    # 返回分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_approval_details(instance_id):
    """获取审批流程详情
    
    Args:
        instance_id: 审批实例ID
        
    Returns:
        审批实例对象，包含流程模板、当前步骤等完整信息
    """
    return ApprovalInstance.query.filter_by(id=instance_id).first_or_404()


def get_approval_object_url(instance):
    """获取审批对象的详情页URL
    
    Args:
        instance: 审批实例对象
        
    Returns:
        业务对象详情页URL
    """
    if not instance:
        return url_for('index')
    
    object_type = instance.object_type
    object_id = instance.object_id
    
    if object_type == 'project':
        return url_for('project.view_project', project_id=object_id)
    elif object_type == 'quotation':
        return url_for('quotation.view_quotation', id=object_id)
    elif object_type == 'customer':
        return url_for('customer.view_company', company_id=object_id)
    else:
        return url_for('index')


def get_current_step_info(instance):
    """获取当前审批步骤信息
    
    Args:
        instance: 审批实例对象
        
    Returns:
        当前步骤对象
    """
    if not instance or instance.status != ApprovalStatus.PENDING:
        return None
    
    return ApprovalStep.query.filter_by(
        process_id=instance.process_id,
        step_order=instance.current_step
    ).first()


def get_approval_records_by_instance(instance_id):
    """获取审批实例的所有审批记录
    
    Args:
        instance_id: 审批实例ID
        
    Returns:
        审批记录列表，按时间倒序排序
    """
    return ApprovalRecord.query.filter_by(
        instance_id=instance_id
    ).order_by(ApprovalRecord.timestamp.desc()).all()


def can_user_approve(instance_id, user_id=None):
    """检查用户是否可以审批当前步骤
    
    Args:
        instance_id: 审批实例ID
        user_id: 用户ID，默认为当前登录用户
        
    Returns:
        布尔值，表示用户是否可以审批
    """
    if user_id is None:
        user_id = current_user.id
    
    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    # 获取当前步骤
    current_step = get_current_step_info(instance)
    if not current_step:
        return False
    
    return current_step.approver_user_id == user_id

# ----- 以下是审批流程配置模块需要的函数 ----- #

def get_approval_templates(page=1, per_page=10, object_type=None, is_active=None):
    """获取审批流程模板列表
    
    Args:
        page: 页码
        per_page: 每页数量
        object_type: 过滤特定类型的审批对象
        is_active: 是否只返回启用的模板
        
    Returns:
        分页对象，包含审批流程模板列表
    """
    query = ApprovalProcessTemplate.query
    
    if object_type:
        query = query.filter(ApprovalProcessTemplate.object_type == object_type)
        
    if is_active is not None:
        query = query.filter(ApprovalProcessTemplate.is_active == is_active)
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalProcessTemplate.created_at.desc())
    
    # 返回分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_template_details(template_id):
    """获取审批流程模板详情
    
    Args:
        template_id: 模板ID
        
    Returns:
        模板对象，包含所有步骤
    """
    return ApprovalProcessTemplate.query.filter_by(id=template_id).first_or_404()


def get_template_steps(template_id):
    """获取审批流程模板的所有步骤
    
    Args:
        template_id: 模板ID
        
    Returns:
        步骤列表，按step_order排序
    """
    return ApprovalStep.query.filter_by(
        process_id=template_id
    ).order_by(ApprovalStep.step_order.asc()).all()


def create_approval_template(name, object_type, creator_id=None, required_fields=None):
    """创建审批流程模板
    
    Args:
        name: 模板名称
        object_type: 适用业务对象类型
        creator_id: 创建人ID
        required_fields: 发起审批必填字段列表
        
    Returns:
        创建的模板对象
    """
    if creator_id is None:
        creator_id = current_user.id
        
    # 处理必填字段
    if isinstance(required_fields, str):
        # 如果是字符串，以逗号分隔，转换为列表
        required_fields = [field.strip() for field in required_fields.split(',') if field.strip()]
    elif required_fields is None:
        required_fields = []
        
    template = ApprovalProcessTemplate(
        name=name,
        object_type=object_type,
        created_by=creator_id,
        is_active=True,
        required_fields=required_fields
    )
    
    db.session.add(template)
    db.session.commit()
    
    current_app.logger.info(f"创建审批模板: {name}, ID: {template.id}")
    return template


def update_approval_template(template_id, name=None, object_type=None, is_active=None, required_fields=None):
    """更新审批流程模板
    
    Args:
        template_id: 模板ID
        name: 新的模板名称
        object_type: 新的适用对象类型
        is_active: 是否启用
        required_fields: 发起审批必填字段列表
        
    Returns:
        更新后的模板对象
    """
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        return None
    
    if name is not None:
        template.name = name
        
    if object_type is not None:
        template.object_type = object_type
        
    if is_active is not None:
        template.is_active = is_active
    
    # 处理必填字段
    if required_fields is not None:
        if isinstance(required_fields, str):
            # 如果是字符串，以逗号分隔，转换为列表
            template.required_fields = [field.strip() for field in required_fields.split(',') if field.strip()]
        else:
            template.required_fields = required_fields
    
    db.session.commit()
    
    current_app.logger.info(f"更新审批模板: {template.name}, ID: {template.id}")
    return template


def delete_approval_template(template_id):
    """删除审批流程模板
    
    Args:
        template_id: 模板ID
        
    Returns:
        布尔值，表示是否成功删除
    """
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        return False
    
    # 检查是否有关联的审批实例
    instances = ApprovalInstance.query.filter_by(process_id=template_id).first()
    if instances:
        # 如果有关联实例，则只是将模板标记为禁用
        template.is_active = False
        db.session.commit()
        return False
    
    # 否则，删除模板和所有关联的步骤
    ApprovalStep.query.filter_by(process_id=template_id).delete()
    db.session.delete(template)
    db.session.commit()
    
    return True


def add_approval_step(template_id, step_name, approver_id, send_email=True):
    """添加审批步骤
    
    Args:
        template_id: 模板ID
        step_name: 步骤名称
        approver_id: 审批人ID
        send_email: 是否发送邮件通知
        
    Returns:
        新创建的步骤对象，如果模板不存在则返回None
    """
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        return None
    
    # 获取最大步骤序号
    max_order = db.session.query(db.func.max(ApprovalStep.step_order)).filter(
        ApprovalStep.process_id == template_id
    ).scalar() or 0
    
    # 添加新步骤
    step = ApprovalStep(
        process_id=template_id,
        step_order=max_order + 1,
        approver_user_id=approver_id,
        step_name=step_name,
        send_email=send_email
    )
    
    db.session.add(step)
    db.session.commit()
    
    return step


def update_approval_step(step_id, step_name=None, approver_id=None, send_email=None):
    """更新审批步骤
    
    Args:
        step_id: 步骤ID
        step_name: 步骤名称
        approver_id: 审批人ID
        send_email: 是否发送邮件通知
        
    Returns:
        更新后的步骤对象，如果没有找到则返回None
    """
    step = ApprovalStep.query.get(step_id)
    if not step:
        return None
    
    if step_name is not None:
        step.step_name = step_name
        
    if approver_id is not None:
        step.approver_user_id = approver_id
        
    if send_email is not None:
        step.send_email = send_email
    
    db.session.commit()
    
    return step


def delete_approval_step(step_id):
    """删除审批步骤
    
    Args:
        step_id: 步骤ID
        
    Returns:
        布尔值，表示是否成功删除
    """
    step = ApprovalStep.query.get(step_id)
    if not step:
        return False
    
    template_id = step.process_id
    current_order = step.step_order
    
    # 删除步骤
    db.session.delete(step)
    
    # 更新后续步骤的序号
    later_steps = ApprovalStep.query.filter(
        ApprovalStep.process_id == template_id,
        ApprovalStep.step_order > current_order
    ).all()
    
    for later_step in later_steps:
        later_step.step_order -= 1
    
    db.session.commit()
    
    return True


def reorder_approval_steps(template_id, step_order_map):
    """重新排序审批步骤
    
    Args:
        template_id: 模板ID
        step_order_map: 字典，键为步骤ID，值为新的step_order
        
    Returns:
        布尔值，表示是否成功重新排序
    """
    steps = ApprovalStep.query.filter_by(process_id=template_id).all()
    if not steps:
        return False
    
    # 创建一个临时映射存储原始顺序
    temp_order_map = {}
    
    # 更新步骤序号
    for step in steps:
        if step.id in step_order_map:
            # 使用负数作为临时序号，避免唯一性冲突
            temp_order_map[step.id] = step.step_order
            step.step_order = -step_order_map[step.id]
    
    db.session.commit()
    
    # 将负数序号转换为正数
    for step in steps:
        if step.step_order < 0:
            step.step_order = -step.step_order
    
    db.session.commit()
    
    return True


def get_all_users(active_only=True):
    """获取所有用户列表，用于选择审批人
    
    Args:
        active_only: 是否只返回激活状态的用户
    
    Returns:
        用户列表
    """
    # 初始查询
    query = User.query
    
    # 如果只需要活跃用户
    if active_only:
        # 管理员总是被视为活跃的，即使is_active字段为False
        # 使用OR条件查询：管理员或者is_active=True的用户
        query = query.filter(db.or_(
            User.role == 'admin',
            User._is_active == True
        ))
    
    # 执行查询并返回结果
    return query.order_by(User.username).all()


def get_object_types():
    """获取所有支持的业务对象类型
    
    Returns:
        对象类型列表，每项为(类型代码, 显示名称)
    """
    return [
        ('project', '项目'),
        ('quotation', '报价单'),
        ('customer', '客户')
    ]


# 辅助函数：获取对象类型的显示名称
def get_object_type_display(object_type):
    """获取对象类型的显示名称
    
    Args:
        object_type: 对象类型代码
        
    Returns:
        对象类型的中文显示名称
    """
    type_map = {
        'project': '项目',
        'quotation': '报价单',
        'customer': '客户',
    }
    
    return type_map.get(object_type, object_type)


def check_template_in_use(template_id):
    """检查审批流程模板是否正在使用
    
    Args:
        template_id: 模板ID
        
    Returns:
        布尔值，表示模板是否有关联的审批实例
    """
    return ApprovalInstance.query.filter_by(process_id=template_id).first() is not None


def get_object_approval_instance(object_type, object_id):
    """获取业务对象的审批实例
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID
        
    Returns:
        对应的审批实例，如果没有则返回None
    """
    instance = ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id
    ).first()

    # 如果没有实例或实例状态不是PENDING，允许重新发起
    if instance and instance.status == ApprovalStatus.PENDING:
        return instance
    elif instance and instance.status == ApprovalStatus.APPROVED:
        # 已批准的实例也返回，用于显示审批历史
        return instance
    else:
        # 被拒绝或其他情况，允许重新发起审批
        return None


def get_available_templates(object_type, object_id=None):
    """获取可用的审批流程模板列表
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID（可选），用于获取业务对象的特定属性以便更精确地筛选模板
        
    Returns:
        可用的审批流程模板列表
    """
    # 基本过滤：模板类型匹配且处于激活状态
    templates = ApprovalProcessTemplate.query.filter_by(
        object_type=object_type,
        is_active=True
    ).all()
    
    # 如果提供了业务对象ID，进行更精确的筛选
    if object_id and templates:
        # 根据业务对象类型获取额外属性
        business_type = None
        
        if object_type == 'project':
            from app.models.project import Project
            project = Project.query.get(object_id)
            if project:
                business_type = project.project_type
        
        # 如果获取到了业务类型，过滤模板
        if business_type:
            # 检查模板名称是否包含业务类型关键词
            filtered_templates = []
            for template in templates:
                # 审批模板名称中包含业务类型关键词
                if business_type in template.name:
                    filtered_templates.append(template)
                # 或者检查模板id，可以添加特定规则
            
            # 如果过滤后没有模板，则返回原始列表
            if filtered_templates:
                templates = filtered_templates
    
    return templates


def start_approval_process(object_type, object_id, template_id, user_id=None):
    """发起审批流程
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID
        template_id: 审批流程模板ID
        user_id: 发起人ID，默认为当前登录用户
        
    Returns:
        新建的审批实例对象，如果失败则返回None
    """
    # 记录详细的诊断信息
    current_app.logger.info(f"开始发起审批流程: 对象类型={object_type}, 对象ID={object_id}, 模板ID={template_id}")
    
    # 检查是否已存在进行中的审批实例
    existing = get_object_approval_instance(object_type, object_id)
    if existing:
        status_str = str(existing.status) if hasattr(existing, 'status') else '未知状态'
        current_app.logger.warning(
            f"业务对象已存在审批实例: {object_type}:{object_id}, "
            f"实例ID: {existing.id}, 状态: {status_str}"
        )
        return None
    
    # 查询历史审批实例，以便在日志中记录
    history_instance = ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id
    ).order_by(ApprovalInstance.ended_at.desc()).first()
    
    if history_instance and history_instance.status == ApprovalStatus.REJECTED:
        current_app.logger.info(f"该业务对象有被拒绝的审批历史: 实例ID={history_instance.id}, 拒绝时间={history_instance.ended_at}")
    
    # 获取模板
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        current_app.logger.warning(f"审批模板不存在: {template_id}")
        return None
        
    if not template.is_active:
        current_app.logger.warning(f"审批模板未启用: {template_id} ({template.name})")
        return None
    
    # 检查模板是否有步骤
    steps = ApprovalStep.query.filter_by(process_id=template_id).order_by(ApprovalStep.step_order.asc()).all()
    if not steps:
        current_app.logger.warning(f"审批模板没有配置审批步骤: {template_id} ({template.name})")
        return None
    
    current_app.logger.info(f"审批模板 {template.name} (ID: {template_id}) 有 {len(steps)} 个步骤")
    
    # 检查必填字段
    has_required_fields = hasattr(template, 'required_fields') and template.required_fields and len(template.required_fields) > 0
    
    if has_required_fields:
        current_app.logger.info(f"审批模板 {template.name} 设置了以下必填字段: {template.required_fields}")
        
        # 根据业务对象类型获取对象
        if object_type == 'project':
            from app.models.project import Project
            obj = Project.query.get(object_id)
        elif object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(object_id)
        elif object_type == 'customer':
            from app.models.customer import Company
            obj = Company.query.get(object_id)
        else:
            obj = None
        
        if not obj:
            current_app.logger.warning(f"找不到业务对象: {object_type}:{object_id}")
            return None
        
        # 检查每个必填字段
        empty_fields = []
        field_values = {}  # 记录字段值用于日志
        
        for field in template.required_fields:
            if hasattr(obj, field):
                field_value = getattr(obj, field)
                # 记录字段值
                if isinstance(field_value, (str, int, float, bool)) or field_value is None:
                    field_values[field] = field_value
                elif isinstance(field_value, list):
                    field_values[field] = f"列表[长度={len(field_value)}]"
                elif field_value:
                    field_values[field] = f"对象类型: {type(field_value).__name__}"
                else:
                    field_values[field] = "空值"
                
                # 检查是否为空
                if field_value is None or field_value == '' or (isinstance(field_value, list) and len(field_value) == 0):
                    empty_fields.append(field)
            else:
                current_app.logger.warning(f"业务对象 {object_type} 没有字段 {field}")
                field_values[field] = "字段不存在"
                empty_fields.append(field)
        
                # 记录字段值日志
        current_app.logger.info(f"业务对象 {object_type}:{object_id} 字段值: {field_values}")
        
        if empty_fields:
            # 转换字段名为可读名称
            readable_fields = []
            for field in empty_fields:
                readable_fields.append(_get_field_display_name(field))
            
            error_msg = f"发起审批失败: 以下字段必填但未填写: {', '.join(readable_fields)}"
            current_app.logger.warning(error_msg)
            from flask import flash
            flash(error_msg, 'danger')
            return None
    
    if user_id is None:
        from flask_login import current_user
        user_id = current_user.id
    
    try:
        # 创建审批实例
        instance = ApprovalInstance(
            process_id=template_id,
            object_id=object_id,
            object_type=object_type,
            current_step=1,  # 从第一步开始
            status=ApprovalStatus.PENDING,
            started_at=datetime.now(),
            created_by=user_id
        )
        db.session.add(instance)
        db.session.commit()
        current_app.logger.info(f"成功发起审批流程: {object_type}:{object_id}, 模板ID: {template_id}, 实例ID: {instance.id}")
        return instance
    except Exception as e:
        current_app.logger.error(f"创建审批实例时发生异常: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        from flask import flash
        flash(f"发起审批失败: 系统错误 - {str(e)}", 'danger')
        return None


def _get_field_display_name(field_name):
    """获取字段的显示名称
    
    Args:
        field_name: 字段名
        
    Returns:
        字段的显示名称
    """
    field_map = {
        # 项目字段
        'authorization_code': '授权编号',
        'project_code': '项目编号',
        'project_name': '项目名称',
        'project_type': '项目类型',
        'report_time': '报备时间',
        'report_source': '报备来源',
        'end_user': '最终用户',
        'design_issues': '设计院/顾问',
        'contractor': '总承包单位',
        'system_integrator': '系统集成商',
        'product_situation': '品牌情况',
        'current_stage': '当前阶段',
        'delivery_forecast': '出货预测日期',
        'quotation_customer': '报价金额',
        
        # 报价单字段
        'quotation_code': '报价单编号',
        'customer_name': '客户名称',
        'valid_days': '有效期',
        'currency': '币种',
        'total_amount': '总金额',
        
        # 客户字段
        'company_name': '企业名称',
        'company_type': '企业类型',
        'industry': '行业',
        'country': '国家/地区',
        'region': '省份/州',
        'address': '地址',
        'contact_name': '联系人',
    }
    
    return field_map.get(field_name, field_name)


def process_approval_with_project_type(instance_id, action, project_type=None, comment=None, user_id=None):
    """处理审批操作，支持项目类型修改
    
    Args:
        instance_id: 审批实例ID
        action: 审批动作（ApprovalAction枚举值）
        project_type: 项目类型，用于授权步骤
        comment: 审批意见
        user_id: 操作人ID
        
    Returns:
        布尔值，表示操作是否成功
    """
    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    if user_id is None:
        user_id = current_user.id
    
    # 获取当前步骤
    current_step = get_current_step_info(instance)
    if not current_step or current_step.approver_user_id != user_id:
        return False
    
    # 检查是否是授权编号步骤
    is_authorization_step = (
        hasattr(current_step, 'action_type') and 
        current_step.action_type == 'authorization'
    )
    
    # 确保action是枚举类型
    if not isinstance(action, ApprovalAction):
        if action == 'approve':
            action = ApprovalAction.APPROVE
        elif action == 'reject':
            action = ApprovalAction.REJECT
        else:
            current_app.logger.error(f"无效的审批动作: {action}")
            return False
    
    # 记录审批结果
    record = ApprovalRecord(
        instance_id=instance_id,
        step_id=current_step.id,
        approver_id=user_id,
        action=action.value,
        comment=comment,
        timestamp=datetime.now()
    )
    
    db.session.add(record)
    
    # 处理授权编号逻辑 - 只有通过且是授权步骤时才执行
    authorization_result = None
    if action == ApprovalAction.APPROVE and is_authorization_step and instance.object_type == 'project':
        authorization_result = _handle_project_authorization(instance, project_type)
    
    # 如果拒绝，直接结束流程
    if action == ApprovalAction.REJECT:
        instance.status = ApprovalStatus.REJECTED
        instance.ended_at = datetime.now()
        
        # 如果是项目，解锁它
        if instance.object_type == 'project':
            from app.helpers.project_helpers import unlock_project
            unlock_project(instance.object_id, user_id)
    else:
        # 获取下一步骤
        next_step_order = instance.current_step + 1
        next_step = ApprovalStep.query.filter_by(
            process_id=instance.process_id,
            step_order=next_step_order
        ).first()
        
        if next_step:
            # 更新到下一步
            instance.current_step = next_step_order
        else:
            # 所有步骤已完成，流程通过
            instance.status = ApprovalStatus.APPROVED
            instance.ended_at = datetime.now()
            
            # 如果是项目，解锁它
            if instance.object_type == 'project':
                from app.helpers.project_helpers import unlock_project
                unlock_project(instance.object_id, user_id)
    
    try:
        db.session.commit()
        
        # 如果设置了发送邮件，则发送邮件通知
        if current_step.send_email:
            try:
                _send_approval_notification(instance, current_step, action, comment)
            except Exception as e:
                # 记录日志但不影响主流程
                current_app.logger.error(f"发送审批邮件失败: {str(e)}")
        
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"处理审批失败: {str(e)}")
        return False


def _handle_project_authorization(instance, project_type):
    """处理项目授权编号逻辑
    
    Args:
        instance: 审批实例对象
        project_type: 用户选择的项目类型
        
    Returns:
        生成的授权编号或None
    """
    from app.models.project import Project
    project = Project.query.get(instance.object_id)
    if not project:
        current_app.logger.error(f"找不到项目: {instance.object_id}")
        return None
    
    # 如果已经有授权编号，则不做处理
    if project.authorization_code:
        current_app.logger.warning(f"项目已有授权编号，不进行处理: {project.id} - {project.authorization_code}")
        return project.authorization_code
    
    try:
        # 如果提供了项目类型，则更新项目类型
        if project_type and project_type != project.project_type:
            current_app.logger.info(f"更新项目类型: {project.id}, 原类型: {project.project_type}, 新类型: {project_type}")
            project.project_type = project_type
        
        # 将英文类型映射为中文，用于生成授权编号
        project_type_for_code = project_type_label(project.project_type)
        
        # 生成授权编号
        authorization_code = Project.generate_authorization_code(project_type_for_code)
        if not authorization_code:
            current_app.logger.error(f"无法为项目生成授权编号: {project.id}, 类型: {project_type_for_code}")
            return None
        
        # 更新项目信息
        project.authorization_code = authorization_code
        project.authorization_status = None  # 清除pending状态
        project.report_time = datetime.now().date()  # 更新报备日期为当前日期
        
        # 同步更新所有关联报价单的project_stage和project_type
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter_by(project_id=project.id).all()
        for q in quotations:
            q.project_stage = project.current_stage
            q.project_type = project.project_type
        
        current_app.logger.info(f"项目授权成功: {project.id}, 授权编号: {authorization_code}, 项目类型: {project.project_type}")
        return authorization_code
    except Exception as e:
        current_app.logger.error(f"处理项目授权失败: {project.id}, 错误: {str(e)}")
        return None


def process_approval(instance_id, action, comment=None, user_id=None, project_type=None):
    """处理审批操作
    
    Args:
        instance_id: 审批实例ID
        action: 审批动作（ApprovalAction枚举值）
        comment: 审批意见
        user_id: 操作人ID，默认为当前登录用户
        project_type: 项目类型，用于授权步骤
        
    Returns:
        布尔值，表示操作是否成功
    """
    # 如果提供了项目类型，使用扩展的处理函数
    if project_type is not None:
        return process_approval_with_project_type(instance_id, action, project_type, comment, user_id)
    
    # 原始处理逻辑保持不变...
    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    if user_id is None:
        user_id = current_user.id
    
    # 获取当前步骤
    current_step = get_current_step_info(instance)
    if not current_step or current_step.approver_user_id != user_id:
        return False
    
    # 确保action是枚举类型
    if not isinstance(action, ApprovalAction):
        if action == 'approve':
            action = ApprovalAction.APPROVE
        elif action == 'reject':
            action = ApprovalAction.REJECT
        else:
            current_app.logger.error(f"无效的审批动作: {action}")
            return False
    
    # 记录审批结果
    record = ApprovalRecord(
        instance_id=instance_id,
        step_id=current_step.id,
        approver_id=user_id,
        action=action.value,
        comment=comment,
        timestamp=datetime.now()
    )
    
    db.session.add(record)
    
    # 如果拒绝，直接结束流程
    if action == ApprovalAction.REJECT:
        instance.status = ApprovalStatus.REJECTED
        instance.ended_at = datetime.now()
        
        # 如果是项目，解锁它
        if instance.object_type == 'project':
            from app.helpers.project_helpers import unlock_project
            unlock_project(instance.object_id, user_id)
    else:
        # 获取下一步骤
        next_step_order = instance.current_step + 1
        next_step = ApprovalStep.query.filter_by(
            process_id=instance.process_id,
            step_order=next_step_order
        ).first()
        
        if next_step:
            # 更新到下一步
            instance.current_step = next_step_order
        else:
            # 所有步骤已完成，流程通过
            instance.status = ApprovalStatus.APPROVED
            instance.ended_at = datetime.now()
            
            # 如果是项目，解锁它
            if instance.object_type == 'project':
                from app.helpers.project_helpers import unlock_project
                unlock_project(instance.object_id, user_id)
    
    db.session.commit()
    
    # 如果设置了发送邮件，则发送邮件通知
    if current_step.send_email:
        try:
            _send_approval_notification(instance, current_step, action, comment)
        except Exception as e:
            # 记录日志但不影响主流程
            current_app.logger.error(f"发送审批邮件失败: {str(e)}")
    
    return True


def _send_approval_notification(instance, step, action, comment):
    """发送审批通知邮件（内部函数）
    
    Args:
        instance: 审批实例
        step: 当前步骤
        action: 审批动作
        comment: 审批意见
    """
    # 邮件发送逻辑，可根据项目实际需求实现
    # 这里仅添加占位，实际实现可在第五阶段通知系统中完成
    pass 


def delete_approval_instance(instance_id):
    """删除审批实例
    
    Args:
        instance_id: 审批实例ID
        
    Returns:
        布尔值，表示是否成功删除
    """
    instance = ApprovalInstance.query.get(instance_id)
    if not instance:
        return False
    
    # 删除相关记录和实例
    try:
        # 级联删除所有相关记录
        db.session.delete(instance)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除审批实例失败: {str(e)}")
        return False


def get_object_field_options(object_type=None):
    """获取业务对象的字段选项列表，用于必填字段下拉多选
    
    Args:
        object_type: 业务对象类型，如project、quotation、customer
        
    Returns:
        字段选项列表，每项为 (字段名, 显示名称)
    """
    # 所有业务对象类型通用字段
    common_fields = []
    
    # 各业务对象特有字段
    project_fields = [
        ('project_code', '项目编号'),
        ('project_name', '项目名称'),
        ('authorization_code', '授权编号'),
        ('project_type', '项目类型'),
        ('report_time', '报备时间'),
        ('report_source', '报备来源'),
        ('end_user', '最终用户'),
        ('design_issues', '设计院/顾问'),
        ('contractor', '总承包单位'),
        ('system_integrator', '系统集成商'),
        ('product_situation', '品牌情况'),
        ('current_stage', '当前阶段'),
        ('delivery_forecast', '出货预测日期')
    ]
    
    quotation_fields = [
        ('quotation_code', '报价单编号'),
        ('customer_name', '客户名称'),
        ('valid_days', '有效期'),
        ('currency', '币种'),
        ('total_amount', '总金额'),
        ('project_type', '项目类型')
    ]
    
    customer_fields = [
        ('company_name', '企业名称'),
        ('company_type', '企业类型'),
        ('industry', '行业'),
        ('country', '国家/地区'),
        ('region', '省份/州'),
        ('address', '地址'),
        ('contact_name', '联系人')
    ]
    
    # 根据业务对象类型返回对应的字段列表
    if object_type == 'project':
        return common_fields + project_fields
    elif object_type == 'quotation':
        return common_fields + quotation_fields
    elif object_type == 'customer':
        return common_fields + customer_fields
    else:
        # 如果没有指定业务对象类型，返回所有字段
        all_fields = set(common_fields + project_fields + quotation_fields + customer_fields)
        return sorted(list(all_fields), key=lambda x: x[1])  # 按显示名称排序 


def get_rejected_approval_history(object_type, object_id):
    """获取业务对象最近一条被拒绝的审批历史
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID
        
    Returns:
        最近一条被拒绝的审批实例，如果没有则返回None
    """
    return ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id,
        status=ApprovalStatus.REJECTED
    ).order_by(ApprovalInstance.ended_at.desc()).first() 


def get_pending_approval_count(user_id=None):
    """获取待用户审批的数量
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        
    Returns:
        整数，表示待审批的数量
    """
    if user_id is None:
        user_id = current_user.id
    
    # 查询当前用户是审批人且处于当前审批步骤的所有实例数量
    count = ApprovalInstance.query.join(
        ApprovalStep, 
        and_(
            ApprovalStep.process_id == ApprovalInstance.process_id,
            ApprovalStep.step_order == ApprovalInstance.current_step
        )
    ).filter(
        ApprovalStep.approver_user_id == user_id,
        ApprovalInstance.status == ApprovalStatus.PENDING
    ).count()
    
    return count 