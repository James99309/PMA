
# ==================== 云端数据库安全锁定 ====================
import os
import sys

def check_cloud_db_lock():
    """检查云端数据库锁定状态"""
    if os.path.exists('.cloud_db_locked'):
        print("🔒 云端数据库访问已被禁用 - 仅允许本地数据库连接")
        return True
    return False

# 强制检查安全锁定
if check_cloud_db_lock():
    # 强制使用本地数据库配置
    os.environ['DATABASE_URL'] = 'postgresql://localhost/pma_local'
    os.environ['FORCE_LOCAL_DB'] = 'true'
    
    # 清除任何云端数据库环境变量
    cloud_vars = ['CLOUD_DATABASE_URL', 'RENDER_DATABASE_URL', 'PRODUCTION_DATABASE_URL']
    for var in cloud_vars:
        if var in os.environ:
            del os.environ[var]
            print(f"🔒 已清除云端数据库环境变量: {var}")

# 执行安全检查
check_cloud_db_lock()
# ==================== 安全锁定结束 ====================

import os
from dotenv import load_dotenv
from datetime import timedelta
import logging
from urllib.parse import urlparse

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# 🔒 安全配置：禁止连接云端数据库
CLOUD_DB_ACCESS_DISABLED = True
CLOUD_DB_URL = None  # 已禁用云端数据库连接

# 🚫 云端数据库URL已被完全移除
# 本地环境已安全隔离，禁止访问任何云端数据库

# 本地数据库配置
LOCAL_DB_PATH = os.path.join(basedir, 'pma_local.db')
LOCAL_DB_URL = 'postgresql://nijie@localhost:5432/pma_local'  # 本地PostgreSQL数据库

class Config:
    """基础配置类 - 仅支持本地数据库"""
    
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'local-development-secret-key-pma-2025'
    
    # 🔒 强制使用本地数据库
    SQLALCHEMY_DATABASE_URI = LOCAL_DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 开发环境配置
    DEBUG = True
    TESTING = False
    
    # 模板配置
    TEMPLATES_AUTO_RELOAD = True
    
    # JWT配置
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 会话配置 - 本地环境
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # 本地环境使用HTTP
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # 邮件配置
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'james98980566@gmail.com'
    MAIL_PASSWORD = 'cihkheuuyvnkrtrj'
    MAIL_DEFAULT_SENDER = 'james98980566@gmail.com'
    ADMIN_EMAIL = 'James.ni@evertacsolutions.com'
    
    # 应用域名配置
    APP_DOMAIN = 'http://localhost:5005'
    
    # 端口配置
    PORT = 5005
    
    # PostgreSQL连接池配置（本地优化）
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'connect_args': {
            'sslmode': 'disable',  # 本地连接不需要SSL
            'connect_timeout': 10,
            'application_name': 'PMA_Local_Secure_App'
        }
    }
    
    # 应用版本信息
    APP_VERSION = '1.2.2-LOCAL-SECURE'
    APP_NAME = 'PMA项目管理系统 (本地安全版)'
    ENVIRONMENT = 'local_secure'
    
    CLOUD_PROVIDER = 'local'
    
    # 安全配置
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 日志配置
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = False
    
    # 备份服务配置
    BACKUP_ENABLED = True
    BACKUP_SCHEDULE = '00:00'
    BACKUP_RETENTION_DAYS = 30
    BACKUP_LOCATION = os.path.join(basedir, 'backups')

# 🔒 安全别名配置
LocalConfig = Config
DevelopmentConfig = Config
ProductionConfig = Config
TestingConfig = Config
CloudConfig = Config

def get_config():
    """获取配置 - 强制返回本地配置"""
    return Config

def verify_cloud_database():
    """云端数据库验证 - 已禁用"""
    print("🔒 云端数据库访问已被禁用")
    return False

def verify_local_database():
    """验证本地数据库连接"""
    try:
        import psycopg2
        conn = psycopg2.connect(LOCAL_DB_URL)
        conn.close()
        return True
    except Exception as e:
        print(f"本地数据库连接失败: {e}")
        return False

def switch_to_local_database():
    """切换到本地数据库 - 已是默认配置"""
    print("✅ 已使用本地数据库")
    return True

def switch_to_cloud_database():
    """切换到云端数据库 - 已禁用"""
    print("🔒 云端数据库访问已被永久禁用")
    print("⚠️ 如需访问云端数据库，请联系系统管理员")
    return False

# 🔒 安全检查函数
def check_cloud_access_attempt():
    """检查是否有尝试访问云端数据库的行为"""
    import traceback
    stack = traceback.extract_stack()
    
    cloud_keywords = ['cloud_db_url', 'dpg-', 'singapore-postgres', 'render_db']
    for frame in stack:
        for keyword in cloud_keywords:
            if keyword in str(frame):
                print(f"🚨 检测到尝试访问云端数据库: {frame}")
                return True
    return False

# 🔒 运行时安全检查
if CLOUD_DB_ACCESS_DISABLED:
    print("🔒 云端数据库访问已被禁用 - 仅允许本地数据库连接")
