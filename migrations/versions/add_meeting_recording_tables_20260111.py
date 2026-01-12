"""Add meeting recording and minutes tables

Revision ID: add_meeting_recording_tables_20260111
Revises: d2731c6921bb
Create Date: 2026-01-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_meeting_recording_tables_20260111'
down_revision = 'd2731c6921bb'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. 创建 meeting_recordings 表 - 会议录音记录
    if 'meeting_recordings' not in existing_tables:
        op.create_table('meeting_recordings',
            sa.Column('id', sa.Integer(), primary_key=True),
            # 关联的工作项（可选）
            sa.Column('work_item_id', sa.Integer(), sa.ForeignKey('work_items.id'), nullable=True),
            # 会议基本信息
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('meeting_time', sa.DateTime(), nullable=False),
            # 录音信息
            sa.Column('recording_mode', sa.String(50), nullable=True),
            sa.Column('duration_seconds', sa.Integer(), server_default='0'),
            sa.Column('file_size_bytes', sa.Integer(), server_default='0'),
            sa.Column('storage_path', sa.String(500), nullable=True),
            sa.Column('storage_url', sa.String(1000), nullable=True),
            # 分块上传
            sa.Column('total_chunks', sa.Integer(), server_default='0'),
            sa.Column('uploaded_chunks', sa.Integer(), server_default='0'),
            sa.Column('chunk_paths', sa.Text(), nullable=True),  # JSON
            # 状态
            sa.Column('status', sa.String(20), server_default='recording'),
            sa.Column('error_message', sa.Text(), nullable=True),
            # 系统字段
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('is_deleted', sa.Boolean(), server_default='false'),
        )
        op.create_index('idx_meeting_recordings_work_item', 'meeting_recordings', ['work_item_id'])
        op.create_index('idx_meeting_recordings_status', 'meeting_recordings', ['status'])
        op.create_index('idx_meeting_recordings_owner', 'meeting_recordings', ['owner_id'])

    # 2. 创建 meeting_transcripts 表 - 转录文本
    if 'meeting_transcripts' not in existing_tables:
        op.create_table('meeting_transcripts',
            sa.Column('id', sa.Integer(), primary_key=True),
            # 关联录音
            sa.Column('recording_id', sa.Integer(), sa.ForeignKey('meeting_recordings.id'), nullable=False, unique=True),
            # 转录状态
            sa.Column('status', sa.String(20), server_default='pending'),
            sa.Column('progress_percent', sa.Integer(), server_default='0'),
            sa.Column('error_message', sa.Text(), nullable=True),
            # 转录结果
            sa.Column('full_text', sa.Text(), nullable=True),
            sa.Column('segments', sa.Text(), nullable=True),  # JSON
            sa.Column('language', sa.String(10), server_default='zh'),
            # 说话人识别
            sa.Column('speaker_count', sa.Integer(), server_default='0'),
            sa.Column('speakers_mapped', sa.Boolean(), server_default='false'),
            # 系统字段
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
        )
        op.create_index('idx_meeting_transcripts_status', 'meeting_transcripts', ['status'])

    # 3. 创建 meeting_speakers 表 - 说话人信息
    if 'meeting_speakers' not in existing_tables:
        op.create_table('meeting_speakers',
            sa.Column('id', sa.Integer(), primary_key=True),
            # 关联转录
            sa.Column('transcript_id', sa.Integer(), sa.ForeignKey('meeting_transcripts.id'), nullable=False),
            # 说话人标识
            sa.Column('speaker_label', sa.String(50), nullable=False),
            # 映射的用户
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('external_name', sa.String(100), nullable=True),
            # 示例发言
            sa.Column('sample_text', sa.Text(), nullable=True),
            sa.Column('sample_start_time', sa.Float(), nullable=True),
            sa.Column('sample_end_time', sa.Float(), nullable=True),
            # 统计
            sa.Column('total_duration_seconds', sa.Float(), server_default='0'),
            sa.Column('segment_count', sa.Integer(), server_default='0'),
            # 系统字段
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('idx_meeting_speakers_transcript', 'meeting_speakers', ['transcript_id'])

    # 4. 创建 meeting_minutes 表 - 会议纪要
    if 'meeting_minutes' not in existing_tables:
        op.create_table('meeting_minutes',
            sa.Column('id', sa.Integer(), primary_key=True),
            # 关联录音
            sa.Column('recording_id', sa.Integer(), sa.ForeignKey('meeting_recordings.id'), nullable=False, unique=True),
            # 纪要状态
            sa.Column('status', sa.String(20), server_default='generating'),
            sa.Column('version', sa.Integer(), server_default='1'),
            # 纪要内容
            sa.Column('title', sa.String(200), nullable=True),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('key_points', sa.Text(), nullable=True),  # JSON
            sa.Column('decisions', sa.Text(), nullable=True),  # JSON
            # 参与者
            sa.Column('participants', sa.Text(), nullable=True),  # JSON
            # 关联
            sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=True),
            sa.Column('customer_id', sa.Integer(), sa.ForeignKey('companies.id'), nullable=True),
            # 生成配置
            sa.Column('generation_mode', sa.String(20), server_default='standard'),
            # 系统字段
            sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), server_default='false'),
        )
        op.create_index('idx_meeting_minutes_status', 'meeting_minutes', ['status'])
        op.create_index('idx_meeting_minutes_owner', 'meeting_minutes', ['owner_id'])

    # 5. 创建 meeting_action_items 表 - 行动项
    if 'meeting_action_items' not in existing_tables:
        op.create_table('meeting_action_items',
            sa.Column('id', sa.Integer(), primary_key=True),
            # 关联纪要
            sa.Column('minutes_id', sa.Integer(), sa.ForeignKey('meeting_minutes.id'), nullable=False),
            # 行动项内容
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            # 负责人
            sa.Column('assignee_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('assignee_name', sa.String(100), nullable=True),
            # 时间
            sa.Column('due_date', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            # 状态
            sa.Column('status', sa.String(20), server_default='pending'),
            # 关联工作项
            sa.Column('linked_work_item_id', sa.Integer(), sa.ForeignKey('work_items.id'), nullable=True),
            # 系统字段
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('is_deleted', sa.Boolean(), server_default='false'),
        )
        op.create_index('idx_meeting_action_items_minutes', 'meeting_action_items', ['minutes_id'])
        op.create_index('idx_meeting_action_items_assignee', 'meeting_action_items', ['assignee_id'])
        op.create_index('idx_meeting_action_items_status', 'meeting_action_items', ['status'])


def downgrade():
    # 按创建的反序删除表
    op.drop_table('meeting_action_items')
    op.drop_table('meeting_minutes')
    op.drop_table('meeting_speakers')
    op.drop_table('meeting_transcripts')
    op.drop_table('meeting_recordings')
