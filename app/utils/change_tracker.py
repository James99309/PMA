from flask import request
from flask_login import current_user
from app.models.change_log import ChangeLog
from app import db
import inspect
from functools import wraps

class ChangeTracker:
    """
    改动跟踪器
    用于自动记录模型的变更历史
    """
    
    # 字段名称映射，用于显示友好的中文名称
    FIELD_NAME_MAP = {
        # 项目字段
        'project_name': '项目名称',
        'report_time': '报备时间',
        'project_type': '项目类型',
        'report_source': '报备来源',
        'product_situation': '产品情况',
        'end_user': '最终用户',
        'design_issues': '设计院',
        'dealer': '经销商',
        'contractor': '总承包商',
        'system_integrator': '系统集成商',
        'current_stage': '当前阶段',
        'stage_description': '阶段描述',
        'authorization_code': '授权编码',
        'delivery_forecast': '交付预测',
        'quotation_customer': '报价客户',
        'authorization_status': '授权状态',
        'feedback': '反馈',
        'vendor_sales_manager_id': '厂商负责人',
        'owner_id': '项目拥有人',
        
        # 客户字段
        'company_name': '公司名称',
        'company_type': '公司类型',
        'company_address': '公司地址',
        'company_phone': '公司电话',
        'company_email': '公司邮箱',
        'company_website': '公司网站',
        'company_description': '公司描述',
        'is_active': '是否活跃',
        
        # 联系人字段
        'contact_name': '联系人姓名',
        'contact_position': '职位',
        'contact_phone': '联系电话',
        'contact_email': '联系邮箱',
        'contact_wechat': '微信',
        'contact_qq': 'QQ',
        'contact_notes': '备注',
        
        # 报价单字段
        'quotation_number': '报价单号',
        'quotation_date': '报价日期',
        'project_stage': '项目阶段',
        'total_amount': '总金额',
        'discount_rate': '折扣率',
        'final_amount': '最终金额',
        'notes': '备注',
        'status': '状态',
        
        # 用户字段
        'username': '用户名',
        'name': '姓名',
        'email': '邮箱',
        'role': '角色',
        'department': '部门',
        'phone': '电话',
        'is_active': '是否激活',
    }
    
    # 模块名称映射
    MODULE_NAME_MAP = {
        'Project': 'project',
        'Company': 'customer',
        'Contact': 'customer',
        'Quotation': 'quotation',
        'User': 'user',
    }
    
    @classmethod
    def get_field_display_name(cls, field_name):
        """获取字段的显示名称"""
        return cls.FIELD_NAME_MAP.get(field_name, field_name)
    
    @classmethod
    def get_module_name(cls, model_class):
        """获取模块名称"""
        class_name = model_class.__name__
        return cls.MODULE_NAME_MAP.get(class_name, class_name.lower())
    
    @classmethod
    def get_record_info(cls, obj):
        """获取记录的描述信息"""
        if hasattr(obj, 'project_name'):
            return f"项目: {obj.project_name}"
        elif hasattr(obj, 'company_name'):
            return f"公司: {obj.company_name}"
        elif hasattr(obj, 'contact_name'):
            return f"联系人: {obj.contact_name}"
        elif hasattr(obj, 'quotation_number'):
            return f"报价单: {obj.quotation_number}"
        elif hasattr(obj, 'username'):
            return f"用户: {obj.username}"
        elif hasattr(obj, 'name'):
            return f"记录: {obj.name}"
        else:
            return f"ID: {obj.id}"
    
    @classmethod
    def log_create(cls, obj):
        """记录创建操作"""
        try:
            # 安全地获取用户信息
            user_id = None
            user_name = '系统'
            try:
                if current_user and current_user.is_authenticated:
                    user_id = current_user.id
                    user_name = current_user.username
            except:
                pass  # 如果获取用户信息失败，使用默认值
            
            log = ChangeLog(
                module_name=cls.get_module_name(obj.__class__),
                table_name=obj.__tablename__,
                record_id=obj.id,
                operation_type='CREATE',
                record_info=cls.get_record_info(obj),
                user_id=user_id,
                user_name=user_name,
                ip_address=request.remote_addr if request else None
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"记录创建日志失败: {str(e)}")
    
    @classmethod
    def log_update(cls, obj, old_values, new_values):
        """记录更新操作"""
        try:
            # 安全地获取用户信息
            user_id = None
            user_name = '系统'
            try:
                if current_user and current_user.is_authenticated:
                    user_id = current_user.id
                    user_name = current_user.username
            except:
                pass  # 如果获取用户信息失败，使用默认值
            
            for field_name, old_value in old_values.items():
                new_value = new_values.get(field_name)
                
                # 只记录有变化的字段
                if old_value != new_value:
                    log = ChangeLog(
                        module_name=cls.get_module_name(obj.__class__),
                        table_name=obj.__tablename__,
                        record_id=obj.id,
                        operation_type='UPDATE',
                        field_name=cls.get_field_display_name(field_name),
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(new_value) if new_value is not None else None,
                        record_info=cls.get_record_info(obj),
                        user_id=user_id,
                        user_name=user_name,
                        ip_address=request.remote_addr if request else None
                    )
                    db.session.add(log)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"记录更新日志失败: {str(e)}")
    
    @classmethod
    def log_delete(cls, obj):
        """记录删除操作"""
        try:
            # 安全地获取用户信息
            user_id = None
            user_name = '系统'
            try:
                if current_user and current_user.is_authenticated:
                    user_id = current_user.id
                    user_name = current_user.username
            except:
                pass  # 如果获取用户信息失败，使用默认值
            
            log = ChangeLog(
                module_name=cls.get_module_name(obj.__class__),
                table_name=obj.__tablename__,
                record_id=obj.id,
                operation_type='DELETE',
                record_info=cls.get_record_info(obj),
                user_id=user_id,
                user_name=user_name,
                ip_address=request.remote_addr if request else None
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"记录删除日志失败: {str(e)}")
    
    @classmethod
    def capture_old_values(cls, obj, fields=None):
        """捕获对象的当前值，用于后续比较"""
        old_values = {}
        
        if fields is None:
            # 如果没有指定字段，获取所有列
            fields = [column.name for column in obj.__table__.columns]
        
        for field in fields:
            if hasattr(obj, field):
                old_values[field] = getattr(obj, field)
        
        return old_values
    
    @classmethod
    def get_new_values(cls, obj, fields):
        """获取对象的新值"""
        new_values = {}
        
        for field in fields:
            if hasattr(obj, field):
                new_values[field] = getattr(obj, field)
        
        return new_values

def track_changes(model_class, fields=None):
    """
    装饰器：自动跟踪模型的变更
    
    Args:
        model_class: 要跟踪的模型类
        fields: 要跟踪的字段列表，如果为None则跟踪所有字段
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 在函数执行前捕获旧值（仅对更新操作）
            old_values = None
            obj_id = None
            
            # 尝试从参数中获取对象ID
            if 'id' in kwargs:
                obj_id = kwargs['id']
            elif len(args) > 0 and hasattr(args[0], 'view_args') and 'id' in args[0].view_args:
                obj_id = args[0].view_args['id']
            elif len(args) > 1 and isinstance(args[1], int):
                obj_id = args[1]
            
            # 如果是更新操作，先获取旧值
            if obj_id and 'edit' in func.__name__:
                try:
                    obj = model_class.query.get(obj_id)
                    if obj:
                        old_values = ChangeTracker.capture_old_values(obj, fields)
                except:
                    pass
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 在函数执行后记录变更
            try:
                if 'create' in func.__name__ or 'add' in func.__name__:
                    # 创建操作 - 需要从结果或数据库中获取新创建的对象
                    if obj_id:
                        obj = model_class.query.get(obj_id)
                        if obj:
                            ChangeTracker.log_create(obj)
                elif 'edit' in func.__name__ or 'update' in func.__name__:
                    # 更新操作
                    if obj_id and old_values:
                        obj = model_class.query.get(obj_id)
                        if obj:
                            new_values = ChangeTracker.get_new_values(obj, old_values.keys())
                            ChangeTracker.log_update(obj, old_values, new_values)
                elif 'delete' in func.__name__:
                    # 删除操作 - 需要在删除前记录
                    if obj_id:
                        obj = model_class.query.get(obj_id)
                        if obj:
                            ChangeTracker.log_delete(obj)
            except Exception as e:
                print(f"跟踪变更失败: {str(e)}")
            
            return result
        return wrapper
    return decorator 