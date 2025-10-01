#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查Affiliation和DataAffiliation表的数据一致性
"""
from app import create_app
from app.models.user import Affiliation, DataAffiliation

def check_affiliation_consistency():
    """检查Affiliation和DataAffiliation表的数据一致性"""
    print("开始检查Affiliation和DataAffiliation表的数据一致性...")
    
    # 获取所有DataAffiliation记录
    data_affiliations = DataAffiliation.query.all()
    data_aff_pairs = set([(da.owner_id, da.viewer_id) for da in data_affiliations])
    
    # 获取所有Affiliation记录
    affiliations = Affiliation.query.all()
    aff_pairs = set([(a.owner_id, a.viewer_id) for a in affiliations])
    
    # 检查不一致
    in_data_not_in_aff = data_aff_pairs - aff_pairs
    in_aff_not_in_data = aff_pairs - data_aff_pairs
    
    print(f"DataAffiliation记录数: {len(data_affiliations)}")
    print(f"Affiliation记录数: {len(affiliations)}")
    print(f"在DataAffiliation中但不在Affiliation中的记录: {len(in_data_not_in_aff)}")
    if in_data_not_in_aff:
        print("详细记录:")
        for owner_id, viewer_id in in_data_not_in_aff:
            print(f"  所有者ID: {owner_id}, 查看者ID: {viewer_id}")
    
    print(f"在Affiliation中但不在DataAffiliation中的记录: {len(in_aff_not_in_data)}")
    if in_aff_not_in_data:
        print("详细记录:")
        for owner_id, viewer_id in in_aff_not_in_data:
            print(f"  所有者ID: {owner_id}, 查看者ID: {viewer_id}")
    
    return in_data_not_in_aff, in_aff_not_in_data

def fix_affiliation_inconsistency():
    """修复Affiliation和DataAffiliation表的数据不一致"""
    print("开始修复Affiliation和DataAffiliation表的数据不一致...")
    
    from app import db
    in_data_not_in_aff, in_aff_not_in_data = check_affiliation_consistency()
    
    # 将DataAffiliation中有但Affiliation中没有的数据添加到Affiliation
    for owner_id, viewer_id in in_data_not_in_aff:
        print(f"添加到Affiliation: 所有者ID={owner_id}, 查看者ID={viewer_id}")
        db.session.add(Affiliation(owner_id=owner_id, viewer_id=viewer_id))
    
    # 将Affiliation中有但DataAffiliation中没有的数据添加到DataAffiliation
    for owner_id, viewer_id in in_aff_not_in_data:
        print(f"添加到DataAffiliation: 所有者ID={owner_id}, 查看者ID={viewer_id}")
        db.session.add(DataAffiliation(owner_id=owner_id, viewer_id=viewer_id))
    
    if in_data_not_in_aff or in_aff_not_in_data:
        db.session.commit()
        print("数据不一致已修复")
    else:
        print("数据已经一致，无需修复")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # 先检查一致性
        check_affiliation_consistency()
        
        # 询问是否需要修复
        fix_choice = input("\n是否需要修复数据不一致? (y/n): ")
        if fix_choice.lower() == 'y':
            fix_affiliation_inconsistency() 