#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import create_app, db
from app.models.dictionary import Dictionary
from app.utils.dictionary_init import init_dictionary

def create_dict_table():
    app = create_app()
    with app.app_context():
        # 创建字典表
        db.create_all()
        print('已创建字典表')
        
        # 初始化字典数据
        success = init_dictionary()
        if success:
            print('已初始化字典数据')
        else:
            print('字典数据初始化失败')

if __name__ == '__main__':
    create_dict_table() 