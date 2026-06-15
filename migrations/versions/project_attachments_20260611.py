"""add attachments column to projects (通用实体附件)

给 projects 增加 attachments 列(Text/JSON: [{filename,url,size,type,uploaded_at,uploaded_by,uploaded_by_name}]),
供通用实体附件上传(/api/attachments/project/<id>)使用。

幂等:本地开发库已手动 ADD COLUMN,生产无此列 → 用 IF NOT EXISTS,两边 upgrade 都安全。

Revision ID: project_attachments_20260611
Revises: 7aeb7caaae8c
Create Date: 2026-06-11

"""
from alembic import op

revision = 'project_attachments_20260611'
down_revision = '7aeb7caaae8c'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS attachments TEXT")


def downgrade():
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS attachments")
