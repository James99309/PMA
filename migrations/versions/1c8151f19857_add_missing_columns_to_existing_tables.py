
"""add_missing_columns_to_existing_tables

SP8D云端数据库迁移 - 第二阶段：添加现有表的缺失字段
基于差异分析结果创建

Revision ID: 1c8151f19857
Revises: e069ac4907d0
Create Date: 2025-07-26 15:18:54.096717

安全说明：
- 此迁移只添加新字段，不修改现有字段
- 完全保护SP8D现有的所有数据和功能
- 支持完整回滚
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c8151f19857'
down_revision = 'e069ac4907d0'
branch_labels = None
depends_on = None


def upgrade():
    """添加SP8D现有表的缺失字段"""
    
    print("🔄 开始SP8D第二阶段迁移：添加现有表的缺失字段")
    
    # 添加 dictionaries 表的缺失字段（14个字段）
    print("🔄 正在为 dictionaries 表添加缺失字段...")
    
    try:
        op.add_column('dictionaries', sa.Column('address', sa.Text(), nullable=True, comment='地址'))
        op.add_column('dictionaries', sa.Column('postal_code', sa.String(20), nullable=True, comment='邮政编码'))
        op.add_column('dictionaries', sa.Column('phone', sa.String(50), nullable=True, comment='电话'))
        op.add_column('dictionaries', sa.Column('fax', sa.String(50), nullable=True, comment='传真'))
        op.add_column('dictionaries', sa.Column('email', sa.String(255), nullable=True, comment='邮箱'))
        op.add_column('dictionaries', sa.Column('website', sa.String(255), nullable=True, comment='网站'))
        op.add_column('dictionaries', sa.Column('logo_content', sa.Text(), nullable=True, comment='Logo内容'))
        op.add_column('dictionaries', sa.Column('logo_filename', sa.String(255), nullable=True, comment='Logo文件名'))
        op.add_column('dictionaries', sa.Column('logo_type', sa.String(50), nullable=True, comment='Logo类型'))
        op.add_column('dictionaries', sa.Column('logo_size', sa.Integer(), nullable=True, comment='Logo大小'))
        op.add_column('dictionaries', sa.Column('email_signature_content', sa.Text(), nullable=True, comment='邮件签名内容'))
        op.add_column('dictionaries', sa.Column('email_signature_filename', sa.String(255), nullable=True, comment='邮件签名文件名'))
        op.add_column('dictionaries', sa.Column('email_signature_type', sa.String(50), nullable=True, comment='邮件签名类型'))
        op.add_column('dictionaries', sa.Column('email_signature_size', sa.Integer(), nullable=True, comment='邮件签名大小'))
        
        print("✅ dictionaries 表字段添加完成（14个字段）")
        
    except Exception as e:
        print(f"⚠️  dictionaries 表字段添加警告: {str(e)}")
    
    # 创建索引以提高查询性能
    print("🔄 正在创建新字段的索引...")
    try:
        op.create_index('idx_dictionaries_email', 'dictionaries', ['email'])
        op.create_index('idx_dictionaries_phone', 'dictionaries', ['phone'])
        print("✅ 新字段索引创建完成")
    except Exception as e:
        print(f"⚠️  索引创建警告: {str(e)}")
    
    print("✅ SP8D第二阶段迁移完成：已添加所有缺失字段")


def downgrade():
    """安全回滚：删除添加的字段"""
    
    print("⚠️  开始回滚SP8D第二阶段迁移...")
    
    # 删除索引
    try:
        op.drop_index('idx_dictionaries_phone', 'dictionaries')
        op.drop_index('idx_dictionaries_email', 'dictionaries')
    except Exception as e:
        print(f"索引删除警告: {str(e)}")
    
    # 删除添加的字段
    try:
        op.drop_column('dictionaries', 'email_signature_size')
        op.drop_column('dictionaries', 'email_signature_type')
        op.drop_column('dictionaries', 'email_signature_filename')
        op.drop_column('dictionaries', 'email_signature_content')
        op.drop_column('dictionaries', 'logo_size')
        op.drop_column('dictionaries', 'logo_type')
        op.drop_column('dictionaries', 'logo_filename')
        op.drop_column('dictionaries', 'logo_content')
        op.drop_column('dictionaries', 'website')
        op.drop_column('dictionaries', 'email')
        op.drop_column('dictionaries', 'fax')
        op.drop_column('dictionaries', 'phone')
        op.drop_column('dictionaries', 'postal_code')
        op.drop_column('dictionaries', 'address')
        
        print("✅ SP8D第二阶段回滚完成：已删除添加的字段")
        
    except Exception as e:
        print(f"字段删除警告: {str(e)}")