from app import create_app
from app.models.user import User
from app.utils.access_control import get_viewable_data
app = create_app()
with app.app_context():
    # 查询用户信息
    xuhao = User.query.filter_by(username='xuhao').first()
    fangl = User.query.filter_by(username='fangl').first()
    shengyh = User.query.filter_by(username='shengyh').first()
    if xuhao and fangl and shengyh:
        # 检查部门成员查看逻辑
        viewable_ids = xuhao.get_viewable_user_ids()
        print(f'xuhao可查看的用户IDs: {viewable_ids}')
        print(f'fangl的ID {fangl.id} 是否在可查看列表中: {fangl.id in viewable_ids}')
        print(f'shengyh的ID {shengyh.id} 是否在可查看列表中: {shengyh.id in viewable_ids}')

        # 检查access_control工具函数
        try:
            viewable_users = get_viewable_data(User, xuhao).all()
            viewable_user_ids = [u.id for u in viewable_users]
            print('get_viewable_data返回的用户数量:', len(viewable_users))
            print(f'fangl的ID {fangl.id} 是否在get_viewable_data结果中: {fangl.id in viewable_user_ids}')
            print(f'shengyh的ID {shengyh.id} 是否在get_viewable_data结果中: {shengyh.id in viewable_user_ids}')
        except Exception as e:
            print(f'get_viewable_data出错: {str(e)}')
            import traceback
            traceback.print_exc()
