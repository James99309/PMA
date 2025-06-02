#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建项目评分系统相关表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_project_scoring_tables():
    """创建项目评分系统相关表"""
    app = create_app()
    
    with app.app_context():
        print("创建项目评分系统相关表...")
        
        # 1. 评分配置表
        create_scoring_config_sql = """
        CREATE TABLE IF NOT EXISTS project_scoring_config (
            id SERIAL PRIMARY KEY,
            category VARCHAR(50) NOT NULL,  -- 'information', 'quotation', 'stage', 'manual'
            field_name VARCHAR(100) NOT NULL,
            field_label VARCHAR(200) NOT NULL,
            score_value DECIMAL(3,2) NOT NULL DEFAULT 0.0,
            prerequisite TEXT,  -- 前置条件描述
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, field_name)
        );
        """
        
        # 2. 项目评分记录表（替换原有的project_rating_records）
        create_scoring_records_sql = """
        CREATE TABLE IF NOT EXISTS project_scoring_records (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            category VARCHAR(50) NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            score_value DECIMAL(3,2) NOT NULL DEFAULT 0.0,
            awarded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- 评分者（手动评分时）
            auto_calculated BOOLEAN DEFAULT TRUE,  -- 是否自动计算
            notes TEXT,  -- 备注
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, category, field_name)
        );
        """
        
        # 3. 项目总评分表
        create_project_scores_sql = """
        CREATE TABLE IF NOT EXISTS project_total_scores (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
            information_score DECIMAL(3,2) DEFAULT 0.0,
            quotation_score DECIMAL(3,2) DEFAULT 0.0,
            stage_score DECIMAL(3,2) DEFAULT 0.0,
            manual_score DECIMAL(3,2) DEFAULT 0.0,
            total_score DECIMAL(3,2) DEFAULT 0.0,
            star_rating INTEGER DEFAULT 0,  -- 星级（0-5）
            last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 4. 创建索引
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_scoring_records_project ON project_scoring_records(project_id);
        CREATE INDEX IF NOT EXISTS idx_scoring_records_category ON project_scoring_records(category);
        CREATE INDEX IF NOT EXISTS idx_scoring_config_category ON project_scoring_config(category);
        """
        
        try:
            # 执行SQL
            db.session.execute(text(create_scoring_config_sql))
            db.session.execute(text(create_scoring_records_sql))
            db.session.execute(text(create_project_scores_sql))
            db.session.execute(text(create_indexes_sql))
            
            # 插入默认配置
            insert_default_config_sql = """
            INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite) VALUES
            -- 信息完整性得分项
            ('information', 'project_stage', '项目阶段', 0.1, '无'),
            ('information', 'project_category', '项目分类', 0.1, '无'),
            ('information', 'design_consultant', '设计顾问', 0.1, '需获得授权编号'),
            ('information', 'user_info', '用户信息', 0.1, '无'),
            ('information', 'general_contractor', '总承包', 0.1, '无'),
            ('information', 'system_integrator', '集成商', 0.1, '无'),
            
            -- 报价完整性得分项
            ('quotation', 'approved_quotation', '审核通过的报价单', 0.5, '必须经由解决方案经理审批流程通过'),
            
            -- 阶段得分项（只取最高值）
            ('stage', 'tender', '招投标', 0.5, '无'),
            ('stage', 'awarded', '中标', 1.0, '无'),
            ('stage', 'final_pricing', '批价', 1.5, '无'),
            
            -- 手动奖励
            ('manual', 'supervisor_award', '上级奖励', 0.5, '手动评分')
            ON CONFLICT (category, field_name) DO NOTHING;
            """
            
            db.session.execute(text(insert_default_config_sql))
            db.session.commit()
            
            print("✅ 项目评分系统表创建成功")
            print("✅ 默认配置数据插入成功")
            
        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_project_scoring_tables() 
# -*- coding: utf-8 -*-
"""
创建项目评分系统相关表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_project_scoring_tables():
    """创建项目评分系统相关表"""
    app = create_app()
    
    with app.app_context():
        print("创建项目评分系统相关表...")
        
        # 1. 评分配置表
        create_scoring_config_sql = """
        CREATE TABLE IF NOT EXISTS project_scoring_config (
            id SERIAL PRIMARY KEY,
            category VARCHAR(50) NOT NULL,  -- 'information', 'quotation', 'stage', 'manual'
            field_name VARCHAR(100) NOT NULL,
            field_label VARCHAR(200) NOT NULL,
            score_value DECIMAL(3,2) NOT NULL DEFAULT 0.0,
            prerequisite TEXT,  -- 前置条件描述
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, field_name)
        );
        """
        
        # 2. 项目评分记录表（替换原有的project_rating_records）
        create_scoring_records_sql = """
        CREATE TABLE IF NOT EXISTS project_scoring_records (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            category VARCHAR(50) NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            score_value DECIMAL(3,2) NOT NULL DEFAULT 0.0,
            awarded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- 评分者（手动评分时）
            auto_calculated BOOLEAN DEFAULT TRUE,  -- 是否自动计算
            notes TEXT,  -- 备注
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, category, field_name)
        );
        """
        
        # 3. 项目总评分表
        create_project_scores_sql = """
        CREATE TABLE IF NOT EXISTS project_total_scores (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
            information_score DECIMAL(3,2) DEFAULT 0.0,
            quotation_score DECIMAL(3,2) DEFAULT 0.0,
            stage_score DECIMAL(3,2) DEFAULT 0.0,
            manual_score DECIMAL(3,2) DEFAULT 0.0,
            total_score DECIMAL(3,2) DEFAULT 0.0,
            star_rating INTEGER DEFAULT 0,  -- 星级（0-5）
            last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 4. 创建索引
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_scoring_records_project ON project_scoring_records(project_id);
        CREATE INDEX IF NOT EXISTS idx_scoring_records_category ON project_scoring_records(category);
        CREATE INDEX IF NOT EXISTS idx_scoring_config_category ON project_scoring_config(category);
        """
        
        try:
            # 执行SQL
            db.session.execute(text(create_scoring_config_sql))
            db.session.execute(text(create_scoring_records_sql))
            db.session.execute(text(create_project_scores_sql))
            db.session.execute(text(create_indexes_sql))
            
            # 插入默认配置
            insert_default_config_sql = """
            INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite) VALUES
            -- 信息完整性得分项
            ('information', 'project_stage', '项目阶段', 0.1, '无'),
            ('information', 'project_category', '项目分类', 0.1, '无'),
            ('information', 'design_consultant', '设计顾问', 0.1, '需获得授权编号'),
            ('information', 'user_info', '用户信息', 0.1, '无'),
            ('information', 'general_contractor', '总承包', 0.1, '无'),
            ('information', 'system_integrator', '集成商', 0.1, '无'),
            
            -- 报价完整性得分项
            ('quotation', 'approved_quotation', '审核通过的报价单', 0.5, '必须经由解决方案经理审批流程通过'),
            
            -- 阶段得分项（只取最高值）
            ('stage', 'tender', '招投标', 0.5, '无'),
            ('stage', 'awarded', '中标', 1.0, '无'),
            ('stage', 'final_pricing', '批价', 1.5, '无'),
            
            -- 手动奖励
            ('manual', 'supervisor_award', '上级奖励', 0.5, '手动评分')
            ON CONFLICT (category, field_name) DO NOTHING;
            """
            
            db.session.execute(text(insert_default_config_sql))
            db.session.commit()
            
            print("✅ 项目评分系统表创建成功")
            print("✅ 默认配置数据插入成功")
            
        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_project_scoring_tables() 
# -*- coding: utf-8 -*-
"""
创建项目评分系统相关表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_project_scoring_tables():
    """创建项目评分系统相关表"""
    app = create_app()
    
    with app.app_context():
        print("创建项目评分系统相关表...")
        
        # 1. 评分配置表
        create_scoring_config_sql = """
        CREATE TABLE IF NOT EXISTS project_scoring_config (
            id SERIAL PRIMARY KEY,
            category VARCHAR(50) NOT NULL,  -- 'information', 'quotation', 'stage', 'manual'
            field_name VARCHAR(100) NOT NULL,
            field_label VARCHAR(200) NOT NULL,
            score_value DECIMAL(3,2) NOT NULL DEFAULT 0.0,
            prerequisite TEXT,  -- 前置条件描述
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, field_name)
        );
        """
        
        # 2. 项目评分记录表（替换原有的project_rating_records）
        create_scoring_records_sql = """
        CREATE TABLE IF NOT EXISTS project_scoring_records (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            category VARCHAR(50) NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            score_value DECIMAL(3,2) NOT NULL DEFAULT 0.0,
            awarded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- 评分者（手动评分时）
            auto_calculated BOOLEAN DEFAULT TRUE,  -- 是否自动计算
            notes TEXT,  -- 备注
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, category, field_name)
        );
        """
        
        # 3. 项目总评分表
        create_project_scores_sql = """
        CREATE TABLE IF NOT EXISTS project_total_scores (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
            information_score DECIMAL(3,2) DEFAULT 0.0,
            quotation_score DECIMAL(3,2) DEFAULT 0.0,
            stage_score DECIMAL(3,2) DEFAULT 0.0,
            manual_score DECIMAL(3,2) DEFAULT 0.0,
            total_score DECIMAL(3,2) DEFAULT 0.0,
            star_rating INTEGER DEFAULT 0,  -- 星级（0-5）
            last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 4. 创建索引
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_scoring_records_project ON project_scoring_records(project_id);
        CREATE INDEX IF NOT EXISTS idx_scoring_records_category ON project_scoring_records(category);
        CREATE INDEX IF NOT EXISTS idx_scoring_config_category ON project_scoring_config(category);
        """
        
        try:
            # 执行SQL
            db.session.execute(text(create_scoring_config_sql))
            db.session.execute(text(create_scoring_records_sql))
            db.session.execute(text(create_project_scores_sql))
            db.session.execute(text(create_indexes_sql))
            
            # 插入默认配置
            insert_default_config_sql = """
            INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite) VALUES
            -- 信息完整性得分项
            ('information', 'project_stage', '项目阶段', 0.1, '无'),
            ('information', 'project_category', '项目分类', 0.1, '无'),
            ('information', 'design_consultant', '设计顾问', 0.1, '需获得授权编号'),
            ('information', 'user_info', '用户信息', 0.1, '无'),
            ('information', 'general_contractor', '总承包', 0.1, '无'),
            ('information', 'system_integrator', '集成商', 0.1, '无'),
            
            -- 报价完整性得分项
            ('quotation', 'approved_quotation', '审核通过的报价单', 0.5, '必须经由解决方案经理审批流程通过'),
            
            -- 阶段得分项（只取最高值）
            ('stage', 'tender', '招投标', 0.5, '无'),
            ('stage', 'awarded', '中标', 1.0, '无'),
            ('stage', 'final_pricing', '批价', 1.5, '无'),
            
            -- 手动奖励
            ('manual', 'supervisor_award', '上级奖励', 0.5, '手动评分')
            ON CONFLICT (category, field_name) DO NOTHING;
            """
            
            db.session.execute(text(insert_default_config_sql))
            db.session.commit()
            
            print("✅ 项目评分系统表创建成功")
            print("✅ 默认配置数据插入成功")
            
        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_project_scoring_tables() 
# -*- coding: utf-8 -*-
"""
创建项目评分系统相关表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_project_scoring_tables():
    """创建项目评分系统相关表"""
    app = create_app()
    
    with app.app_context():
        print("创建项目评分系统相关表...")
        
        # 1. 评分配置表
        create_scoring_config_sql = """
        CREATE TABLE IF NOT EXISTS project_scoring_config (
            id SERIAL PRIMARY KEY,
            category VARCHAR(50) NOT NULL,  -- 'information', 'quotation', 'stage', 'manual'
            field_name VARCHAR(100) NOT NULL,
            field_label VARCHAR(200) NOT NULL,
            score_value DECIMAL(3,2) NOT NULL DEFAULT 0.0,
            prerequisite TEXT,  -- 前置条件描述
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, field_name)
        );
        """
        
        # 2. 项目评分记录表（替换原有的project_rating_records）
        create_scoring_records_sql = """
        CREATE TABLE IF NOT EXISTS project_scoring_records (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            category VARCHAR(50) NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            score_value DECIMAL(3,2) NOT NULL DEFAULT 0.0,
            awarded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,  -- 评分者（手动评分时）
            auto_calculated BOOLEAN DEFAULT TRUE,  -- 是否自动计算
            notes TEXT,  -- 备注
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, category, field_name)
        );
        """
        
        # 3. 项目总评分表
        create_project_scores_sql = """
        CREATE TABLE IF NOT EXISTS project_total_scores (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
            information_score DECIMAL(3,2) DEFAULT 0.0,
            quotation_score DECIMAL(3,2) DEFAULT 0.0,
            stage_score DECIMAL(3,2) DEFAULT 0.0,
            manual_score DECIMAL(3,2) DEFAULT 0.0,
            total_score DECIMAL(3,2) DEFAULT 0.0,
            star_rating INTEGER DEFAULT 0,  -- 星级（0-5）
            last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # 4. 创建索引
        create_indexes_sql = """
        CREATE INDEX IF NOT EXISTS idx_scoring_records_project ON project_scoring_records(project_id);
        CREATE INDEX IF NOT EXISTS idx_scoring_records_category ON project_scoring_records(category);
        CREATE INDEX IF NOT EXISTS idx_scoring_config_category ON project_scoring_config(category);
        """
        
        try:
            # 执行SQL
            db.session.execute(text(create_scoring_config_sql))
            db.session.execute(text(create_scoring_records_sql))
            db.session.execute(text(create_project_scores_sql))
            db.session.execute(text(create_indexes_sql))
            
            # 插入默认配置
            insert_default_config_sql = """
            INSERT INTO project_scoring_config (category, field_name, field_label, score_value, prerequisite) VALUES
            -- 信息完整性得分项
            ('information', 'project_stage', '项目阶段', 0.1, '无'),
            ('information', 'project_category', '项目分类', 0.1, '无'),
            ('information', 'design_consultant', '设计顾问', 0.1, '需获得授权编号'),
            ('information', 'user_info', '用户信息', 0.1, '无'),
            ('information', 'general_contractor', '总承包', 0.1, '无'),
            ('information', 'system_integrator', '集成商', 0.1, '无'),
            
            -- 报价完整性得分项
            ('quotation', 'approved_quotation', '审核通过的报价单', 0.5, '必须经由解决方案经理审批流程通过'),
            
            -- 阶段得分项（只取最高值）
            ('stage', 'tender', '招投标', 0.5, '无'),
            ('stage', 'awarded', '中标', 1.0, '无'),
            ('stage', 'final_pricing', '批价', 1.5, '无'),
            
            -- 手动奖励
            ('manual', 'supervisor_award', '上级奖励', 0.5, '手动评分')
            ON CONFLICT (category, field_name) DO NOTHING;
            """
            
            db.session.execute(text(insert_default_config_sql))
            db.session.commit()
            
            print("✅ 项目评分系统表创建成功")
            print("✅ 默认配置数据插入成功")
            
        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_project_scoring_tables() 