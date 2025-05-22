from app.models.user import User
from flask_login import current_user
from sqlalchemy import or_
from app.utils.dictionary_helpers import get_role_display_name

def generate_user_tree_data(filter_by_department=False, include_inactive=False):
    """
    生成用户的树状结构数据，用于树状选择控件
    三级结构：企业 -> 部门 -> 用户
    
    参数:
        filter_by_department: 是否仅包含当前用户所在部门的用户
        include_inactive: 是否包含已停用的用户
    
    返回:
        包含树状结构的列表，每项具有id、label和children字段
    """
    # 查询条件
    query = User.query
    
    # 过滤条件
    if not include_inactive:
        query = query.filter(User._is_active == True)
    
    # 按部门过滤
    if filter_by_department and current_user.department:
        query = query.filter(User.department == current_user.department)
    
    # 管理员始终可以看到所有用户
    if current_user.role == 'admin':
        users = query.all()
    # 部门管理员可以看到其部门的所有用户
    elif getattr(current_user, 'is_department_manager', False):
        users = query.filter(User.department == current_user.department).all()
    # 其他用户只能看到自己
    else:
        users = query.filter(User.id == current_user.id).all()
    
    # 组织三级树：企业 -> 部门 -> 用户
    companies = {}
    root_nodes = []
    
    # 首先按企业和部门分组
    for user in users:
        company_name = user.company_name or '未分配企业'
        dept_name = user.department or '未分配部门'
        
        # 确保企业节点存在
        if company_name not in companies:
            companies[company_name] = {
                'id': f'company_{company_name}',
                'label': company_name,
                'is_group': True,
                'children': {}
            }
        
        # 确保部门节点存在
        if dept_name not in companies[company_name]['children']:
            companies[company_name]['children'][dept_name] = {
                'id': f'dept_{company_name}_{dept_name}',
                'label': dept_name,
                'is_group': True,
                'children': []
            }
        
        # 使用get_role_display_name获取角色的显示名称
        role_display = get_role_display_name(user.role)
        
        # 添加用户到对应部门
        companies[company_name]['children'][dept_name]['children'].append({
            'id': user.id,
            'label': f"{user.real_name or user.username}（{role_display}）",
            'is_group': False,
            'children': []
        })
    
    # 转换为最终的树状结构
    # 对企业排序
    sorted_company_names = sorted(companies.keys())
    
    for company_name in sorted_company_names:
        company = companies[company_name]
        company_node = {
            'id': company['id'],
            'label': company['label'],
            'is_group': True,
            'children': []
        }
        
        # 对部门排序
        sorted_dept_names = sorted(company['children'].keys())
        
        for dept_name in sorted_dept_names:
            dept = company['children'][dept_name]
            dept_node = {
                'id': dept['id'],
                'label': dept['label'],
                'is_group': True,
                'children': []
            }
            
            # 对用户按姓名排序
            sorted_users = sorted(dept['children'], key=lambda x: x['label'])
            dept_node['children'] = sorted_users
            
            company_node['children'].append(dept_node)
        
        root_nodes.append(company_node)
    
    return root_nodes 