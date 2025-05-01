#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
产品分类标识符分配工具

此脚本用于为已存在但尚未分配标识符的产品分类自动分配唯一标识符。
"""

import os
import sys
import random
import string
from flask import Flask

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.product_code import ProductCategory

def assign_identifiers():
    """为未分配标识符的产品分类分配唯一标识符"""
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        # 查找所有分类
        all_categories = ProductCategory.query.all()
        print(f"找到 {len(all_categories)} 个产品分类")
        
        # 获取已使用的标识符
        used_identifiers = [cat.code_letter for cat in all_categories if cat.code_letter]
        print(f"已使用标识符: {', '.join(sorted(used_identifiers))}")
        
        # 可用字母池
        available_letters = [letter for letter in string.ascii_uppercase 
                           if letter not in used_identifiers]
        # 可用数字池
        available_digits = [str(digit) for digit in range(10) 
                          if str(digit) not in used_identifiers]
        
        # 合并可用标识符（优先字母，然后数字）
        available_identifiers = available_letters + available_digits
        
        print(f"可用字母: {', '.join(sorted(available_letters))}")
        print(f"可用数字: {', '.join(sorted(available_digits))}")
        print(f"总可用标识符: {len(available_identifiers)}")
        
        # 查找所有未分配标识符的分类
        empty_categories = ProductCategory.query.filter(
            (ProductCategory.code_letter == None) | 
            (ProductCategory.code_letter == '')
        ).all()
        
        if not empty_categories:
            print("没有找到未分配标识符的产品分类")
            return
        
        print(f"找到 {len(empty_categories)} 个未分配标识符的产品分类")
        
        if len(empty_categories) > len(available_identifiers):
            print(f"警告：需要分配 {len(empty_categories)} 个标识符，但只有 {len(available_identifiers)} 个可用标识符")
            print("部分分类可能无法分配到标识符")
        
        # 分配标识符
        assigned_count = 0
        for category in empty_categories:
            if not available_identifiers:
                print(f"无可用标识符，剩余 {len(empty_categories) - assigned_count} 个分类未分配")
                break
                
            # 优先使用字母
            if available_letters:
                identifier = random.choice(available_letters)
                available_letters.remove(identifier)
            else:
                # 字母用完后使用数字
                identifier = random.choice(available_digits)
                available_digits.remove(identifier)
                
            available_identifiers.remove(identifier)
            
            # 更新分类
            category.code_letter = identifier
            print(f"为分类 '{category.name}' 分配标识符 '{identifier}'")
            assigned_count += 1
        
        # 提交更改
        if assigned_count > 0:
            db.session.commit()
            print(f"成功为 {assigned_count} 个分类分配了标识符")
        else:
            print("未分配任何标识符")

if __name__ == "__main__":
    assign_identifiers() 