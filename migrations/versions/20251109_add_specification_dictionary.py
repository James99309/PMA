"""添加规格字典表

Revision ID: 20251109_spec_dict
Revises: 20251104_config_type
Create Date: 2025-11-09

业务说明:
- 创建规格字典表，用于标准化产品规格名称
- 提供常用规格名称的输入建议，避免重复录入和拼写不一致
- 作为独立的参考数据，不影响现有产品规格数据结构

功能特性:
1. 规格名称标准化 - 统一管理常用规格名称（如"频率范围"、"输出功率"等）
2. 单位管理 - 记录每个规格对应的标准单位（如"MHz"、"dBm"等）
3. 启用/停用控制 - 支持停用不常用的规格，保持字典整洁
4. 输入建议 - 前端可调用此字典提供自动完成功能

表结构:
- id: 主键
- name: 规格名称（唯一）
- unit: 单位（可选）
- is_active: 是否启用
- created_at: 创建时间

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20251109_spec_dict'
down_revision = '20251104_config_type'
branch_labels = None
depends_on = None


def upgrade():
    """创建规格字典表并添加初始数据"""
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # 检查表是否已存在
    if 'specification_dictionary' not in existing_tables:
        # 创建 specification_dictionary 表
        op.create_table('specification_dictionary',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('unit', sa.String(length=20), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        print("✅ specification_dictionary 表创建成功")

        # 添加索引提升查询性能
        op.create_index('idx_spec_dict_active', 'specification_dictionary', ['is_active'], unique=False)
        op.create_index('idx_spec_dict_name', 'specification_dictionary', ['name'], unique=True)
        print("✅ 创建索引成功")

        # 插入初始常用规格数据
        from sqlalchemy.sql import table, column
        from sqlalchemy import String, Integer, Boolean, DateTime

        spec_dict_table = table('specification_dictionary',
            column('name', String),
            column('unit', String),
            column('is_active', Boolean),
            column('created_at', DateTime)
        )

        initial_specs = [
            {'name': '频率范围', 'unit': 'MHz', 'is_active': True},
            {'name': '输出功率', 'unit': 'dBm', 'is_active': True},
            {'name': '工作温度', 'unit': '℃', 'is_active': True},
            {'name': '接口类型', 'unit': None, 'is_active': True},
            {'name': '防护等级', 'unit': None, 'is_active': True},
            {'name': '工作电压', 'unit': 'V', 'is_active': True},
            {'name': '尺寸', 'unit': 'mm', 'is_active': True},
            {'name': '重量', 'unit': 'kg', 'is_active': True},
            {'name': '增益', 'unit': 'dB', 'is_active': True},
            {'name': '带宽', 'unit': 'MHz', 'is_active': True},
            {'name': '噪声系数', 'unit': 'dB', 'is_active': True},
            {'name': '功耗', 'unit': 'W', 'is_active': True},
            {'name': '存储温度', 'unit': '℃', 'is_active': True},
            {'name': '湿度范围', 'unit': '%RH', 'is_active': True},
            {'name': '传输距离', 'unit': 'm', 'is_active': True},
        ]

        # 添加创建时间并批量插入
        current_time = datetime.utcnow()
        for spec in initial_specs:
            spec['created_at'] = current_time

        op.bulk_insert(spec_dict_table, initial_specs)

        print(f"✅ 已添加 {len(initial_specs)} 条初始规格数据")
    else:
        print("⏭️ specification_dictionary 表已存在，跳过创建")

        # 检查索引是否存在
        result = bind.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'specification_dictionary' AND indexname = 'idx_spec_dict_active'"))
        if not result.fetchone():
            op.create_index('idx_spec_dict_active', 'specification_dictionary', ['is_active'], unique=False)
            print("✅ 创建索引 idx_spec_dict_active 成功")

        result = bind.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'specification_dictionary' AND indexname = 'idx_spec_dict_name'"))
        if not result.fetchone():
            op.create_index('idx_spec_dict_name', 'specification_dictionary', ['name'], unique=True)
            print("✅ 创建索引 idx_spec_dict_name 成功")


def downgrade():
    """回滚：删除规格字典表"""

    # 删除索引
    op.drop_index('idx_spec_dict_name', table_name='specification_dictionary')
    op.drop_index('idx_spec_dict_active', table_name='specification_dictionary')

    # 删除表
    op.drop_table('specification_dictionary')

    print("✅ specification_dictionary 表已删除")
