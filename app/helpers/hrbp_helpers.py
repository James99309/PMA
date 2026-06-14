# -*- coding: utf-8 -*-
"""HRBP 数据隔离 helpers(2026-06-14)

固定规则:角色 hr_manager(非 admin)访问他人**绩效/薪资**时,目标必须在
「该 HRBP 负责的部门」内(Department.hrbp_user_id == 他),否则不可见/不可改。
负责部门在「部门管理」页配置(Department.hrbp_user_id)。

仅作用于 hr_manager 角色;其它角色按原数据范围,不受影响。
"""


def is_hrbp(user):
    return bool(user) and getattr(user, 'role', None) == 'hr_manager'


def hrbp_department_keys(hrbp):
    """该 HRBP 负责的部门集合 {(部门名, 公司名)}。"""
    from app.models.expense import Department
    rows = Department.query.filter_by(hrbp_user_id=hrbp.id).all()
    return {(r.name, r.company_name or '') for r in rows}


def in_hrbp_scope(hrbp, target):
    """target 是否在 hrbp 负责范围内(本人始终可见;无 target 视为不可见)。"""
    if not target:
        return False
    if target.id == hrbp.id:
        return True
    keys = hrbp_department_keys(hrbp)
    return (target.department or '', target.company_name or '') in keys


def hrbp_scope_user_ids(hrbp):
    """该 HRBP 绩效/薪资可见的员工 id 集合(本人 + 负责部门在职成员)。"""
    from app.models.user import User
    ids = {hrbp.id}
    keys = hrbp_department_keys(hrbp)
    for name, comp in keys:
        q = User.query.filter(User.department == name,
                              User.company_name == comp,
                              User._is_active.is_(True))
        ids.update(u.id for u in q.all())
    return ids
