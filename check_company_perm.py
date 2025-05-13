from app import create_app
from app.models.user import User
from app.models.customer import Company
app = create_app()
with app.app_context():
    # 获取用户
    xuhao = User.query.filter_by(username='xuhao').first()
    fangl = User.query.filter_by(username='fangl').first()
    shengyh = User.query.filter_by(username='shengyh').first()
    if xuhao and fangl and shengyh:
        print(f'用户信息:')
        print(f'xuhao: ID={xuhao.id}, 部门={xuhao.department}, 公司={xuhao.company_name}, 角色={xuhao.role}')
        print(f'fangl: ID={fangl.id}, 部门={fangl.department}, 公司={fangl.company_name}, 角色={fangl.role}')
        print(f'shengyh: ID={shengyh.id}, 部门={shengyh.department}, 公司={shengyh.company_name}, 角色={shengyh.role}')
        # 检查部门是否匹配
        same_dept = xuhao.department == fangl.department and xuhao.department == shengyh.department
        same_company = xuhao.company_name == fangl.company_name and xuhao.company_name == shengyh.company_name
        print(f'是否同部门: {same_dept}, 是否同公司: {same_company}')
        # 检查客户数据权限
        print('检查部门员工的客户数据:')
        fangl_companies = Company.query.filter_by(owner_id=fangl.id).all()
        shengyh_companies = Company.query.filter_by(owner_id=shengyh.id).all()
        print(f'fangl的客户数量: {len(fangl_companies)}')
        print(f'shengyh的客户数量: {len(shengyh_companies)}')
