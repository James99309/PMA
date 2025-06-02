#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复剩余的数据库差异

该脚本用于修复本地和云端数据库之间的剩余差异：
1. 修正 projects.rating 字段类型 (INTEGER -> NUMERIC(2,1))
2. 创建缺失的 project_rating_records 表
3. 添加任何缺失的列
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text

def main():
    cloud_db_url = os.environ.get('RENDER_DATABASE_URL')
    
    if not cloud_db_url:
        print("❌ 未设置 RENDER_DATABASE_URL 环境变量")
        return
    
    print("🔧 开始修复剩余的数据库差异...")
    
    try:
        engine = create_engine(cloud_db_url)
        
        with engine.connect() as conn:
            print("\n1️⃣ 修正 projects.rating 字段类型...")
            
            # 检查当前类型
            result = conn.execute(text("""
                SELECT data_type, numeric_precision, numeric_scale 
                FROM information_schema.columns 
                WHERE table_name = 'projects' AND column_name = 'rating'
            """))
            current_type = result.fetchone()
            
            if current_type:
                print(f"   当前类型: {current_type[0]}")
                
                if current_type[0] == 'integer':
                    print("   修改字段类型为 NUMERIC(2,1)...")
                    conn.execute(text("ALTER TABLE projects ALTER COLUMN rating TYPE NUMERIC(2,1)"))
                    print("   ✅ rating字段类型修正完成")
                else:
                    print("   ✅ rating字段类型已正确")
            
            print("\n2️⃣ 检查并创建 project_rating_records 表...")
            
            # 检查表是否存在
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'project_rating_records'
                )
            """))
            
            table_exists = result.scalar()
            
            if not table_exists:
                print("   创建 project_rating_records 表...")
                
                create_table_sql = """
                CREATE TABLE project_rating_records (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    rating NUMERIC(2,1) NOT NULL,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_project_rating_project_id FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    CONSTRAINT fk_project_rating_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT uq_project_rating_project_user UNIQUE (project_id, user_id)
                );
                
                -- 创建索引
                CREATE INDEX idx_project_rating_records_project_id ON project_rating_records(project_id);
                CREATE INDEX idx_project_rating_records_user_id ON project_rating_records(user_id);
                CREATE INDEX idx_project_rating_records_created_at ON project_rating_records(created_at);
                
                -- 添加注释
                COMMENT ON TABLE project_rating_records IS '项目评分记录表';
                COMMENT ON COLUMN project_rating_records.project_id IS '项目ID';
                COMMENT ON COLUMN project_rating_records.user_id IS '评分用户ID';
                COMMENT ON COLUMN project_rating_records.rating IS '评分(1.0-5.0)';
                COMMENT ON COLUMN project_rating_records.comment IS '评分备注';
                COMMENT ON COLUMN project_rating_records.created_at IS '创建时间';
                COMMENT ON COLUMN project_rating_records.updated_at IS '更新时间';
                """
                
                conn.execute(text(create_table_sql))
                print("   ✅ project_rating_records 表创建完成")
            else:
                print("   ✅ project_rating_records 表已存在")
            
            print("\n3️⃣ 检查其他可能缺失的列...")
            
            # 检查 approval_process_template 表的新列
            missing_columns = []
            
            check_columns = [
                ('approval_process_template', 'lock_object_on_start', 'BOOLEAN DEFAULT true'),
                ('approval_process_template', 'lock_reason', "VARCHAR(200) DEFAULT '审批流程进行中，暂时锁定编辑'"),
                ('approval_step', 'editable_fields', "JSON DEFAULT '[]'"),
                ('approval_step', 'cc_users', "JSON DEFAULT '[]'"),
                ('approval_step', 'cc_enabled', 'BOOLEAN DEFAULT false'),
                ('approval_instance', 'template_snapshot', 'JSON'),
                ('approval_instance', 'template_version', 'VARCHAR(50)'),
                ('quotations', 'approval_status', "VARCHAR(50) DEFAULT 'pending'"),
                ('quotations', 'approved_stages', 'JSON'),
                ('quotations', 'approval_history', 'JSON'),
                ('quotations', 'approved_by', 'INTEGER'),
                ('quotations', 'approved_at', 'TIMESTAMP'),
                ('quotations', 'approval_comments', 'TEXT'),
                ('quotations', 'approval_required_fields', 'JSON'),
            ]
            
            for table_name, column_name, column_type in check_columns:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = '{table_name}' AND column_name = '{column_name}'
                    )
                """))
                
                column_exists = result.scalar()
                
                if not column_exists:
                    print(f"   添加列: {table_name}.{column_name}")
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                    missing_columns.append(f"{table_name}.{column_name}")
            
            if missing_columns:
                print(f"   ✅ 添加了 {len(missing_columns)} 个缺失的列")
            else:
                print("   ✅ 所有列都已存在")
            
            # 提交事务
            conn.commit()
            
            print("\n🎉 所有数据库差异修复完成！")
            
            # 最终验证
            print("\n📋 最终验证...")
            
            # 验证 rating 字段类型
            result = conn.execute(text("""
                SELECT data_type, numeric_precision, numeric_scale 
                FROM information_schema.columns 
                WHERE table_name = 'projects' AND column_name = 'rating'
            """))
            rating_type = result.fetchone()
            print(f"   projects.rating: {rating_type[0]}({rating_type[1]},{rating_type[2]})")
            
            # 验证表数量
            result = conn.execute(text("""
                SELECT count(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """))
            table_count = result.scalar()
            print(f"   表总数: {table_count}")
            
            print("\n✅ 数据库同步完全完成！")
            
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        return

if __name__ == "__main__":
    main() 