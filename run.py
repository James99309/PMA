import os
import sys
import socket
import logging
import signal
import subprocess
from app import create_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """终止占用指定端口的进程"""
    try:
        # 这在MacOS和Linux上有效
        cmd = f"lsof -ti:{port} | xargs kill -9"
        subprocess.run(cmd, shell=True)
        logger.info(f"已终止占用端口 {port} 的进程")
        return True
    except Exception as e:
        logger.error(f"终止进程时出错: {e}")
        return False

def main():
    PORT = 8082
    
    # 检查是否是重载器进程
    is_reloader = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    
    # 只在非重载器进程中进行端口检查和清理
    if not is_reloader:
        # 检查端口是否被占用
        if is_port_in_use(PORT):
            logger.info(f"端口 {PORT} 已被占用，尝试清理...")
            if not kill_process_on_port(PORT):
                logger.error(f"无法释放端口 {PORT}，请手动终止占用该端口的进程")
                sys.exit(1)
    
    app = create_app()
    
    # 只在主进程中显示启动信息
    if not is_reloader:
        logger.info(f"启动应用于端口 {PORT}")
    
    try:
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=True
        )
    except OSError as e:
        if not is_reloader and "Address already in use" in str(e):
            logger.error(f"端口 {PORT} 仍然被占用，无法启动应用")
            sys.exit(1)
        raise

if __name__ == '__main__':
    # 注册信号处理
    def signal_handler(signum, frame):
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main() 