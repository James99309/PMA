"""统一的对象锁定调度器。

适用场景:审批流模板配置 `lock_object_on_start=true` 时,需要锁定业务对象
编辑。审批通过/驳回时需要解锁。

设计:
- LOCKABLE_REGISTRY: 每个对象类型一项,声明 model 类、字段名映射、可选的
  lock/unlock handler(用来包装现有专用 helper)。
- lock_object / unlock_object: 单一调度入口,替换 approval_helpers 里散落的
  if-elif 链。
- LockableMixin: 给**未来新模块**继承用,提供标准 4 字段 + lock()/unlock()。
  现有 Project/Quotation/Expense 字段已存在,继续走 handler 路径。

新模块接入(参见 CLAUDE-LOCKING.md):
  1. Model 继承 LockableMixin → 自动有 is_locked/locked_reason/locked_by/locked_at
  2. alembic 加 4 列
  3. LOCKABLE_REGISTRY['xxx'] = {'model': XxModel}
"""
from datetime import datetime
from flask import current_app
from sqlalchemy import Column, Boolean, DateTime, Integer, String, ForeignKey
from app import db


# ─────────────────────────────────────────────────────
# Mixin — 给新模块用(提供标准 4 字段 + lock()/unlock())
# ─────────────────────────────────────────────────────
class LockableMixin:
    """标准锁定字段。

    现有 Project/Quotation 已有同名/相近字段,继续用各自 lock_xxx helper,
    无需继承此 Mixin。新模块继承即可获得 4 字段 + lock()/unlock() 方法。
    """
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_reason = Column(String(200), nullable=True)
    locked_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    locked_at = Column(DateTime, nullable=True)

    def lock(self, reason=None, user_id=None, force=False):
        if self.is_locked and not force:
            return False
        self.is_locked = True
        self.locked_reason = reason or '审批流程进行中，暂时锁定编辑'
        self.locked_by = user_id
        self.locked_at = datetime.now()
        return True

    def unlock(self, user_id=None):
        if not self.is_locked:
            return True
        self.is_locked = False
        self.locked_reason = None
        self.locked_by = None
        self.locked_at = None
        return True


# ─────────────────────────────────────────────────────
# 注册表
# ─────────────────────────────────────────────────────
# 字段:
#   model           — SQLAlchemy Model 类
#   reason_attr     — 锁定原因字段名(None 表示该模型不存原因)
#   lock_handler    — 可选 fn(oid, reason, user_id) -> bool;有则用,否则走通用 mixin 路径
#   unlock_handler  — 可选 fn(oid, user_id) -> bool;有则用
#
# 现有 Project/Quotation/Expense 走 handler(包装旧 lock_xxx,保留原行为);
# 未来用 LockableMixin 的新模块只需声明 'model',不需 handler。
def _get_registry():
    """惰性构建注册表,避免模块循环引用。"""
    from app.models.project import Project
    from app.models.quotation import Quotation
    from app.models.expense import Expense
    from app.models.inventory import PurchaseOrder
    from app.models.sales_order import SalesOrder
    from app.models.pricing_order import PricingOrder

    def _project_lock(oid, reason, uid):
        from app.helpers.project_helpers import lock_project
        return lock_project(project_id=oid, reason=reason, user_id=uid, force=True)

    def _project_unlock(oid, uid):
        from app.helpers.project_helpers import unlock_project
        return unlock_project(oid, uid)

    def _quotation_lock(oid, reason, uid):
        from app.helpers.quotation_helpers import lock_quotation
        return lock_quotation(quotation_id=oid, reason=reason, user_id=uid)

    def _quotation_unlock(oid, uid):
        from app.helpers.quotation_helpers import unlock_quotation
        return unlock_quotation(oid, uid)

    def _expense_lock(oid, reason, uid):
        from app.helpers.approval_helpers import lock_expense
        return lock_expense(oid, uid)  # 现有签名忽略 reason

    def _expense_unlock(oid, uid):
        from app.helpers.approval_helpers import unlock_expense
        return unlock_expense(oid, uid)

    return {
        'project':   {
            'model': Project,        'reason_attr': 'locked_reason',
            'lock_handler': _project_lock,     'unlock_handler': _project_unlock,
        },
        'quotation': {
            'model': Quotation,      'reason_attr': 'lock_reason',
            'lock_handler': _quotation_lock,   'unlock_handler': _quotation_unlock,
        },
        'expense':   {
            'model': Expense,        'reason_attr': None,
            'lock_handler': _expense_lock,     'unlock_handler': _expense_unlock,
        },
        # ── 用 LockableMixin 的新模块(Phase 2):无需 handler,调度器走通用路径 ──
        'purchase_order': {'model': PurchaseOrder, 'reason_attr': 'locked_reason',
                           'lock_handler': None, 'unlock_handler': None},
        'sales_order':    {'model': SalesOrder,    'reason_attr': 'locked_reason',
                           'lock_handler': None, 'unlock_handler': None},
        'pricing_order':  {'model': PricingOrder,  'reason_attr': 'locked_reason',
                           'lock_handler': None, 'unlock_handler': None},
    }


_REGISTRY_CACHE = None


def get_registry():
    """返回 (并缓存) lockable 注册表。"""
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None:
        _REGISTRY_CACHE = _get_registry()
    return _REGISTRY_CACHE


def register_lockable(object_type, model, reason_attr='locked_reason',
                      lock_handler=None, unlock_handler=None):
    """运行时注册(主要给 Phase 2 的 PO/SO/PricingOrder 用)。

    用 LockableMixin 的新模型只需:
        register_lockable('purchase_order', PurchaseOrder)
    无需传 handler — 调度器走 mixin 通用路径。
    """
    reg = get_registry()
    reg[object_type] = {
        'model': model, 'reason_attr': reason_attr,
        'lock_handler': lock_handler, 'unlock_handler': unlock_handler,
    }


# ─────────────────────────────────────────────────────
# 统一调度入口
# ─────────────────────────────────────────────────────
def lock_object(object_type, object_id, reason=None, user_id=None):
    """统一锁定入口。返回 bool 表示是否成功(或对象已锁也视为成功)。

    未注册的 object_type 会记 warning 后返回 True(不阻断审批流程,
    旧的 if-elif 也是这样静默跳过 — 模板可能为 customer 配 lock 但实际无锁)。
    """
    cfg = get_registry().get(object_type)
    if not cfg:
        current_app.logger.warning(
            f'[lockable] object_type={object_type} 未注册,跳过锁定'
        )
        return True

    handler = cfg.get('lock_handler')
    if handler:
        return bool(handler(object_id, reason, user_id))

    # 通用路径(基于 LockableMixin)
    target = cfg['model'].query.get(object_id)
    if not target:
        current_app.logger.warning(
            f'[lockable] {object_type}#{object_id} 不存在,跳过锁定'
        )
        return False
    if hasattr(target, 'lock'):
        ok = target.lock(reason=reason, user_id=user_id, force=True)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'[lockable] 提交锁定失败: {e}')
            return False
        return ok
    current_app.logger.warning(
        f'[lockable] {object_type} 已注册但 model 不支持 .lock(),跳过'
    )
    return False


def unlock_object(object_type, object_id, user_id=None):
    """统一解锁入口。"""
    cfg = get_registry().get(object_type)
    if not cfg:
        current_app.logger.warning(
            f'[lockable] object_type={object_type} 未注册,跳过解锁'
        )
        return True

    handler = cfg.get('unlock_handler')
    if handler:
        return bool(handler(object_id, user_id))

    target = cfg['model'].query.get(object_id)
    if not target:
        return False
    if hasattr(target, 'unlock'):
        ok = target.unlock(user_id=user_id)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'[lockable] 提交解锁失败: {e}')
            return False
        return ok
    return False


def is_object_locked(object_type, object_id):
    """判断对象是否处于锁定状态。未注册或不存在返回 False。"""
    cfg = get_registry().get(object_type)
    if not cfg:
        return False
    target = cfg['model'].query.get(object_id)
    return bool(target and getattr(target, 'is_locked', False))


def get_lock_info(object_type, object_id):
    """返回锁定详情 dict (用于前端展示)。未锁定返回 None。

    dict 结构:
      { 'is_locked': True, 'reason': str|None, 'locked_by_id': int|None,
        'locked_by_name': str|None, 'locked_at': datetime|None }
    """
    cfg = get_registry().get(object_type)
    if not cfg:
        return None
    target = cfg['model'].query.get(object_id)
    if not target or not getattr(target, 'is_locked', False):
        return None

    reason = None
    if cfg.get('reason_attr'):
        reason = getattr(target, cfg['reason_attr'], None)

    locked_by_id = getattr(target, 'locked_by', None)
    locked_at = getattr(target, 'locked_at', None)
    locked_by_name = None
    if locked_by_id:
        from app.models.user import User
        u = User.query.get(locked_by_id)
        if u:
            locked_by_name = u.real_name or u.username

    return {
        'is_locked': True,
        'reason': reason,
        'locked_by_id': locked_by_id,
        'locked_by_name': locked_by_name,
        'locked_at': locked_at,
    }


def can_edit_with_lock(target, current_user):
    """统一的"能否编辑"判断:权限 OK 且(未锁定 or admin)。

    target — 已加载的 model 实例(任何有 is_locked 属性的对象)
    """
    from app.utils.access_control import can_edit_data
    if not can_edit_data(target, current_user):
        return False
    if not getattr(target, 'is_locked', False):
        return True
    return getattr(current_user, 'role', None) == 'admin'
