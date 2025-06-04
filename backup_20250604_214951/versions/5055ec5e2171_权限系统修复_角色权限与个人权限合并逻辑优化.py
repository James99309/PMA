"""权限系统修复 - 角色权限与个人权限合并逻辑优化

本迁移文件记录了权限系统的重要修复，主要解决以下问题：

1. 权限合并逻辑修复
   - 修复了个人权限覆盖角色权限的问题
   - 确保个人权限只能增强角色权限，不能减少
   - 修复了权限显示中的None值问题

2. 权限保存逻辑优化
   - 修复了个人权限保存时错误创建冗余记录的问题
   - 确保只保存真正需要的个人权限增强设置
   - 避免角色权限已为True的权限被个人权限设为False

3. 用户角色变更处理
   - 角色变更时自动清理旧的个人权限设置
   - 避免权限冲突和混乱

修复涉及的核心文件：
- app/views/user.py: 权限管理视图逻辑
- app/models/user.py: 用户权限检查方法
- app/__init__.py: 模板上下文权限函数

Revision ID: 5055ec5e2171
Revises: 669777b71041
Create Date: 2025-06-02 19:27:06.093348

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5055ec5e2171'
down_revision = '669777b71041'
branch_labels = None
depends_on = None


def upgrade():
    """
    应用权限系统修复
    
    注意：此迁移主要包含代码逻辑修复，无需数据库结构变更。
    权限系统的修复主要体现在应用层逻辑的改进。
    
    如需清理错误的个人权限数据，可以运行以下SQL：
    -- 清理与角色权限冲突的个人权限记录
    -- DELETE FROM permissions WHERE user_id IN (
    --     SELECT p.user_id FROM permissions p
    --     JOIN users u ON p.user_id = u.id
    --     JOIN role_permissions rp ON u.role = rp.role AND p.module = rp.module
    --     WHERE p.can_view = false AND rp.can_view = true
    --        OR p.can_create = false AND rp.can_create = true
    --        OR p.can_edit = false AND rp.can_edit = true
    --        OR p.can_delete = false AND rp.can_delete = true
    -- );
    """
    pass


def downgrade():
    """
    回退权限系统修复
    
    注意：权限系统修复主要是代码逻辑层面的改进，
    无法通过数据库迁移完全回退。
    如需回退，请使用相应的代码版本。
    """
    pass