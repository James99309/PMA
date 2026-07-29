"""add video_source to interactive_courses

视频来源分流:webdav(NAS 流,默认) / gdrive(Google Drive iframe,境外绕隧道)。
非破坏性:加 1 列,存量视频默认 webdav 行为不变。幂等 IF NOT EXISTS。

Revision ID: video_source_20260729
Revises: video_watch_state_20260729
Create Date: 2026-07-29
"""
from alembic import op


revision = 'video_source_20260729'
down_revision = 'video_watch_state_20260729'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE interactive_courses ADD COLUMN IF NOT EXISTS video_source VARCHAR(20) DEFAULT 'webdav'")


def downgrade():
    op.execute("ALTER TABLE interactive_courses DROP COLUMN IF EXISTS video_source")
