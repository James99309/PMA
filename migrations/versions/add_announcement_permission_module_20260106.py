"""添加公告管理权限模块

Revision ID: add_announcement_permission_module_20260106
Revises:
Create Date: 2026-01-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import time

# revision identifiers, used by Alembic.
revision = 'add_announcement_permission_module_20260106'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加公告管理权限模块"""
    conn = op.get_bind()
    now = time.time()

    # 检查 announcement 模块是否已存在
    existing = conn.execute(text(
        "SELECT id FROM permission_modules WHERE module_id = 'announcement'"
    )).fetchone()

    if existing:
        print("- 公告管理模块已存在，跳过")
        return

    # 添加 announcement 模块
    conn.execute(text("""
        INSERT INTO permission_modules
        (module_id, name, name_en, icon, description, description_en,
         group_name, group_name_en, sort_order,
         supports_discount, supports_owner_change, supports_affiliation, supports_content_filter,
         is_active, created_at, updated_at)
        VALUES
        ('announcement', '公告管理', 'Announcement', 'campaign',
         '管理系统公告', 'Manage system announcements',
         '系统管理', 'System', 22,
         false, false, false, false,
         true, :now, :now)
    """), {'now': now})

    print("✓ 添加公告管理权限模块")


def downgrade():
    """移除公告管理权限模块"""
    conn = op.get_bind()

    # 删除模块
    conn.execute(text(
        "DELETE FROM permission_modules WHERE module_id = 'announcement'"
    ))

    print("✓ 移除公告管理权限模块")
