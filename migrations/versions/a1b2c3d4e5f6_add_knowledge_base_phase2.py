"""Add knowledge base phase 2 - tag-based model

Revision ID: a1b2c3d4e5f6
Revises: 429349b8805f
Create Date: 2026-02-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '429349b8805f'
branch_labels = None
depends_on = None


def upgrade():
    # 尝试启用 pgvector 扩展（NAS 环境可能没有安装）
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        has_vector = True
    except Exception:
        has_vector = False
        # 需要在新事务中继续
        from alembic import context
        if not context.is_offline_mode():
            connection = op.get_bind()
            connection.execute(sa.text("ROLLBACK"))
            connection.execute(sa.text("BEGIN"))

    # 删除旧 Phase 1 表（如果存在）
    op.execute("DROP TABLE IF EXISTS knowledge_chat_messages CASCADE")
    op.execute("DROP TABLE IF EXISTS knowledge_chat_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS knowledge_chunks CASCADE")
    op.execute("DROP TABLE IF EXISTS knowledge_documents CASCADE")
    op.execute("DROP TABLE IF EXISTS knowledge_spaces CASCADE")

    # 创建知识库标签表
    op.create_table('knowledge_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 创建知识库文档表
    op.create_table('knowledge_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_library_id', sa.Integer(), nullable=False),
        sa.Column('user_file_ref_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('chunk_count', sa.Integer(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('added_by', sa.Integer(), nullable=False),
        sa.Column('expired_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['added_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['file_library_id'], ['file_library.id'], ),
        sa.ForeignKeyConstraint(['user_file_ref_id'], ['user_file_refs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_docs_status', 'knowledge_documents', ['status'])
    op.create_index('ix_knowledge_docs_file_lib', 'knowledge_documents', ['file_library_id'])
    op.create_index('ix_knowledge_docs_added_by', 'knowledge_documents', ['added_by'])

    # 创建文档-标签多对多关联表
    op.create_table('knowledge_document_tags',
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['knowledge_tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('document_id', 'tag_id')
    )

    # 创建知识库分块表
    op.create_table('knowledge_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_knowledge_chunks_doc_idx', 'knowledge_chunks', ['document_id', 'chunk_index'])

    # 添加 pgvector embedding 列（仅在 pgvector 可用时）
    if has_vector:
        op.execute("ALTER TABLE knowledge_chunks ADD COLUMN embedding vector(1024)")


def downgrade():
    op.drop_table('knowledge_chunks')
    op.drop_table('knowledge_document_tags')
    op.drop_table('knowledge_documents')
    op.drop_table('knowledge_tags')
