"""移动端通用共享端点 —— 一处实现, 所有可分享模块共用。

复用 web 同源逻辑:
- 候选用户: get_shareable_users_tree(三层公司→部门→账户, 与数据权限解耦)
- 鉴权:    SharingService.can_edit_sharing_settings
- 访问校验: get_viewable_data
- 保存:    SharingMixin.set_shared_users

新增可分享模块只需在 _SHARE_MODELS 加一行(模型类 + model_type)。
"""
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.customer import Company
from app.models.project import Project
from app.utils.access_control import get_viewable_data
from app import db
import logging

logger = logging.getLogger(__name__)

# model 路由名 → (模型类, SharingService model_type)
_SHARE_MODELS = {
    'customer': (Company, 'customer'),
    'project':  (Project,  'project'),
}


def _resolve(model, obj_id, user):
    """返回 (obj, error_response)。校验存在性 + 可见性。"""
    entry = _SHARE_MODELS.get(model)
    if not entry:
        return None, api_response(success=False, code=404, message="不支持的共享类型")
    model_cls, _mt = entry
    obj = model_cls.query.filter_by(id=obj_id, is_deleted=False).first()
    if not obj:
        return None, api_response(success=False, code=404, message="对象不存在")
    if not get_viewable_data(model_cls, user, [model_cls.id == obj_id]).first():
        return None, api_response(success=False, code=403, message="无权访问此对象")
    return obj, None


@api_v1_bp.route('/mobile/sharing/<model>/<int:obj_id>', methods=['GET'])
@jwt_required()
def mobile_sharing_get(model, obj_id):
    """返回共享设置: can_edit / 三层候选树 tree / 已选 selected / home。"""
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    obj, err = _resolve(model, obj_id, user)
    if err:
        return err
    model_type = _SHARE_MODELS[model][1]

    from app.utils.sharing import SharingService, get_shareable_users_tree
    can_edit = SharingService.can_edit_sharing_settings(user, obj, model_type)
    tree = get_shareable_users_tree(user, model_type) if can_edit else []

    return api_response(success=True, data={
        'can_edit': can_edit,
        'tree': tree,
        'home': {
            'company_name': user.company_name or '',
            'department': user.department or '',
        },
        'selected': obj.shared_user_ids or [],
    })


@api_v1_bp.route('/mobile/sharing/<model>/<int:obj_id>', methods=['POST'])
@jwt_required()
def mobile_sharing_save(model, obj_id):
    """保存共享名单 {shared_with_users:[id,...]}。"""
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    obj, err = _resolve(model, obj_id, user)
    if err:
        return err
    model_type = _SHARE_MODELS[model][1]

    from app.utils.sharing import SharingService
    if not SharingService.can_edit_sharing_settings(user, obj, model_type):
        return api_response(success=False, code=403, message="无权编辑此对象的共享设置")

    ids = [int(x) for x in ((request.get_json() or {}).get('shared_with_users') or [])
           if str(x).isdigit()]
    try:
        obj.set_shared_users(ids)
        if hasattr(obj, 'share_enabled'):
            obj.share_enabled = bool(ids)
        db.session.commit()
        return api_response(success=True, message='共享设置已更新',
                            data={'selected': obj.shared_user_ids or []})
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile sharing save error ({model}/{obj_id}): {e}", exc_info=True)
        return api_response(success=False, code=500, message='保存失败')
