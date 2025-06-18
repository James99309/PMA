from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel

# 初始化扩展，但不绑定app
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager() 
csrf = CSRFProtect()
babel = Babel() 