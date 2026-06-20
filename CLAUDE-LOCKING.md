# PMA 审批锁定统一规范 (Lockable Protocol)

适用于所有接入审批流的业务对象。审批模板配置 `lock_object_on_start=true`
时,提交审批 → 自动锁定;审批通过/驳回 → 自动解锁。

## 架构总览

```
app/utils/lockable.py
├── LOCKABLE_REGISTRY        ← 对象类型 → 配置(model + handler 或 mixin)
├── lock_object(...)         ← 单一锁定入口(approval_helpers 调用它)
├── unlock_object(...)       ← 单一解锁入口
├── is_object_locked(...)    ← 查询
├── get_lock_info(...)       ← 返回锁定详情(reason / locked_by / locked_at)
├── can_edit_with_lock(...)  ← 视图层判定:权限 OK 且(未锁定 or admin)
└── LockableMixin            ← 新模块继承,自动获得 4 字段 + lock()/unlock()
```

**已接入的对象类型**(6 种):
- `project` / `quotation` / `expense` — 用各自老 helper,via `handler` 注册
- `purchase_order` / `sales_order` / `pricing_order` — 用 LockableMixin,via 通用路径

## 新模块接入 5 步

> 假设你要给 `foo_order` 接入。

### 1. Model 继承 `LockableMixin`

```python
# app/models/foo_order.py
from app.utils.lockable import LockableMixin

class FooOrder(LockableMixin, db.Model):  # ← Mixin 放在 db.Model 前
    __tablename__ = 'foo_orders'
    id = Column(Integer, primary_key=True)
    # ...其他字段
```

Mixin 自动提供:
- `is_locked` (Boolean, NOT NULL, default False)
- `locked_reason` (String 200, nullable)
- `locked_by` (Integer FK → users.id, nullable)
- `locked_at` (DateTime, nullable)
- `lock(reason, user_id, force=False)` 方法
- `unlock(user_id)` 方法

### 2. Alembic 迁移加 4 列

```python
# migrations/versions/xxx_lockable_foo_order.py
def upgrade():
    with op.batch_alter_table('foo_orders') as batch_op:
        batch_op.add_column(sa.Column('is_locked', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('locked_reason', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('locked_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('locked_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key('fk_foo_orders_locked_by_users', 'users', ['locked_by'], ['id'])
```

### 3. 注册到 LOCKABLE_REGISTRY

在 `app/utils/lockable.py` 的 `_get_registry()` 里加一行:

```python
from app.models.foo_order import FooOrder
# ...
return {
    # ...
    'foo_order': {'model': FooOrder, 'reason_attr': 'locked_reason',
                  'lock_handler': None, 'unlock_handler': None},
}
```

> **handler=None** 表示走通用路径(基于 Mixin 的 `lock()/unlock()`),你不用写任何锁定函数。
> 只有当对象**已有自己的 lock helper**(像 quotation/project/expense 那样)才需要传 handler。

### 4. 视图层把 `is_locked` 算进 `can_edit`

```python
# app/views/foo_order.py
from app.utils.lockable import can_edit_with_lock

@bp.route('/foo/<int:foo_id>')
def detail_view(foo_id):
    foo = FooOrder.query.get_or_404(foo_id)
    perms = {
        'can_edit': can_edit_with_lock(foo, current_user),  # ← 一行替换
        # ...
    }
```

### 5. 标题旁加锁定 mini pill

对齐 AT 设计语言 — 锁定不用 banner 横条占位,而是在标题旁边、跟状态徽章并列加一个 mini pill,hover 看详细原因/锁定人/时间;编辑按钮由 `can_edit_with_lock` 自动隐藏。

```jinja2
{# foo_order/at_detail.html — 标题行 #}
{% from 'components/at_base.html' import at_icon, at_status_pill %}

<h1>{{ foo.name }}</h1>
{{ at_status_pill(foo.status, scope='foo_order') }}

{% if foo.is_locked %}
{% set _lock_title = (foo.locked_reason or '') ~
                     ( ' · 锁定人 ' ~ (foo.locked_by_user.real_name or foo.locked_by_user.username) if foo.locked_by_user else '' ) ~
                     ( ' · ' ~ foo.locked_at.strftime('%Y-%m-%d %H:%M') if foo.locked_at else '' ) %}
<span title="{{ _lock_title }}"
      style="display:inline-flex;align-items:center;gap:4px;padding:3px 8px;
             border-radius:4px;background:var(--warn-soft);color:var(--warn);
             font-size:11px;font-weight:500;letter-spacing:0.02em;">
  {{ at_icon('lock', 11) }} 已锁定
</span>
{% endif %}
```

参考实现:`app/templates/project/at_view.html` 标题行。

## 审批模板配置

在 `approval_process_template` 表里建 `object_type='foo_order'` 的模板,把
`lock_object_on_start=true` 即可。提交审批时 `approval_helpers.start_approval_process`
会自动调 `lock_object('foo_order', ...)`,审批通过/驳回时调 `unlock_object`。

## 锁定原因字段名兼容

| 对象类型 | 字段名 |
|---|---|
| `project` / `purchase_order` / `sales_order` / `pricing_order` / 新模块 | `locked_reason` |
| `quotation` | `lock_reason`(历史遗留,通过注册表 `reason_attr` 兼容) |
| `expense` | 无(`reason_attr=None`,只有 `is_locked`) |

`at_lock_banner` 宏会自动识别 `locked_reason` / `lock_reason`,模板里直接用即可。

## 改动历史

- **2026-05-29** 创建 Phase 1-4:
  - `app/utils/lockable.py` 调度器 + Mixin
  - `approval_helpers.py` 4 处 if-elif 收敛
  - `purchase_order` / `sales_order` / `pricing_order` 接入(alembic
    `lockable_po_so_pricing_20260529`)
  - 前端 mini pill 方案对接 `at_view_project`(初版尝试过 `at_lock_banner` 横条,
    后改为 mini pill 对齐 AT 设计语言,banner 宏已删除)
