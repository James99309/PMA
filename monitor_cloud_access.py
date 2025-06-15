#!/usr/bin/env python3

import os
import sys
import time
import psutil
import re

def monitor_cloud_access():
    """监控是否有进程尝试访问云端数据库"""
    print("🔍 启动云端访问监控...")
    
    cloud_patterns = [
        r'render\.com',
        r'dpg-.*\.singapore-postgres\.render\.com',
        r'pma_db_sp8d_user',
        r'LXNGJmR6bFrNecoaWbdbdzPpltIAd40w'
    ]
    
    while True:
        try:
            # 检查网络连接
            for conn in psutil.net_connections():
                if conn.raddr:
                    remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}"
                    for pattern in cloud_patterns:
                        if re.search(pattern, remote_addr):
                            print(f"🚨 检测到云端数据库连接尝试: {remote_addr}")
                            print(f"🔒 连接已被监控系统记录")
            
            time.sleep(5)  # 每5秒检查一次
            
        except KeyboardInterrupt:
            print("\n🔒 云端访问监控已停止")
            break
        except Exception as e:
            print(f"监控错误: {e}")
            time.sleep(10)

if __name__ == '__main__':
    monitor_cloud_access()
