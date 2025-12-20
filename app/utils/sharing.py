"""
通用数据共享工具模块
用于处理各种数据模型的用户共享功能
"""

import logging
from flask_login import current_user
from flask import request
from flask_babel import lazy_gettext as _
from sqlalchemy import cast, text, and_, or_
from sqlalchemy.dialects.postgresql import JSONB
from app import db

logger = logging.getLogger(__name__)

class SharingMixin:
    """
    通用共享功能混入类
    为数据模型提供用户共享功能
    
    使用方法：
    1. 在模型中继承此类
    2. 确保模型有 shared_with_users (JSON) 和 share_enabled (Boolean) 字段
    3. 使用提供的方法和属性
    """
    
    @property
    def shared_user_ids(self):
        """获取共享用户ID列表"""
        # 兼容性处理：如果字段不存在，返回空列表
        try:
            if hasattr(self, 'shared_with_users') and self.shared_with_users:
                return self.shared_with_users if isinstance(self.shared_with_users, list) else []
        except Exception:
            pass
        return []
    
    @property
    def is_shared(self):
        """检查是否启用了共享"""
        # 兼容性处理：如果字段不存在，返回False
        try:
            return getattr(self, 'share_enabled', False) and len(self.shared_user_ids) > 0
        except Exception:
            return False
    
    def is_shared_with_user(self, user_id):
        """检查是否共享给了指定用户"""
        try:
            return user_id in self.shared_user_ids
        except Exception:
            return False
    
    def add_shared_user(self, user_id):
        """添加共享用户"""
        try:
            if not hasattr(self, 'shared_with_users'):
                return False
            
            current_users = self.shared_user_ids
            if user_id not in current_users:
                current_users.append(user_id)
                self.shared_with_users = current_users
                return True
            return False
        except Exception:
            return False
    
    def remove_shared_user(self, user_id):
        """移除共享用户"""
        try:
            if not hasattr(self, 'shared_with_users'):
                return False
            
            current_users = self.shared_user_ids
            if user_id in current_users:
                current_users.remove(user_id)
                self.shared_with_users = current_users
                return True
            return False
        except Exception:
            return False
    
    def clear_shared_users(self):
        """清空所有共享用户"""
        try:
            if hasattr(self, 'shared_with_users'):
                self.shared_with_users = []
                return True
            return False
        except Exception:
            return False
    
    def set_shared_users(self, user_ids):
        """设置共享用户列表"""
        try:
            if hasattr(self, 'shared_with_users'):
                self.shared_with_users = user_ids if isinstance(user_ids, list) else []
                return True
            return False
        except Exception:
            return False

class SharingService:
    """
    通用共享服务类
    提供共享相关的查询和操作功能
    """
    
    @staticmethod
    def get_sharing_query_condition(model_class, user_id):
        """
        获取共享数据的查询条件
        
        参数:
            model_class: 数据模型类
            user_id: 用户ID
            
        返回:
            SQLAlchemy查询条件
        """
        # 检查模型是否有共享字段
        try:
            # 尝试访问字段属性，如果不存在会抛出异常
            _ = model_class.shared_with_users
            _ = model_class.share_enabled
        except AttributeError:
            # 字段不存在，返回None
            logger.debug(f"模型 {model_class.__name__} 不支持共享功能（字段不存在）")
            return None
        except Exception as e:
            logger.error(f"检查模型 {model_class.__name__} 共享字段时出错: {e}")
            return None
        
        try:
            return and_(
                model_class.share_enabled == True,
                cast(model_class.shared_with_users, JSONB).op('@>')(text(f"'{user_id}'"))
            )
        except Exception as e:
            logger.error(f"构建共享查询条件时出错: {e}")
            return None
    
    @staticmethod
    def get_shared_data_query(model_class, user, additional_filters=None):
        """
        获取用户可访问的共享数据查询
        
        参数:
            model_class: 数据模型类
            user: 用户对象
            additional_filters: 额外的过滤条件列表
            
        返回:
            查询对象
        """
        if additional_filters is None:
            additional_filters = []
        
        sharing_condition = SharingService.get_sharing_query_condition(model_class, user.id)
        
        if sharing_condition is not None:
            all_filters = [sharing_condition] + additional_filters
            return model_class.query.filter(*all_filters)
        else:
            # 如果模型不支持共享，返回空查询
            return model_class.query.filter(False)
    
    @staticmethod
    def can_edit_sharing_settings(user, data_obj, model_type=None):
        """
        检查用户是否可以编辑指定数据的共享设置
        
        参数:
            user: 用户对象
            data_obj: 数据对象
            model_type: 模型类型（可选，用于特殊权限检查）
            
        返回:
            bool: 是否有权限编辑共享设置
        """
        # 管理员有全部权限
        if user.role == 'admin':
            return True
        
        # 首先检查基本的编辑权限
        from app.utils.access_control import can_edit_data
        if not can_edit_data(data_obj, user):
            return False
        
        # 基本编辑权限检查通过后，进一步检查模块权限和权限级别
        if model_type == 'project':
            # 检查用户是否有项目模块的编辑权限
            if not user.has_permission('project', 'edit'):
                return False
            
            # 检查权限级别
            permission_level = user.get_permission_level('project')
            
            if permission_level == 'system':
                # 系统级权限：可以编辑所有项目的共享设置
                return True
            elif permission_level == 'company' and user.company_name:
                # 企业级权限：可以编辑企业下所有项目的共享设置
                from app.models.user import User
                data_owner = User.query.get(data_obj.owner_id)
                return data_owner and data_owner.company_name == user.company_name
            elif permission_level == 'department' and user.department and user.company_name:
                # 部门级权限：可以编辑部门下所有项目的共享设置
                from app.models.user import User
                data_owner = User.query.get(data_obj.owner_id)
                return (data_owner and data_owner.department == user.department and 
                       data_owner.company_name == user.company_name)
            else:
                # 个人级权限：只能编辑自己的项目或厂商负责的项目（已在can_edit_data中检查）
                return True
        
        elif model_type in ['customer', 'company']:
            # 检查用户是否有客户模块的编辑权限
            if not user.has_permission('customer', 'edit'):
                return False
            
            # 检查权限级别
            permission_level = user.get_permission_level('customer')
            
            if permission_level == 'system':
                # 系统级权限：可以编辑所有客户的共享设置
                return True
            elif permission_level == 'company' and user.company_name:
                # 企业级权限：可以编辑企业下所有客户的共享设置
                from app.models.user import User
                data_owner = User.query.get(data_obj.owner_id)
                return data_owner and data_owner.company_name == user.company_name
            elif permission_level == 'department' and user.department and user.company_name:
                # 部门级权限：可以编辑部门下所有客户的共享设置
                from app.models.user import User
                data_owner = User.query.get(data_obj.owner_id)
                return (data_owner and data_owner.department == user.department and 
                       data_owner.company_name == user.company_name)
            else:
                # 个人级权限：只能编辑自己创建的客户（已在can_edit_data中检查）
                return True
        
        # 其他模型类型或没有指定模型类型时，依赖基本编辑权限检查
        return True

    @staticmethod
    def can_view_sharing_settings(user, data_obj, model_type=None):
        """
        检查用户是否可以查看指定数据的共享设置

        规则：
        1. 如果能编辑共享设置，当然能查看
        2. 管理员可以查看所有
        3. system/company/department 级别权限可以查看对应范围内的数据共享设置
        4. personal 级别只有数据 owner 可以查看

        参数:
            user: 用户对象
            data_obj: 数据对象
            model_type: 模型类型 ('project', 'customer', 'company' 等)

        返回:
            bool: 是否有权限查看共享设置
        """
        # 如果能编辑，当然能查看
        if SharingService.can_edit_sharing_settings(user, data_obj, model_type):
            return True

        # 管理员可以查看所有
        if user.role == 'admin':
            return True

        # 确定模块名称用于权限检查
        if model_type == 'project':
            module_name = 'project'
        elif model_type in ['customer', 'company']:
            module_name = 'customer'
        else:
            module_name = model_type

        # 检查查看权限
        if not module_name or not user.has_permission(module_name, 'view'):
            return False

        # 检查权限级别
        permission_level = user.get_permission_level(module_name)

        if permission_level in ['system', 'company', 'department']:
            # 高级别权限可以查看（但不一定能编辑）
            return True
        elif permission_level == 'personal':
            # personal 级别只有 owner 可以查看
            return hasattr(data_obj, 'owner_id') and data_obj.owner_id == user.id

        return False

    @staticmethod
    def update_sharing_from_request(data_obj, user, model_type=None):
        """
        从请求数据更新共享设置
        
        参数:
            data_obj: 数据对象
            user: 当前用户
            model_type: 模型类型
            
        返回:
            bool: 是否成功更新
        """
        # 检查权限
        if not SharingService.can_edit_sharing_settings(user, data_obj, model_type):
            return False
        
        try:
            # 更新共享启用状态
            if hasattr(data_obj, 'share_enabled'):
                share_enabled = 'share_enabled' in request.form
                data_obj.share_enabled = share_enabled
            
            # 更新共享用户列表
            if hasattr(data_obj, 'shared_with_users'):
                shared_user_ids = request.form.getlist('shared_with_users')
                
                # 如果getlist获取到的是包含逗号的单个字符串，需要进一步分割
                if len(shared_user_ids) == 1 and ',' in shared_user_ids[0]:
                    shared_user_ids = [uid.strip() for uid in shared_user_ids[0].split(',') if uid.strip()]
                elif not shared_user_ids:
                    # 如果getlist没有获取到，尝试从单个字段获取
                    shared_users_str = request.form.get('shared_with_users', '')
                    if shared_users_str:
                        shared_user_ids = [uid.strip() for uid in shared_users_str.split(',') if uid.strip()]
                
                # 转换为整数列表并去重
                shared_user_ids = list(set([int(uid) for uid in shared_user_ids if uid.isdigit()]))
                data_obj.shared_with_users = shared_user_ids
            
            return True
            
        except Exception as e:
            logger.error(f"更新共享设置时出错: {e}")
            return False

def get_shareable_users(current_user, model_type=None):
    """
    获取可以共享给的用户列表
    
    根据业务需求，允许用户将数据分享给系统中的所有活跃用户，
    不受公司边界限制，以支持跨公司协作和灵活的数据共享需求。
    
    参数:
        current_user: 当前用户
        model_type: 模型类型（保留参数以兼容现有调用）
        
    返回:
        用户查询对象
    """
    from app.models.user import User
    
    # 基础查询：排除当前用户，包含活跃用户
    # 活跃用户包括：1. 管理员(role='admin') 2. _is_active=True的用户
    from sqlalchemy import or_
    base_query = User.query.filter(
        User.id != current_user.id,
        or_(
            User.role == 'admin',  # 管理员总是活跃的
            User._is_active == True  # 其他用户根据_is_active字段
        )
    )
    
    # 移除公司限制，允许分享给所有系统中的活跃用户
    # 这样支持：
    # 1. 跨公司业务协作
    # 2. 客户与供应商之间的信息共享
    # 3. 项目中多方参与的协作需求
    # 4. 更灵活的数据共享策略
    
    logger.debug(f"用户 {current_user.username} 可分享给所有系统活跃用户，支持跨公司协作")
    return base_query

def get_shareable_users_tree(current_user, model_type=None):
    """
    获取可共享用户的树状结构数据
    
    返回格式:
    [
        {
            'id': 'company_1',
            'name': '公司A',
            'type': 'company',
            'selectable': True,
            'children': [
                {
                    'id': 'dept_1',
                    'name': '销售部',
                    'type': 'department',
                    'selectable': True,
                    'children': [
                        {'id': 'user_1', 'name': '张三', 'type': 'user', 'user_id': 1}
                    ]
                },
                {'id': 'user_2', 'name': '李四', 'type': 'user', 'user_id': 2} # 无部门用户
            ]
        }
    ]
    """
    # 获取可共享的用户列表
    shareable_users = get_shareable_users(current_user, model_type).all()
    
    if not shareable_users:
        return []
    
    # 按公司和部门组织数据
    company_tree = {}

    # 获取公司厂商信息
    from app.models.dictionary import Dictionary
    company_vendor_info = {}
    company_dicts = Dictionary.query.filter_by(type='company').all()
    for comp_dict in company_dicts:
        company_vendor_info[comp_dict.value] = comp_dict.is_vendor

    for user in shareable_users:
        company_name = user.company_name or _('未指定公司')
        department = user.department or None

        # 创建公司节点
        if company_name not in company_tree:
            # 获取企业的厂商状态
            is_vendor = company_vendor_info.get(company_name, False)
            company_tree[company_name] = {
                'id': f'company_{hash(company_name) % 10000}',
                'name': company_name,
                'type': 'company',
                'selectable': True,
                'is_vendor': is_vendor,
                'children': [],
                'departments': {},
                'direct_users': []
            }
        
        company_node = company_tree[company_name]
        
        if department:
            # 有部门的用户
            if department not in company_node['departments']:
                company_node['departments'][department] = {
                    'id': f'dept_{hash(f"{company_name}_{department}") % 10000}',
                    'name': department,
                    'type': 'department', 
                    'selectable': True,
                    'children': []
                }
            
            # 添加用户到部门
            company_node['departments'][department]['children'].append({
                'id': f'user_{user.id}',
                'name': user.real_name or user.username,
                'type': 'user',
                'selectable': True,
                'user_id': user.id
            })
        else:
            # 无部门的用户直接归属公司
            company_node['direct_users'].append({
                'id': f'user_{user.id}',
                'name': user.real_name or user.username,
                'type': 'user',
                'selectable': True,
                'user_id': user.id
            })
    
    # 构建最终树结构
    result = []
    for company_name, company_data in company_tree.items():
        # 添加部门到公司的children中
        for dept_data in company_data['departments'].values():
            company_data['children'].append(dept_data)
        
        # 添加无部门用户到公司的children中
        company_data['children'].extend(company_data['direct_users'])
        
        # 清理临时字段
        del company_data['departments']
        del company_data['direct_users']
        
        # 按名称排序children
        company_data['children'].sort(key=lambda x: (x['type'] != 'department', x['name']))
        
        result.append(company_data)
    
    # 按公司名称排序
    result.sort(key=lambda x: x['name'])
    
    return result

class SharingPermissionHelper:
    """
    共享权限辅助类
    提供模板中使用的权限检查函数
    """
    
    @staticmethod
    def can_view_shared_data(user, data_obj):
        """检查用户是否可以查看共享的数据"""
        if not hasattr(data_obj, 'is_shared_with_user'):
            return False
        return data_obj.is_shared_with_user(user.id)
    
    @staticmethod
    def can_edit_shared_data(user, data_obj):
        """检查用户是否可以编辑共享的数据（通常共享数据只读）"""
        # 共享数据一般是只读的，只有拥有者可以编辑
        return hasattr(data_obj, 'owner_id') and data_obj.owner_id == user.id

def register_sharing_context_processors(app):
    """
    注册共享相关的上下文处理器
    """
    @app.context_processor
    def inject_sharing_helpers():
        return dict(
            SharingService=SharingService,
            SharingPermissionHelper=SharingPermissionHelper,
            get_shareable_users=get_shareable_users
        )