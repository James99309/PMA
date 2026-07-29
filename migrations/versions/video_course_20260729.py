"""add video/ppt media fields to interactive_courses

互动课程增加内容类型分流:media_type(html/video/ppt) + media_url/duration/file_size/chapters。
非破坏性:只给现有表加列,存量行 media_type 默认 'html' 行为不变。
幂等:ADD COLUMN IF NOT EXISTS,可重复执行(应对 create_all 抢建表与多 head 场景)。

Revision ID: video_course_20260729
Revises: pricing_facevalue_backfill_20260715
Create Date: 2026-07-29
"""
from alembic import op


revision = 'video_course_20260729'
down_revision = 'pricing_facevalue_backfill_20260715'
branch_labels = None
depends_on = None


# (列名, 类型, 默认值 SQL 片段 or None)
_COLS = [
    ('media_type', "VARCHAR(20) NOT NULL DEFAULT 'html'"),
    ('media_url', 'VARCHAR(500)'),
    ('duration', 'INTEGER'),
    ('file_size', 'INTEGER'),
    ('chapters', 'TEXT'),
]


def upgrade():
    for name, ddl in _COLS:
        op.execute(f'ALTER TABLE interactive_courses ADD COLUMN IF NOT EXISTS {name} {ddl}')


def downgrade():
    for name, _ in _COLS:
        op.execute(f'ALTER TABLE interactive_courses DROP COLUMN IF EXISTS {name}')
