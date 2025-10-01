#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
角色同步脚本
用于确保角色字典数据和权限系统中的角色保持一致
"""

from app import create_app
from app.models.dictionary import Dictionary
from app.permissions import ROLE_PERMISSIONS
from sqlalchemy import func

app = create_app()

def sync_roles():
    """同步角色字典和权限系统角色"""
    with app.app_context():
        print('开始同步角色数据...')
        print('\n=== 当前角色字典数据 ===')
        dict_roles = Dictionary.query.filter_by(type='role').all()
        for role in dict_roles:
            print(f'{role.key} - {role.value} (active: {role.is_active})')
        
        print('\n=== 权限系统角色 ===')
        for role_key in ROLE_PERMISSIONS.keys():
            print(role_key)
        
        # 确保所有权限系统角色都存在于字典中
        perm_roles = set(ROLE_PERMISSIONS.keys())
        dict_role_keys = {r.key for r in dict_roles}
        
        # 找出需要添加的角色
        missing_roles = perm_roles - dict_role_keys
        
        if missing_roles:
            print(f'\n需要添加 {len(missing_roles)} 个角色到字典:')
            # 获取最大排序号
            max_order = Dictionary.query.filter_by(type='role').with_entities(func.max(Dictionary.sort_order)).scalar() or 0
            
            for i, role_key in enumerate(missing_roles):
                # 获取角色显示名称
                role_name = ROLE_NAME_MAPPINGS.get(role_key, role_key)
                
                # 添加新角色到字典
                new_role = Dictionary(
                    type='role',
                    key=role_key,  # 使用标准键名
                    value=role_name,  # 使用显示名称作为值
                    sort_order=max_order + (i + 1) * 10,
                    is_active=True
                )
                Dictionary.query.session.add(new_role)
                print(f'  - 添加: {role_key} -> {role_name}')
                
            # 提交更改
            Dictionary.query.session.commit()
            print('新角色已添加到字典')
            
        # 更新现有角色的状态和名称
        updated = False
        for dict_role in dict_roles:
            orig_key = dict_role.key
            norm_key = orig_key
            
            # 如果规范化后的键在权限系统中存在，确保角色是激活的
            if norm_key in perm_roles:
                if not dict_role.is_active:
                    dict_role.is_active = True
                    print(f'激活角色: {orig_key}')
                    updated = True
                
                # 更新显示名称为标准名称
                std_name = ROLE_NAME_MAPPINGS.get(norm_key, norm_key)
                if dict_role.value != std_name:
                    print(f'更新显示名称: {orig_key} 从 "{dict_role.value}" 到 "{std_name}"')
                    dict_role.value = std_name
                    updated = True
            # 否则，如果角色在权限系统中不存在，但在字典中存在，设为非活动
            elif dict_role.is_active:
                dict_role.is_active = False
                print(f'禁用角色: {orig_key} (在权限系统中不存在)')
                updated = True
        
        # 如果有更新，提交更改
        if updated:
            Dictionary.query.session.commit()
            print('角色字典数据已更新')
        else:
            print('所有角色都是最新的，无需更新')
        
        print('\n=== 同步后的角色字典数据 ===')
        dict_roles = Dictionary.query.filter_by(type='role').order_by(Dictionary.sort_order).all()
        for role in dict_roles:
            status = "启用" if role.is_active else "禁用"
            norm_key = role.key
            print(f'{role.key} ({norm_key}) - {role.value} [{status}]')
        
        print('\n角色同步完成')

if __name__ == '__main__':
    sync_roles() 