#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加required_fields字段到approval_process_template表
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 从config.py加载配置
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
print("加载配置中...")
from config import Config
app.config.from_object(Config)
print(f"数据库URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

# 初始化数据库
db = SQLAlchemy(app)

def add_required_fields_column():
    """添加required_fields字段到approval_process_template表（如果不存在）"""
    try:
        print("正在连接到数据库...")
        with app.app_context():
            # 检查字段是否存在
            print("正在检查字段是否存在...")
            check_sql = text("""
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'approval_process_template' 
                AND column_name = 'required_fields'
            """)
            
            result = db.session.execute(check_sql).fetchone()
            
            if not result:
                # 字段不存在，添加它
                print("required_fields字段不存在，正在添加...")
                add_sql = text("""
                    ALTER TABLE approval_process_template 
                    ADD COLUMN IF NOT EXISTS required_fields JSONB DEFAULT '[]'
                """)
                db.session.execute(add_sql)
                db.session.commit()
                print("✅ required_fields字段已成功添加！")
            else:
                print("✅ required_fields字段已存在，无需添加")
                
            return True
    except Exception as e:
        print(f"❌ 添加字段时出错: {e}")
        return False

if __name__ == "__main__":
    print("开始执行数据库迁移脚本...")
    success = add_required_fields_column()
    
    if success:
        print("迁移脚本执行完成！")
        sys.exit(0)
    else:
        print("迁移脚本执行失败！")
        sys.exit(1) 