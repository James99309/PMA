#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMA系统智能启动脚本
自动检测可用端口，解决端口冲突问题
"""

import os
import sys
import socket
import subprocess
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_port_available(port):
    """检查端口是否可用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result != 0  # 如果连接失败，说明端口可用
    except Exception:
        return False

def find_available_port(start_port=10000, max_attempts=10):
    """查找可用端口"""
    for i in range(max_attempts):
        port = start_port + i
        if check_port_available(port):
            return port
    return None

def kill_existing_processes():
    """终止现有的PMA进程"""
    try:
        # 查找并终止现有的Python进程
        result = subprocess.run(['pgrep', '-f', 'run.py'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    logger.info(f"终止现有进程: PID {pid}")
                    subprocess.run(['kill', pid])
                    time.sleep(1)
        
        # 检查端口10000是否仍被占用
        result = subprocess.run(['lsof', '-ti:10000'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    logger.info(f"强制终止占用端口10000的进程: PID {pid}")
                    subprocess.run(['kill', '-9', pid])
                    time.sleep(1)
                    
    except Exception as e:
        logger.warning(f"清理进程时出现警告: {str(e)}")

def start_pma_application(port):
    """启动PMA应用"""
    try:
        logger.info(f"正在启动PMA系统，端口: {port}")
        
        # 设置环境变量
        env = os.environ.copy()
        env['PORT'] = str(port)
        env['FLASK_ENV'] = 'production'
        
        # 启动应用
        process = subprocess.Popen(
            [sys.executable, 'run.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 等待应用启动
        logger.info("等待应用启动...")
        time.sleep(5)
        
        # 检查应用是否成功启动
        if check_port_available(port):
            logger.error(f"应用启动失败，端口 {port} 未被监听")
            if process.poll() is None:
                process.terminate()
            return False
        
        logger.info(f"✅ PMA系统启动成功!")
        logger.info(f"🌐 访问地址: http://localhost:{port}")
        logger.info(f"📊 备份管理: http://localhost:{port}/backup")
        logger.info(f"🔧 进程ID: {process.pid}")
        
        # 实时显示应用日志
        try:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭应用...")
            process.terminate()
            process.wait()
            logger.info("应用已关闭")
        
        return True
        
    except Exception as e:
        logger.error(f"启动应用时发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("🚀 PMA系统智能启动器")
    logger.info("=" * 50)
    
    # 1. 清理现有进程
    logger.info("🧹 清理现有进程...")
    kill_existing_processes()
    
    # 2. 查找可用端口
    logger.info("🔍 查找可用端口...")
    port = find_available_port()
    
    if not port:
        logger.error("❌ 无法找到可用端口 (10000-10009)")
        sys.exit(1)
    
    logger.info(f"✅ 找到可用端口: {port}")
    
    # 3. 启动应用
    success = start_pma_application(port)
    
    if not success:
        logger.error("❌ 应用启动失败")
        sys.exit(1)

if __name__ == "__main__":
    main() 