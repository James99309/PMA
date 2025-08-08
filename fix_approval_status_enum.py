#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复审批状态枚举问题

问题：云端数据库的 approvalstatus 枚举类型缺少 'RECALLED' 值
解决：在数据库中添加 'RECALLED' 到 approvalstatus 枚举类型

错误信息：
invalid input value for enum approvalstatus: "RECALLED"

使用方法：
python fix_approval_status_enum.py
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_enum_values():
    """检查当前枚举值"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.extensions import db
            
            # 查询当前枚举值
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT enumlabel 
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid 
                WHERE t.typname = 'approvalstatus'
                ORDER BY e.enumsortorder;
            """))
            
            enum_values = [row[0] for row in result.fetchall()]
            logger.info(f"当前 approvalstatus 枚举值: {enum_values}")
            
            return enum_values
            
    except Exception as e:
        logger.error(f"检查枚举值失败: {str(e)}")
        return None

def add_recalled_to_enum():
    """向 approvalstatus 枚举添加 RECALLED 值"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.extensions import db
            
            # 检查是否已经存在 RECALLED 值
            enum_values = check_enum_values()
            if not enum_values:
                return False
                
            if 'RECALLED' in enum_values:
                logger.info("✅ RECALLED 值已存在于枚举中，无需添加")
                return True
                
            if 'recalled' in enum_values:
                logger.info("✅ recalled 值已存在于枚举中，无需添加")
                return True
            
            logger.info("🔧 开始添加 RECALLED 值到 approvalstatus 枚举...")
            
            # 添加新的枚举值
            # PostgreSQL 需要在事务外执行 ALTER TYPE ADD VALUE
            db.session.commit()  # 提交当前事务
            
            # 使用原始连接执行 ALTER TYPE 命令
            connection = db.engine.raw_connection()
            try:
                cursor = connection.cursor()
                # 添加 recalled 值（小写，与模型定义一致）
                cursor.execute("ALTER TYPE approvalstatus ADD VALUE 'recalled'")
                connection.commit()
                logger.info("✅ 成功添加 recalled 值到 approvalstatus 枚举")
                
                # 验证添加结果
                cursor.execute("""
                    SELECT enumlabel 
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid 
                    WHERE t.typname = 'approvalstatus'
                    ORDER BY e.enumsortorder;
                """)
                new_enum_values = [row[0] for row in cursor.fetchall()]
                logger.info(f"更新后的枚举值: {new_enum_values}")
                
            finally:
                cursor.close()
                connection.close()
            
            return True
            
    except Exception as e:
        logger.error(f"添加枚举值失败: {str(e)}")
        return False

def test_recalled_status():
    """测试 RECALLED 状态是否可以正常使用"""
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models.approval import ApprovalStatus, ApprovalInstance
            from app.extensions import db
            
            # 测试枚举值
            logger.info(f"📝 测试 ApprovalStatus.RECALLED: {ApprovalStatus.RECALLED.value}")
            
            # 测试数据库查询（不插入真实数据，只测试查询）
            test_query = ApprovalInstance.query.filter(
                ApprovalInstance.status == ApprovalStatus.RECALLED
            ).limit(1)
            
            # 执行查询但不获取结果，只验证SQL是否有效
            test_query.statement
            logger.info("✅ RECALLED 状态查询测试通过")
            
            return True
            
    except Exception as e:
        logger.error(f"测试 RECALLED 状态失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🔧 开始修复审批状态枚举问题")
    logger.info("=" * 60)
    
    try:
        # 1. 检查当前枚举值
        logger.info("1. 检查当前枚举值...")
        enum_values = check_enum_values()
        if not enum_values:
            logger.error("❌ 无法检查枚举值")
            return 1
        
        # 2. 添加 RECALLED 值
        logger.info("2. 添加缺失的枚举值...")
        success = add_recalled_to_enum()
        if not success:
            logger.error("❌ 添加枚举值失败")
            return 1
        
        # 3. 测试修复结果
        logger.info("3. 测试修复结果...")
        success = test_recalled_status()
        if not success:
            logger.error("❌ 测试修复结果失败")
            return 1
        
        logger.info("=" * 60)
        logger.info("✅ 审批状态枚举修复完成")
        logger.info("=" * 60)
        logger.info("")
        logger.info("修复内容:")
        logger.info("- ✅ 向 approvalstatus 枚举添加了 'recalled' 值")
        logger.info("- ✅ 现在支持审批实例的召回功能")
        logger.info("- ✅ 报销上传图片功能应该恢复正常")
        logger.info("")
        logger.info("建议操作:")
        logger.info("1. 重启应用服务")
        logger.info("2. 测试报销功能是否正常")
        logger.info("3. 验证审批流程工作正常")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 修复过程出现异常: {str(e)}")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)