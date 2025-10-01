#!/usr/bin/env python3

import os
import re

def security_check():
    """执行安全检查"""
    print("🔒 PMA本地环境安全检查")
    print("=" * 50)
    
    issues = []
    
    # 检查配置文件
    print("1. 检查配置文件...")
    if os.path.exists('config.py'):
        with open('config.py', 'r') as f:
            config_content = f.read()
            
        if 'CLOUD_DB_ACCESS_DISABLED = True' in config_content:
            print("✅ 云端数据库访问已禁用")
        else:
            issues.append("❌ 云端数据库访问未正确禁用")
            
        if 'render.com' in config_content:
            issues.append("⚠️ 配置文件中仍包含云端数据库URL")
    else:
        issues.append("❌ 配置文件不存在")
    
    # 检查环境变量
    print("2. 检查环境变量...")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
            
        if 'CLOUD_DB_ACCESS=disabled' in env_content:
            print("✅ 环境变量已禁用云端访问")
        else:
            issues.append("❌ 环境变量未正确配置")
    else:
        issues.append("❌ 环境变量文件不存在")
    
    # 检查运行进程
    print("3. 检查运行进程...")
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmdline = ' '.join(proc.info['cmdline'] or [])
            if 'render.com' in cmdline or 'dpg-' in cmdline:
                issues.append(f"⚠️ 发现可疑进程: {proc.info['name']} (PID: {proc.info['pid']})")
    except ImportError:
        print("⚠️ 无法检查进程（需要安装psutil）")
    
    # 输出结果
    print("\n🎯 安全检查结果:")
    if not issues:
        print("✅ 所有安全检查通过")
        print("🔒 本地环境已安全隔离")
        return True
    else:
        print("❌ 发现安全问题:")
        for issue in issues:
            print(f"  {issue}")
        return False

if __name__ == '__main__':
    security_check()
