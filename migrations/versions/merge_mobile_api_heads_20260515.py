"""merge mobile-api + main heads into one

合并 feature/mobile-api 大合并后的 3 个并行 head:
- chat_participant_hidden_20260510 (main 独有 chat 改动)
- mobile_push_token_20260429 (feature/mobile-api 独有, push token 列)
- pma_training_v2_20260513 (main 独有, PMA training v2 表)

空 migration, 不改 schema, 只把 DAG 合并为单 head。

Revision ID: merge_mobile_api_20260515
Revises: chat_participant_hidden_20260510, mobile_push_token_20260429, pma_training_v2_20260513
Create Date: 2026-05-15
"""

# revision identifiers, used by Alembic.
revision = 'merge_mobile_api_20260515'
down_revision = (
    'chat_participant_hidden_20260510',
    'mobile_push_token_20260429',
    'pma_training_v2_20260513',
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
