"""补锁定所有signed阶段但未锁定的项目

Revision ID: lock_signed_projects_20260205
Revises: unify_performance_targets_constraints
Create Date: 2026-02-05 09:00:00.000000

修复历史数据：31个项目处于signed阶段但is_locked=false
原因：
  - 18个项目是审批系统上线前的历史数据（2024-01 ~ 2025-06）
  - 13个项目通过批价单审批自动推进到signed，但该代码路径缺少自动锁定逻辑
同步修复了 pricing_order_service.py 的 complete_approval 方法
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'lock_signed_projects_20260205'
down_revision = 'add_step_execution_condition_20260129'
branch_labels = None
depends_on = None


def upgrade():
    """将所有 signed 阶段但未锁定的活跃项目补上锁定标记"""
    conn = op.get_bind()

    # 先统计受影响行数
    result = conn.execute(sa.text("""
        SELECT COUNT(*) FROM projects
        WHERE current_stage = 'signed'
          AND is_locked = false
          AND is_active = true
    """))
    count = result.scalar()

    if count > 0:
        conn.execute(sa.text("""
            UPDATE projects
            SET is_locked = true,
                locked_reason = '项目已签约，数据迁移补锁定',
                locked_at = :now
            WHERE current_stage = 'signed'
              AND is_locked = false
              AND is_active = true
        """), {'now': datetime.now()})

        print(f'✅ 已锁定 {count} 个 signed 阶段未锁定的项目')
    else:
        print('ℹ️  没有需要锁定的项目')


def downgrade():
    """回滚：解锁通过此迁移锁定的项目"""
    conn = op.get_bind()

    conn.execute(sa.text("""
        UPDATE projects
        SET is_locked = false,
            locked_reason = NULL,
            locked_by = NULL,
            locked_at = NULL
        WHERE current_stage = 'signed'
          AND locked_reason = '项目已签约，数据迁移补锁定'
    """))
