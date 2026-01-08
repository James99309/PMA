#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查OVS代码版本 - 在OVS服务器上运行此脚本
运行方法: python scripts/temp/check_ovs_code_version.py
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

print("="*60)
print("检查代码版本和配置")
print("="*60)

# 1. 检查 get_content_filter_options 函数是否存在
print("\n1. 检查 config_management.py 中的 get_content_filter_options 函数:")
try:
    from app.views.config_management import get_content_filter_options
    print("   ✓ 函数存在")

    # 尝试调用
    from app import create_app
    app = create_app()
    with app.app_context():
        result = get_content_filter_options()
        print(f"   ✓ 函数可调用")
        print(f"   - 返回的模块数: {len(result)}")

        # 检查 project 模块
        if 'project' in result:
            project_config = result['project']
            print(f"   - project 模块筛选项: {list(project_config.keys())}")

            for key, config in project_config.items():
                opts = config.get('options', [])
                print(f"     - {key}: {len(opts)} 个选项")
                if len(opts) == 0:
                    print(f"       ⚠️ 选项为空!")
                else:
                    print(f"       前3个: {opts[:3]}")
        else:
            print("   ⚠️ project 模块不在返回结果中!")

except ImportError as e:
    print(f"   ✗ 导入失败: {e}")
except Exception as e:
    print(f"   ✗ 错误: {e}")

# 2. 检查 dictionary_helpers.py 中的函数
print("\n2. 检查 dictionary_helpers.py 中的选项函数:")
try:
    from app.utils.dictionary_helpers import (
        get_project_type_options,
        get_project_stage_options,
        get_report_source_options
    )
    print("   ✓ 函数导入成功")

    from app import create_app
    app = create_app()
    with app.app_context():
        opts1 = get_project_type_options()
        opts2 = get_project_stage_options()
        opts3 = get_report_source_options()
        print(f"   - get_project_type_options: {len(opts1)} 个")
        print(f"   - get_project_stage_options: {len(opts2)} 个")
        print(f"   - get_report_source_options: {len(opts3)} 个")

except ImportError as e:
    print(f"   ✗ 导入失败: {e}")
except Exception as e:
    print(f"   ✗ 错误: {e}")

# 3. 检查数据库 dictionaries 表
print("\n3. 检查数据库 dictionaries 表:")
try:
    from app import create_app, db
    from app.models.dictionary import Dictionary

    app = create_app()
    with app.app_context():
        for dict_type in ['project_type', 'project_stage', 'report_source']:
            count = Dictionary.query.filter_by(type=dict_type, is_active=True).count()
            status = "✓" if count > 0 else "⚠️"
            print(f"   {status} {dict_type}: {count} 条记录")

except Exception as e:
    print(f"   ✗ 错误: {e}")

print("\n" + "="*60)
print("检查完成")
print("="*60)
