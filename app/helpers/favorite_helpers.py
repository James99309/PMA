# -*- coding: utf-8 -*-
"""个人关注(收藏)helpers。

关注是纯个人书签:只认 user_id,不改变任何可见性。
  - 写入前校验"你本来就能看到这个对象"(不能关注看不见的东西)
  - 读取侧一律配合 get_viewable_data 使用:对象后来移出你的权限范围 → 自动不显示

对象类型注册表 _OBJ 是唯一扩展点:以后给客户/报价单加关注,只在这里加一行。
"""
from app import db
from app.models.favorite import UserFavorite

FAV_PROJECT = 'project'
FAV_CUSTOMER = 'customer'
FAV_QUOTATION = 'quotation'


def _can_view_project(user, obj_id):
    from app.models.project import Project
    from app.utils.access_control import can_view_project
    p = Project.query.filter_by(id=obj_id, is_deleted=False).first()
    return bool(p) and can_view_project(user, p)


def _can_view_customer(user, obj_id):
    from app.models.customer import Company
    from app.utils.access_control import can_view_company
    c = Company.query.filter_by(id=obj_id, is_deleted=False).first()
    return bool(c) and can_view_company(user, c)


def _can_view_quotation(user, obj_id):
    from app.models.quotation import Quotation
    from app.utils.access_control import can_view_quotation
    q = Quotation.query.filter_by(id=obj_id).first()   # 报价单无 is_deleted 字段
    return bool(q) and can_view_quotation(user, q)


# object_type → 可见性校验函数(新增关注对象只需在此登记一行)
_OBJ = {
    FAV_PROJECT: _can_view_project,
    FAV_CUSTOMER: _can_view_customer,
    FAV_QUOTATION: _can_view_quotation,
}


def is_supported(object_type):
    return object_type in _OBJ


def favorite_ids(user_id, object_type):
    """该用户关注的对象 id 集合(一次查询;列表页批量判定用,避免 N+1)。"""
    rows = db.session.query(UserFavorite.object_id).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.object_type == object_type,
    ).all()
    return {r[0] for r in rows}


def is_favorited(user_id, object_type, object_id):
    return db.session.query(UserFavorite.id).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.object_type == object_type,
        UserFavorite.object_id == object_id,
    ).first() is not None


def toggle_favorite(user, object_type, object_id):
    """点亮/熄灭关注。Returns (favorited: bool | None, err_code: str | None)。

    err_code 是稳定的机器码('unsupported' / 'forbidden'),由调用方翻译成文案 ——
    helper 里不放可翻译字符串(Babel 提取不到运行期变量)。"""
    checker = _OBJ.get(object_type)
    if not checker:
        return None, 'unsupported'
    if not checker(user, object_id):
        return None, 'forbidden'

    row = UserFavorite.query.filter_by(
        user_id=user.id, object_type=object_type, object_id=object_id).first()
    if row:
        db.session.delete(row)
        db.session.commit()
        return False, None

    db.session.add(UserFavorite(user_id=user.id, object_type=object_type,
                                object_id=object_id))
    try:
        db.session.commit()
    except Exception:
        # 并发双击 → 唯一约束冲突;此时已是"已关注",按幂等处理
        db.session.rollback()
        if is_favorited(user.id, object_type, object_id):
            return True, None
        raise
    return True, None
