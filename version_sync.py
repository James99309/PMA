#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本同步工具

一键同步版本管理系统与Git提交记录
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("🔄 PMA版本管理同步工具")
    print("=" * 50)
    
    try:
        from update_version_to_latest_git import update_current_version_to_git
        from test_version_integration import test_version_integration
        
        print("📋 步骤1: 同步版本与Git记录")
        success = update_current_version_to_git()
        
        if not success:
            print("❌ 版本同步失败")
            return False
        
        print("\n📋 步骤2: 验证版本管理功能")
        success = test_version_integration()
        
        if not success:
            print("❌ 版本验证失败")
            return False
        
        print("\n🎉 版本同步完成！")
        print("💡 现在您可以：")
        print("   1. 刷新版本管理页面查看最新信息")
        print("   2. 使用'自动升级'按钮基于新Git提交创建版本")
        print("   3. 使用'生成版本'按钮创建语义化版本号")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)