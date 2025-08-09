#!/usr/bin/env python3
"""
验证客户关联权限控制功能迁移是否成功
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_database_structure():
    """验证数据库结构"""
    print("=== 数据库结构验证 ===\n")
    
    try:
        import psycopg2
        
        # 连接数据库
        conn = psycopg2.connect("postgresql://nijie@localhost:5432/pma_local")
        cursor = conn.cursor()
        
        # 检查created_by字段
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'project_customer_associations' 
            AND column_name = 'created_by'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ created_by字段已存在: {result[0]} ({result[1]}, nullable: {result[2]})")
        else:
            print("❌ created_by字段不存在")
            return False
        
        # 检查外键约束
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(oid) as constraint_definition 
            FROM pg_constraint 
            WHERE conname = 'project_customer_associations_created_by_fkey'
        """)
        
        constraint = cursor.fetchone()
        if constraint:
            print(f"✅ 外键约束已建立: {constraint[0]}")
            print(f"   约束定义: {constraint[1]}")
        else:
            print("❌ 外键约束不存在")
        
        # 检查现有数据
        cursor.execute("""
            SELECT COUNT(*) as total, 
                   COUNT(created_by) as with_creator,
                   COUNT(CASE WHEN created_by IS NULL THEN 1 END) as without_creator
            FROM project_customer_associations
        """)
        
        data_stats = cursor.fetchone()
        print(f"\n📊 现有数据统计:")
        print(f"   总关联数: {data_stats[0]}")
        print(f"   有创建者: {data_stats[1]}")
        print(f"   无创建者(历史数据): {data_stats[2]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False

def verify_model_compatibility():
    """验证模型兼容性"""
    print("\n=== 模型兼容性验证 ===\n")
    
    try:
        # 测试模型导入
        from app.models.project_customer_association import ProjectCustomerAssociation
        print("✅ ProjectCustomerAssociation模型导入成功")
        
        # 检查模型属性
        if hasattr(ProjectCustomerAssociation, 'created_by'):
            print("✅ 模型包含created_by属性")
        else:
            print("⚠️  模型不包含created_by属性（需要重启应用）")
        
        if hasattr(ProjectCustomerAssociation, 'creator'):
            print("✅ 模型包含creator关联")
        else:
            print("⚠️  模型不包含creator关联（需要重启应用）")
        
        # 测试add_association方法
        method = getattr(ProjectCustomerAssociation, 'add_association', None)
        if method and callable(method):
            print("✅ add_association方法可用")
            
            # 检查方法签名
            import inspect
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            if 'created_by' in params:
                print("✅ add_association方法支持created_by参数")
            else:
                print("❌ add_association方法不支持created_by参数")
        else:
            print("❌ add_association方法不可用")
        
        return True
        
    except Exception as e:
        print(f"❌ 模型验证失败: {e}")
        return False

def verify_api_endpoints():
    """验证API端点功能"""
    print("\n=== API功能验证 ===\n")
    
    print("📋 需要手动测试的API端点:")
    print("1. GET /project/api/customer_associations/<project_id>")
    print("   - 验证返回数据包含created_by和created_by_name字段")
    print("   - 验证can_remove权限字段正确")
    
    print("\n2. POST /project/api/add_customer_association")
    print("   - 验证新关联会记录created_by字段")
    print("   - 验证异常处理机制")
    
    print("\n3. POST /project/api/remove_customer_association/<id>")
    print("   - 验证权限检查逻辑")
    print("   - 验证只能移除自己创建的关联")
    
    return True

def main():
    """主验证函数"""
    print("🔍 客户关联权限控制功能迁移验证")
    print("=" * 50)
    
    success = True
    
    # 验证数据库结构
    if not verify_database_structure():
        success = False
    
    # 验证模型兼容性
    if not verify_model_compatibility():
        success = False
    
    # 验证API功能
    verify_api_endpoints()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 迁移验证成功！")
        print("\n📋 后续步骤:")
        print("1. 重启Flask应用程序")
        print("2. 访问项目详情页面测试功能")
        print("3. 验证添加/移除客户关联权限")
        print("4. 检查前端界面显示")
    else:
        print("❌ 迁移验证失败，需要检查问题")
    
    return success

if __name__ == '__main__':
    main()