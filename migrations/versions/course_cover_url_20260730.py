"""add cover_url to interactive_courses

自定义封面(video/ppt 上传封面 NAS 路径)。非破坏性:加 1 列。幂等 IF NOT EXISTS。

Revision ID: course_cover_url_20260730
Revises: video_source_20260729
Create Date: 2026-07-30
"""
from alembic import op


revision = 'course_cover_url_20260730'
down_revision = 'video_source_20260729'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE interactive_courses ADD COLUMN IF NOT EXISTS cover_url VARCHAR(500)")


def downgrade():
    op.execute("ALTER TABLE interactive_courses DROP COLUMN IF EXISTS cover_url")
