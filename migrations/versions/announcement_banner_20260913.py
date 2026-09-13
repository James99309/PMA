"""announcements 加首页横幅两列

仪表盘顶部通栏改为轮播多条通知,内容来自公告系统。
  show_on_banner  勾选后这条公告出现在横幅上(默认 false:存量公告不会突然冒到首页)
  banner_link     点击跳转地址;为空 = 纯告知,渲染成不可点的文字

非破坏性:加 2 列。幂等 IF NOT EXISTS(重复跑不报错)。

Revision ID: announcement_banner_20260913
Revises: course_cover_url_20260730
Create Date: 2026-09-13
"""
from alembic import op


revision = 'announcement_banner_20260913'
down_revision = 'course_cover_url_20260730'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE announcements ADD COLUMN IF NOT EXISTS show_on_banner BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE announcements ADD COLUMN IF NOT EXISTS banner_link VARCHAR(500)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_announcements_show_on_banner ON announcements (show_on_banner)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_announcements_show_on_banner")
    op.execute("ALTER TABLE announcements DROP COLUMN IF EXISTS banner_link")
    op.execute("ALTER TABLE announcements DROP COLUMN IF EXISTS show_on_banner")
