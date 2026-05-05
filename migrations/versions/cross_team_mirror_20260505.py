"""add cross-team mirror columns to users (Federation Lite)

Revision ID: cross_team_mirror_20260505
Revises: xlsx_skill_system_20260420
Create Date: 2026-05-05

Context
-------
跨系统协作 Phase 1：用户身份联邦 Lite。

CN admin 把用户标为「海外支持」(cross_team_visible=true) → 后端自动调 SG NAS
的 /cross-sync/mirror_user 端点，在 SG users 表创建一行 is_mirror=true 的行，
sync 同样的 password_hash + email + real_name。SG 用户用同样账号密码可登 SG App
查看 SG 数据。SG admin 在自己后台给该 mirror 用户分配角色 / 项目可见范围。

新加 5 列：
- cross_team_visible BOOL DEFAULT FALSE  (本地用户是否对其他系统可见)
- cross_team_label   STRING(50)           (对外身份标签如"海外技术支持")
- source_system      STRING(20)           (本行从哪个系统镜像来 'sp8d'/'ovs', NULL=本地原生)
- source_user_id     INT                  (源系统的 user.id)
- is_mirror          BOOL DEFAULT FALSE   (本行是镜像)
- mirrored_at        FLOAT                (上次同步时间戳)

幂等：使用 IF NOT EXISTS 模式，可在两个 NAS 同一份代码部署。
"""
from alembic import op
import sqlalchemy as sa


revision = 'cross_team_mirror_20260505'
down_revision = 'xlsx_skill_system_20260420'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 新增 5 列（按列名判断是否存在，幂等）
    rows = conn.execute(sa.text("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'users'
          AND column_name IN ('cross_team_visible', 'cross_team_label',
                              'source_system', 'source_user_id', 'is_mirror', 'mirrored_at')
    """)).fetchall()
    existing = {r[0] for r in rows}

    if 'cross_team_visible' not in existing:
        conn.execute(sa.text("ALTER TABLE users ADD COLUMN cross_team_visible BOOLEAN NOT NULL DEFAULT FALSE"))
    if 'cross_team_label' not in existing:
        conn.execute(sa.text("ALTER TABLE users ADD COLUMN cross_team_label VARCHAR(50)"))
    if 'source_system' not in existing:
        conn.execute(sa.text("ALTER TABLE users ADD COLUMN source_system VARCHAR(20)"))
    if 'source_user_id' not in existing:
        conn.execute(sa.text("ALTER TABLE users ADD COLUMN source_user_id INTEGER"))
    if 'is_mirror' not in existing:
        conn.execute(sa.text("ALTER TABLE users ADD COLUMN is_mirror BOOLEAN NOT NULL DEFAULT FALSE"))
    if 'mirrored_at' not in existing:
        conn.execute(sa.text("ALTER TABLE users ADD COLUMN mirrored_at DOUBLE PRECISION"))

    # 唯一索引：同一源系统的 source_user_id 只能 mirror 一次
    conn.execute(sa.text("""
        CREATE UNIQUE INDEX IF NOT EXISTS uk_users_mirror_source
            ON users(source_system, source_user_id) WHERE is_mirror IS TRUE
    """))


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS uk_users_mirror_source"))
    for col in ('cross_team_visible', 'cross_team_label', 'source_system',
                'source_user_id', 'is_mirror', 'mirrored_at'):
        try:
            conn.execute(sa.text(f"ALTER TABLE users DROP COLUMN IF EXISTS {col}"))
        except Exception:
            pass
