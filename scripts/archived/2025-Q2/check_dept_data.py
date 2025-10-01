from app import create_app
from app.models.user import User, Affiliation, DataAffiliation
from app.models.user import Permission
app = create_app()
with app.app_context():
    # 查询用户信息
    xuhao = User.query.filter_by(username='xuhao').first()
    fangl = User.query.filter_by(username='fangl').first()
    shengyh = User.query.filter_by(username='shengyh').first()
    print('用户信息:')
    print(f'xuhao: ID={xuhao.id if xuhao else None}, 部门={xuhao.department if xuhao else None}, 角色={xuhao.role if xuhao else None}, 是否部门负责人={xuhao.is_department_manager if xuhao else None}')
    print(f'fangl: ID={fangl.id if fangl else None}, 部门={fangl.department if fangl else None}, 角色={fangl.role if fangl else None}, 是否部门负责人={fangl.is_department_manager if fangl else None}')
    print(f'shengyh: ID={shengyh.id if shengyh else None}, 部门={shengyh.department if shengyh else None}, 角色={shengyh.role if shengyh else None}, 是否部门负责人={shengyh.is_department_manager if shengyh else None}')

    # 查询数据归属关系
    if xuhao and fangl and shengyh:
        # 检查旧的归属关系表
        affiliations_fangl = Affiliation.query.filter_by(owner_id=fangl.id, viewer_id=xuhao.id).all()
        affiliations_shengyh = Affiliation.query.filter_by(owner_id=shengyh.id, viewer_id=xuhao.id).all()
        print('旧归属关系:')
        print(f'xuhao可以查看fangl的数据: {len(affiliations_fangl)>0}, 数量={len(affiliations_fangl)}')
        print(f'xuhao可以查看shengyh的数据: {len(affiliations_shengyh)>0}, 数量={len(affiliations_shengyh)}')

        # 检查新的归属关系表
        data_affiliations_fangl = DataAffiliation.query.filter_by(owner_id=fangl.id, viewer_id=xuhao.id).all()
        data_affiliations_shengyh = DataAffiliation.query.filter_by(owner_id=shengyh.id, viewer_id=xuhao.id).all()
        print('新归属关系:')
        print(f'xuhao可以查看fangl的数据: {len(data_affiliations_fangl)>0}, 数量={len(data_affiliations_fangl)}')
        print(f'xuhao可以查看shengyh的数据: {len(data_affiliations_shengyh)>0}, 数量={len(data_affiliations_shengyh)}')
