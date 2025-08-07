#!/usr/bin/env python3
"""
调试项目拥有者选择逻辑
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.user import User, Affiliation
from app.models.project import Project
from sqlalchemy import or_

app = create_app()

with app.app_context():
    # 获取yangjj用户
    yangjj = User.query.filter_by(username='yangjj').first()
    if not yangjj:
        print("找不到yangjj用户")
        exit(1)
    
    print(f"当前用户: {yangjj.username} ({yangjj.real_name}) - {yangjj.company_name}")
    print(f"用户ID: {yangjj.id}")
    print()
    
    # 获取一个yangjj拥有的项目进行测试
    project = Project.query.filter_by(owner_id=yangjj.id).first()
    if not project:
        print("yangjj没有拥有的项目，创建测试项目")
        # 这里可以创建测试项目，或者选择任意项目
        project = Project.query.first()
    
    print(f"测试项目: {project.project_name if project else 'None'}")
    print(f"项目拥有者ID: {project.owner_id if project else 'None'}")
    print()
    
    # 模拟项目拥有者选择逻辑
    current_user = yangjj
    
    # 基础用户ID
    base_user_ids = {current_user.id}
    if project:
        base_user_ids.add(project.owner_id)
    
    print(f"基础用户ID: {base_user_ids}")
    
    # 3. 通过归属关系，用户可以将数据转移给的账户
    
    # 用户可以查看的数据的拥有者（双向关系）
    # - 用户作为viewer，可以查看的数据的owner
    viewer_affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
    viewer_accessible_owner_ids = {a.owner_id for a in viewer_affiliations}
    
    print(f"作为viewer的归属关系:")
    for aff in viewer_affiliations:
        owner = User.query.get(aff.owner_id)
        print(f"  - 可查看 {owner.username} ({owner.real_name}) 的数据")
    print(f"Viewer accessible owner IDs: {viewer_accessible_owner_ids}")
    
    # - 用户作为owner，将数据归属给的viewer（可以将数据转移给这些用户）
    owner_affiliations = Affiliation.query.filter_by(owner_id=current_user.id).all()
    owner_accessible_viewer_ids = {a.viewer_id for a in owner_affiliations}
    
    print(f"\n作为owner的归属关系:")
    for aff in owner_affiliations:
        viewer = User.query.get(aff.viewer_id)
        print(f"  - 将数据归属给 {viewer.username} ({viewer.real_name})")
    print(f"Owner accessible viewer IDs: {owner_accessible_viewer_ids}")
    
    # 合并所有可访问的用户ID
    all_accessible_user_ids = base_user_ids.union(viewer_accessible_owner_ids).union(owner_accessible_viewer_ids)
    
    print(f"\n所有可访问用户ID: {all_accessible_user_ids}")
    
    # 查询这些用户，确保只包含活跃用户
    all_users = User.query.filter(
        User.id.in_(all_accessible_user_ids),
        or_(User.role == 'admin', User._is_active == True)
    ).all()
    
    print(f"\n最终可选择的用户列表:")
    for user in all_users:
        print(f"  - {user.username} ({user.real_name}) - {user.company_name} [ID: {user.id}]")
    
    # 检查lidong是否在列表中
    lidong_in_list = any(user.username == 'lidong' for user in all_users)
    print(f"\nlidong是否在可选择列表中: {lidong_in_list}")
    
    # 检查lidong用户状态
    lidong = User.query.filter_by(username='lidong').first()
    if lidong:
        print(f"lidong用户状态:")
        print(f"  - ID: {lidong.id}")
        print(f"  - 角色: {lidong.role}")
        print(f"  - 活跃状态: {lidong._is_active}")
        print(f"  - 公司: {lidong.company_name}")
        
        # 检查是否满足查询条件
        role_condition = lidong.role == 'admin' or lidong._is_active == True
        id_condition = lidong.id in all_accessible_user_ids
        print(f"  - 角色/活跃状态符合: {role_condition}")
        print(f"  - ID在可访问列表中: {id_condition}")