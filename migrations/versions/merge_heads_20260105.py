"""merge multiple heads

Revision ID: merge_heads_20260105
Revises: add_ai_analysis_cache_20251230, add_ai_config_fields, add_announcements_20260105, add_contact_20260103, add_end_date_20260103, add_expense_budget_20251227, add_filter_dictionaries_20251228, add_formula_builder_20251229, add_mention_20260103, add_messages_20260104, add_monthly_targets_20251228, add_permission_modules_20251228, add_report_read_col, add_role_expense_budget_20251228, add_role_performance_targets_20251228, add_salary_config_tables_20251228, add_salary_period_snapshots_20251230, add_shared_users_20260103, add_version_first_used_at, add_worklog_20260102, add_year_to_salary_config, preserve_orphaned_config_values_20251225, remove_ai_prompt_fields
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads_20260105'
down_revision = ('add_ai_analysis_cache_20251230', 'add_ai_config_fields', 'add_announcements_20260105', 'add_contact_20260103', 'add_end_date_20260103', 'add_expense_budget_20251227', 'add_filter_dictionaries_20251228', 'add_formula_builder_20251229', 'add_mention_20260103', 'add_messages_20260104', 'add_monthly_targets_20251228', 'add_permission_modules_20251228', 'add_report_read_col', 'add_role_expense_budget_20251228', 'add_role_performance_targets_20251228', 'add_salary_config_tables_20251228', 'add_salary_period_snapshots_20251230', 'add_shared_users_20260103', 'add_version_first_used_at', 'add_worklog_20260102', 'add_year_to_salary_config', 'preserve_orphaned_config_values_20251225', 'remove_ai_prompt_fields')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
