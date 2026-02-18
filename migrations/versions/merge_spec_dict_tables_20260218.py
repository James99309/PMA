"""合并 spec_definitions 到 specification_dictionary

给 specification_dictionary 添加定义层字段（name_en, category_id, description 等），
从 spec_definitions 迁移数据，给 spec_template_items 添加 spec_dict_id FK。

Revision ID: a9b8c7d6e5f4
Revises: f7a8b9c0d1e2
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'a9b8c7d6e5f4'
down_revision = 'f7a8b9c0d1e2'
branch_labels = None
depends_on = None


def upgrade():
    # ========== A1: 给 specification_dictionary 加新列 ==========
    op.add_column('specification_dictionary',
                  sa.Column('name_en', sa.String(100), nullable=True))
    op.add_column('specification_dictionary',
                  sa.Column('category_id', sa.Integer(),
                            sa.ForeignKey('spec_categories.id'), nullable=True))
    op.add_column('specification_dictionary',
                  sa.Column('description', sa.Text(), nullable=True))
    op.add_column('specification_dictionary',
                  sa.Column('value_type', sa.String(20), server_default='text', nullable=True))
    op.add_column('specification_dictionary',
                  sa.Column('allow_attachment', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('specification_dictionary',
                  sa.Column('default_test_condition_id', sa.Integer(),
                            sa.ForeignKey('test_condition_dictionary.id'), nullable=True))
    op.add_column('specification_dictionary',
                  sa.Column('default_test_method_id', sa.Integer(),
                            sa.ForeignKey('test_method_dictionary.id'), nullable=True))
    op.add_column('specification_dictionary',
                  sa.Column('updated_at', sa.DateTime(), nullable=True))

    # ========== A2: 从 spec_definitions 迁移数据（74 个名称匹配） ==========
    op.execute("""
        UPDATE specification_dictionary sd SET
            name_en = sdef.name_en,
            category_id = sdef.category_id,
            description = sdef.description,
            value_type = sdef.value_type,
            allow_attachment = sdef.allow_attachment,
            default_test_condition_id = sdef.default_test_condition_id,
            default_test_method_id = sdef.default_test_method_id,
            updated_at = NOW()
        FROM spec_definitions sdef
        WHERE sd.name = sdef.name AND sdef.is_active = true
    """)

    # ========== A3: 补入 48 个独有 spec_definitions ==========
    op.execute("""
        INSERT INTO specification_dictionary (
            name, name_en, unit, category_id, description,
            value_type, allow_attachment, default_test_condition_id,
            default_test_method_id, is_active, display_order, created_at, updated_at
        )
        SELECT
            sdef.name, sdef.name_en, sdef.unit, sdef.category_id, sdef.description,
            sdef.value_type, sdef.allow_attachment, sdef.default_test_condition_id,
            sdef.default_test_method_id, sdef.is_active, sdef.display_order, NOW(), NOW()
        FROM spec_definitions sdef
        WHERE sdef.is_active = true
          AND sdef.name NOT IN (
              SELECT name FROM specification_dictionary WHERE is_active = true
          )
    """)

    # ========== A4: 处理 7 个 unit 不一致 ==========
    op.execute("UPDATE specification_dictionary SET unit = 'dBc' WHERE name = '互调衰减'")
    op.execute("UPDATE specification_dictionary SET unit = 'dB' WHERE name = '增益调节线性'")
    op.execute("UPDATE specification_dictionary SET unit = 'dBm' WHERE name = '最大输出功率'")
    op.execute("UPDATE specification_dictionary SET unit = '℃' WHERE name = '存储温度'")
    op.execute("UPDATE specification_dictionary SET unit = 'dBi' WHERE name = '增益'")

    # ========== A5: 给 spec_template_items 添加 spec_dict_id FK ==========
    op.add_column('spec_template_items',
                  sa.Column('spec_dict_id', sa.Integer(),
                            sa.ForeignKey('specification_dictionary.id'), nullable=True))

    # 通过名称映射填充 spec_dict_id
    op.execute("""
        UPDATE spec_template_items sti SET
            spec_dict_id = sd.id
        FROM spec_definitions sdef
        JOIN specification_dictionary sd ON sd.name = sdef.name
        WHERE sti.definition_id = sdef.id
    """)

    # 创建索引
    op.create_index('ix_specification_dictionary_category_id',
                    'specification_dictionary', ['category_id'])
    op.create_index('ix_spec_template_items_spec_dict_id',
                    'spec_template_items', ['spec_dict_id'])


def downgrade():
    # 移除索引
    op.drop_index('ix_spec_template_items_spec_dict_id', table_name='spec_template_items')
    op.drop_index('ix_specification_dictionary_category_id', table_name='specification_dictionary')

    # 移除 spec_template_items.spec_dict_id
    op.drop_column('spec_template_items', 'spec_dict_id')

    # 移除 specification_dictionary 新列
    op.drop_column('specification_dictionary', 'updated_at')
    op.drop_column('specification_dictionary', 'default_test_method_id')
    op.drop_column('specification_dictionary', 'default_test_condition_id')
    op.drop_column('specification_dictionary', 'allow_attachment')
    op.drop_column('specification_dictionary', 'value_type')
    op.drop_column('specification_dictionary', 'description')
    op.drop_column('specification_dictionary', 'category_id')
    op.drop_column('specification_dictionary', 'name_en')
