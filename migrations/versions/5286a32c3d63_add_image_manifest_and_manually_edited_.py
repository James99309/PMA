"""add image_manifest and manually_edited to wiki articles

Revision ID: 5286a32c3d63
Revises: settlement_order_notes_20260430
Create Date: 2026-05-03 18:29:00.429181

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5286a32c3d63'
down_revision = 'settlement_order_notes_20260430'
branch_labels = None
depends_on = None


def upgrade():
    """Add image_manifest (JSON) and manually_edited (Boolean) to knowledge_wiki_articles.

    Note: Alembic autogenerate detects unrelated schema drift across the project (see
    pre-existing wiki/RAG migrations and other modules). We intentionally scope this
    migration to only the columns this feature requires, matching the policy in
    docs/plans/2026-05-03-wiki-image-embedding.md (Task 1).
    """
    op.add_column(
        'knowledge_wiki_articles',
        sa.Column('image_manifest', sa.JSON(), nullable=True),
    )
    op.add_column(
        'knowledge_wiki_articles',
        sa.Column(
            'manually_edited',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false'),
        ),
    )


def downgrade():
    op.drop_column('knowledge_wiki_articles', 'manually_edited')
    op.drop_column('knowledge_wiki_articles', 'image_manifest')
