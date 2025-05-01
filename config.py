import os
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 调试模式
    DEBUG = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('SMTP_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('SMTP_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('SENDER_EMAIL')
    MAIL_PASSWORD = os.environ.get('SENDER_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('SENDER_EMAIL')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'James.ni@evertacsolutions.com' 
    
    # 应用域名，用于邮件中的链接
    APP_DOMAIN = os.environ.get('APP_DOMAIN') or 'http://localhost:8082'
    
    PORT = int(os.environ.get('FLASK_PORT', 8082))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False 