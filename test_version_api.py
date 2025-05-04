#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本API测试脚本

此脚本用于测试版本信息API功能
"""

import requests
import json
import sys

def test_version_api(base_url):
    """测试版本信息API"""
    url = f"{base_url}/api/version"
    
    try:
        print(f"正在请求版本信息: {url}")
        response = requests.get(url)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("API响应:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                if data.get('success'):
                    print("
版本信息获取成功!")
                    
                    # 检查一致性
                    consistency = data.get('data', {}).get('consistency', {})
                    if consistency:
                        print("
模块一致性状态:")
                        for module, status in consistency.items():
                            is_consistent = status.get('is_consistent', False)
                            status_str = "一致" if is_consistent else "不一致"
                            print(f"  {module}: {status_str}")
                            
                            if not is_consistent:
                                print(f"    不一致文件: {status.get('inconsistent_files', [])}")
                    
                    return True
                else:
                    print(f"版本信息获取失败: {data.get('message', '未知错误')}")
                    return False
            except json.JSONDecodeError:
                print("解析API响应失败，返回的不是有效的JSON")
                print(f"响应内容: {response.text}")
                return False
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"测试版本API时出错: {str(e)}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_version_api.py <base_url>")
        print("示例: python test_version_api.py http://localhost:5000")
        return 1
    
    base_url = sys.argv[1]
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url
    
    success = test_version_api(base_url)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
