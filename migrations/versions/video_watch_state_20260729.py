"""add video_watch_state table

视频课程观看记录(续播位置 + 看完标志),与培训考核表分离。
非破坏性:只新增 1 张表。幂等:IF NOT EXISTS。

Revision ID: video_watch_state_20260729
Revises: video_course_20260729
Create Date: 2026-07-29
"""
from alembic import op


revision = 'video_watch_state_20260729'
down_revision = 'video_course_20260729'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS video_watch_state (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER NOT NULL REFERENCES users(id),
            course_key    VARCHAR(80) NOT NULL,
            last_position DOUBLE PRECISION NOT NULL DEFAULT 0,
            max_progress  DOUBLE PRECISION NOT NULL DEFAULT 0,
            completed     BOOLEAN NOT NULL DEFAULT FALSE,
            completed_at  TIMESTAMP,
            created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_video_watch_state_user_id ON video_watch_state (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_video_watch_state_course_key ON video_watch_state (course_key)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_vws_user_course ON video_watch_state (user_id, course_key)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS video_watch_state")
