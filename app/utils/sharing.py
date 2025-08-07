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
        # 管理员和管理角色有全部权限
        if user.role in ['admin', 'product_manager', 'solution_manager', 'finance_director']:
            return True
        
        # 数据拥有者可以编辑
        if hasattr(data_obj, 'owner_id') and data_obj.owner_id == user.id:
            return True
        
        # 模型特定的权限检查
        if model_type == 'project':
            # 项目厂商销售负责人可以编辑
            if hasattr(data_obj, 'vendor_sales_manager_id') and data_obj.vendor_sales_manager_id == user.id:
                return True
        
        elif model_type == 'company':
            # 客户的归属关系权限检查
            from app.models.user import Affiliation
            affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
            if data_obj.owner_id in [aff.owner_id for aff in affiliations]:
                return True
            
            # 商务助理的部门权限
            if user.role.strip() == 'business_admin' and user.department and user.company_name:
                from app.models.user import User
                data_owner = User.query.get(data_obj.owner_id)
                if (data_owner and data_owner.department == user.department and 
                    data_owner.company_name == user.company_name):
                    return True
        
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
    
    参数:
        current_user: 当前用户
        model_type: 模型类型（用于特定的用户筛选）
        
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
    
    # 根据用户角色和模型类型进一步筛选
    if current_user.role == 'admin':
        # 管理员可以共享给所有用户
        return base_query
    
    elif current_user.company_name:
        # 同公司用户
        company_users = base_query.filter(User.company_name == current_user.company_name)
        
        # 根据模型类型进一步限制
        if model_type in ['project', 'quotation']:
            # 项目和报价单：限制为同公司的业务相关用户
            business_roles = ['sales', 'sales_manager', 'sales_director', 'business_admin', 
                            'product_manager', 'solution_manager', 'channel_manager', 'admin']
            business_users = company_users.filter(User.role.in_(business_roles))
            
            # 如果没有找到业务相关用户，返回同公司所有用户作为备选
            if business_users.count() == 0:
                logger.info(f"未找到同公司的业务相关用户，返回同公司所有用户")
                return company_users
            else:
                return business_users
        else:
            # 其他类型：同公司所有用户
            return company_users
    
    else:
        # 无公司信息的用户，返回所有活跃用户（更宽松的策略）
        logger.info(f"用户 {current_user.username} 无公司信息，返回所有活跃用户")
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
    
    for user in shareable_users:
        company_name = user.company_name or _('未指定公司')
        department = user.department or None
        
        # 创建公司节点
        if company_name not in company_tree:
            company_tree[company_name] = {
                'id': f'company_{hash(company_name) % 10000}',
                'name': company_name,
                'type': 'company',
                'selectable': True,
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