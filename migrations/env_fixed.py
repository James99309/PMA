import logging
from logging.config import fileConfig
import os

from flask import current_app

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


def get_app_and_db():
    """获取应用实例和数据库实例，处理应用上下文问题"""
    try:
        # 尝试获取当前应用上下文
        app = current_app._get_current_object()
        target_db = app.extensions['migrate'].db
        return app, target_db
    except RuntimeError:
        # 如果没有应用上下文，创建一个
        import sys
        import os
        
        # 添加项目根目录到Python路径
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        try:
            # 导入应用
            from run import app
            
            # 在应用上下文中运行
            with app.app_context():
                target_db = app.extensions['migrate'].db
                return app, target_db
        except ImportError:
            # 如果无法导入run.py，尝试其他方式
            try:
                from app import create_app
                app = create_app()
                with app.app_context():
                    target_db = app.extensions['migrate'].db
                    return app, target_db
            except ImportError:
                # 最后的备选方案：直接使用环境变量配置
                logger.warning("无法获取Flask应用，使用环境变量直接配置数据库连接")
                return None, None


# 尝试获取应用和数据库配置
app_instance, target_db = get_app_and_db()

if app_instance and target_db:
    # 有应用上下文的情况
    with app_instance.app_context():
        config.set_main_option('sqlalchemy.url', get_engine_url())
else:
    # 无应用上下文的情况，直接使用环境变量
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError("无法获取数据库连接URL，请设置 DATABASE_URL 环境变量")
    
    # 处理PostgreSQL URL格式
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://')
    
    config.set_main_option('sqlalchemy.url', database_url)
    logger.info(f"使用环境变量DATABASE_URL配置数据库连接")


def get_metadata():
    if target_db:
        if hasattr(target_db, 'metadatas'):
            return target_db.metadatas[None]
        return target_db.metadata
    else:
        # 无Flask应用时，使用简单的元数据
        from sqlalchemy import MetaData
        return MetaData()


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    # 处理有无Flask应用上下文的情况
    if app_instance and target_db:
        # 有Flask应用的情况
        with app_instance.app_context():
            conf_args = app_instance.extensions['migrate'].configure_args
            if conf_args.get("process_revision_directives") is None:
                conf_args["process_revision_directives"] = process_revision_directives

            connectable = get_engine()

            with connectable.connect() as connection:
                context.configure(
                    connection=connection,
                    target_metadata=get_metadata(),
                    **conf_args
                )

                with context.begin_transaction():
                    context.run_migrations()
    else:
        # 无Flask应用的情况，直接连接数据库
        from sqlalchemy import engine_from_config, pool
        
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=get_metadata(),
                process_revision_directives=process_revision_directives
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()