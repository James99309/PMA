from app import create_app, db
from app.models.user import User
from app.api.v1.affiliations import get_available_users_for_owner
import json
from flask import jsonify

app = create_app()

# 1. 检查所有用户状态
with app.app_context():
    users = User.query.all()
    print("=== 用户数据检查 ===")
    print("id | username | real_name | company_name | department | is_department_manager | is_active")
    for u in users:
        print(f'{u.id} | {u.username} | {u.real_name} | {u.company_name} | {u.department} | {u.is_department_manager} | {u.is_active}')
    
    # 2. 检查xuhao(假设ID为7)的详细信息
    xuhao = User.query.filter_by(username='xuhao').first() or User.query.get(7)
    if xuhao:
        print("\n=== xuhao(徐昊)详细信息 ===")
        print(f"ID: {xuhao.id}")
        print(f"用户名: {xuhao.username}")
        print(f"真实姓名: {xuhao.real_name}")
        print(f"所属公司: {xuhao.company_name}")
        print(f"所属部门: {xuhao.department}")
        print(f"是否部门负责人: {xuhao.is_department_manager}")
        print(f"是否激活: {xuhao.is_active}")
    
    # 3. 检查department和company_name一致的用户
    if xuhao:
        print("\n=== 与xuhao同部门同公司用户 ===")
        same_dept_users = User.query.filter_by(
            department=xuhao.department, 
            company_name=xuhao.company_name
        ).all()
        
        for u in same_dept_users:
            if u.id != xuhao.id:  # 排除自己
                print(f"{u.id} | {u.username} | {u.real_name} | {u.department} | {u.company_name} | {u.is_active}")
    
    # 4. 手动测试API函数
    print("\n=== 手动调用API函数 ===")
    try:
        with app.test_request_context():
            # 创建请求上下文
            if xuhao:
                # 模拟JWT身份
                app.config['JWT_IDENTITY_CALLBACK'] = lambda: str(1)  # admin用户ID
                
                # 调用API函数
                api_response = get_available_users_for_owner(xuhao.id)
                
                # 尝试将Response对象转为字典
                if hasattr(api_response, 'get_json'):
                    api_data = api_response.get_json()
                    print(f"API响应: {json.dumps(api_data, indent=2, ensure_ascii=False)}")
                else:
                    print(f"API原始响应: {api_response}")
    except Exception as e:
        print(f"API调用异常: {str(e)}")
        import traceback
        traceback.print_exc() 