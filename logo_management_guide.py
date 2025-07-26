#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logo数据库管理指南和示例代码
如何在PMA系统中上传和管理Logo
"""

from app.services.logo_service import LogoService
from app.models.company_asset import CompanyAsset
from app import db

def upload_logo_from_file(file_path, user_id=None):
    """
    从文件上传Logo到数据库
    
    Args:
        file_path: Logo文件路径 (支持 .png, .jpg, .svg 等格式)
        user_id: 上传用户ID (可选)
    
    Example:
        upload_logo_from_file('/path/to/your/logo.png', user_id=1)
    """
    try:
        # 读取文件
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # 获取文件名
        import os
        filename = os.path.basename(file_path)
        
        # 上传到数据库
        logo = LogoService.upload_logo(
            file_data=file_data,
            filename=filename,
            asset_name=f"公司Logo - {filename}",
            asset_key='evertac_logo',  # 标准Logo键名
            created_by_id=user_id
        )
        
        print(f"✅ Logo上传成功: {logo.asset_name}")
        print(f"   文件大小: {logo.file_size_kb}KB")
        print(f"   文件类型: {logo.file_type}")
        print(f"   数据库ID: {logo.id}")
        
        return logo
        
    except Exception as e:
        print(f"❌ Logo上传失败: {e}")
        return None

def list_all_logos():
    """查看数据库中的所有Logo"""
    try:
        logos = LogoService.list_logos()
        
        if not logos:
            print("📭 数据库中暂无Logo")
            return
        
        print(f"📋 数据库中共有 {len(logos)} 个Logo:")
        print("-" * 80)
        
        for i, logo in enumerate(logos, 1):
            status = "🟢 默认" if logo['is_default'] else "⚪ 普通"
            print(f"{i}. {status} {logo['asset_name']}")
            print(f"   ID: {logo['id']}")
            print(f"   键名: {logo['asset_key']}")
            print(f"   文件: {logo['file_name']} ({logo['file_size_kb']}KB)")
            print(f"   类型: {logo['file_type']}")
            print(f"   创建时间: {logo['created_at']}")
            print()
        
        return logos
        
    except Exception as e:
        print(f"❌ 获取Logo列表失败: {e}")
        return []

def set_default_logo(logo_id):
    """设置默认Logo"""
    try:
        success = CompanyAsset.set_default_logo(logo_id)
        if success:
            db.session.commit()
            print(f"✅ 已将Logo ID {logo_id} 设为默认Logo")
        else:
            print(f"❌ 设置默认Logo失败：ID {logo_id} 不存在或不是Logo类型")
        
        return success
        
    except Exception as e:
        print(f"❌ 设置默认Logo失败: {e}")
        return False

def delete_logo(logo_id):
    """删除Logo"""
    try:
        success = LogoService.delete_logo(logo_id)
        if success:
            print(f"✅ Logo ID {logo_id} 已删除")
        else:
            print(f"❌ 删除Logo失败：ID {logo_id} 不存在")
        
        return success
        
    except Exception as e:
        print(f"❌ 删除Logo失败: {e}")
        return False

def check_current_logo():
    """检查当前使用的Logo"""
    try:
        logo_base64 = LogoService.get_company_logo('evertac_logo')
        
        if logo_base64:
            print("✅ 当前Logo状态：已设置")
            
            # 获取Logo信息
            logo = CompanyAsset.get_logo('evertac_logo') or CompanyAsset.get_default_logo()
            if logo:
                print(f"   Logo名称: {logo.asset_name}")
                print(f"   文件类型: {logo.file_type}")
                print(f"   文件大小: {logo.file_size_kb}KB")
                print(f"   是否默认: {'是' if logo.is_default else '否'}")
            
            # Data URL长度（用于验证）
            print(f"   Data URL长度: {len(logo_base64)} 字符")
            print(f"   Data URL前缀: {logo_base64[:50]}...")
        else:
            print("❌ 当前Logo状态：未设置")
            print("💡 建议：使用 upload_logo_from_file() 上传Logo")
        
        return logo_base64 is not None
        
    except Exception as e:
        print(f"❌ 检查Logo状态失败: {e}")
        return False

def init_default_logo():
    """初始化默认Logo"""
    try:
        logo = LogoService.init_default_logo()
        print(f"✅ 默认Logo已初始化: {logo.asset_name}")
        return logo
        
    except Exception as e:
        print(f"❌ 初始化默认Logo失败: {e}")
        return None

# 使用示例和说明
if __name__ == "__main__":
    print("=" * 60)
    print("📋 PMA系统 Logo数据库管理指南")
    print("=" * 60)
    
    print("\n🎯 Logo存储位置:")
    print("   数据库表: company_assets")
    print("   存储方式: Base64编码存储在 file_content 字段")
    print("   标准键名: 'evertac_logo'")
    
    print("\n📝 使用方法:")
    print("1. 上传Logo文件到数据库:")
    print("   upload_logo_from_file('/path/to/your/logo.png')")
    
    print("\n2. 查看当前Logo状态:")
    print("   check_current_logo()")
    
    print("\n3. 查看所有Logo:")
    print("   list_all_logos()")
    
    print("\n4. 设置默认Logo:")
    print("   set_default_logo(logo_id)")
    
    print("\n5. 删除Logo:")
    print("   delete_logo(logo_id)")
    
    print("\n6. 初始化默认Logo:")
    print("   init_default_logo()")
    
    print("\n💡 支持的文件格式:")
    print("   - PNG (.png)")
    print("   - JPEG (.jpg, .jpeg)")
    print("   - SVG (.svg)")
    print("   - GIF (.gif)")
    
    print("\n📏 建议的Logo规格:")
    print("   - 尺寸: 240x50像素 (或等比例)")
    print("   - 格式: PNG或SVG (推荐SVG)")
    print("   - 大小: < 100KB")
    print("   - 背景: 透明背景")
    
    print("\n🔧 实际操作示例:")
    print("-------------------")
    
    # 示例1: 检查当前Logo状态
    print("\n1. 检查当前Logo状态:")
    check_current_logo()
    
    # 示例2: 查看所有Logo
    print("\n2. 查看数据库中的所有Logo:")
    list_all_logos()
    
    print("\n✨ 完成！")
    print("现在你可以使用上述函数来管理Logo了。")