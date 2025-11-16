#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接运行迁移脚本 - 不加载完整Flask应用"""
import sys
import os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)

# 从config获取数据库URL
from config import Config
from sqlalchemy import create_engine, text
from datetime import datetime

# 创建数据库引擎
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

print("🔄 开始创建规格字典表...")

with engine.connect() as conn:
    # 开始事务
    trans = conn.begin()

    try:
        # 创建表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS specification_dictionary (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                unit VARCHAR(20),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✅ specification_dictionary 表创建成功")

        # 创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_spec_dict_active
            ON specification_dictionary (is_active)
        """))

        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_spec_dict_name
            ON specification_dictionary (name)
        """))
        print("✅ 索引创建成功")

        # 检查是否已有数据
        result = conn.execute(text("SELECT COUNT(*) FROM specification_dictionary"))
        count = result.scalar()

        if count == 0:
            # 插入初始数据
            initial_specs = [
                ('频率范围', 'MHz'),
                ('输出功率', 'dBm'),
                ('工作温度', '℃'),
                ('接口类型', None),
                ('防护等级', None),
                ('工作电压', 'V'),
                ('尺寸', 'mm'),
                ('重量', 'kg'),
                ('增益', 'dB'),
                ('带宽', 'MHz'),
                ('噪声系数', 'dB'),
                ('功耗', 'W'),
                ('存储温度', '℃'),
                ('湿度范围', '%RH'),
                ('传输距离', 'm'),
            ]

            for name, unit in initial_specs:
                conn.execute(
                    text("INSERT INTO specification_dictionary (name, unit, is_active, created_at) VALUES (:name, :unit, TRUE, :created_at)"),
                    {"name": name, "unit": unit, "created_at": datetime.utcnow()}
                )

            print(f"✅ 已添加 {len(initial_specs)} 条初始规格数据")
        else:
            print(f"ℹ️  表中已有 {count} 条记录，跳过初始数据插入")

        # 更新 alembic_version 表
        # 检查迁移是否已记录
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.scalar()

        new_version = '20251109_spec_dict'

        if current_version != new_version:
            conn.execute(
                text("UPDATE alembic_version SET version_num = :version"),
                {"version": new_version}
            )
            print(f"✅ 更新迁移版本: {current_version} -> {new_version}")
        else:
            print(f"ℹ️  迁移版本已是最新: {new_version}")

        # 提交事务
        trans.commit()
        print("\n✅ 迁移完成！")

        # 验证结果
        result = conn.execute(text("SELECT name, unit FROM specification_dictionary LIMIT 5"))
        rows = result.fetchall()

        print("\n前5条规格记录：")
        for row in rows:
            unit_str = f" ({row[1]})" if row[1] else ""
            print(f"  - {row[0]}{unit_str}")

    except Exception as e:
        trans.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
