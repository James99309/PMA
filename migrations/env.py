import logging
import os
from logging.config import fileConfig

from flask import current_app
from sqlalchemy import create_engine, pool

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

# 检查是否有DATABASE_URL环境变量（独立运行模式）
database_url = os.getenv('DATABASE_URL')
if database_url:
    # 独立运行模式 - 使用环境变量
    config.set_main_option('sqlalchemy.url', database_url)
    target_db = None
    logger.info("使用独立模式运行 - DATABASE_URL环境变量")
else:
    # Flask应用模式
    config.set_main_option('sqlalchemy.url', get_engine_url())
    target_db = current_app.extensions['migrate'].db
    logger.info("使用Flask应用模式运行")

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_metadata():
    if target_db is None:
        # 独立模式 - 尝试从app导入模型元数据
        try:
            import sys
            # 确保项目根目录在路径中
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from app import db
            # 导入所有模型以确保它们被注册
            from app import models  # noqa: F401
            if hasattr(db, 'metadatas'):
                return db.metadatas[None]
            return db.metadata
        except Exception as e:
            logger.warning(f"独立模式下无法获取元数据: {e}")
            return None
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


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
    if target_db is None:
        # 独立模式 - 直接使用环境变量中的数据库URL
        logger.info("运行在独立模式")
        connectable = create_engine(
            config.get_main_option("sqlalchemy.url"),
            poolclass=pool.NullPool,
        )
        
        with connectable.connect() as connection:
            # 检测Supabase环境并设置search_path
            database_url = config.get_main_option("sqlalchemy.url")
            if 'supabase.com' in database_url or 'supabase.co' in database_url:
                logger.info('检测到Supabase环境，设置search_path为public')
                from sqlalchemy import text
                connection.execute(text('SET search_path TO public'))
            
            context.configure(
                connection=connection,
                target_metadata=get_metadata()
            )

            with context.begin_transaction():
                context.run_migrations()
    else:
        # Flask应用模式
        logger.info("运行在Flask应用模式")
        
        # this callback is used to prevent an auto-migration from being generated
        # when there are no changes to the schema
        # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
        def process_revision_directives(context, revision, directives):
            if getattr(config.cmd_opts, 'autogenerate', False):
                script = directives[0]
                if script.upgrade_ops.is_empty():
                    directives[:] = []
                    logger.info('No changes in schema detected.')

        conf_args = current_app.extensions['migrate'].configure_args
        if conf_args.get("process_revision_directives") is None:
            conf_args["process_revision_directives"] = process_revision_directives

        connectable = get_engine()

        with connectable.connect() as connection:
            # 检测Supabase环境并设置search_path
            database_url = str(connectable.url)
            if 'supabase.com' in database_url or 'supabase.co' in database_url:
                logger.info('检测到Supabase环境，设置search_path为public')
                from sqlalchemy import text
                connection.execute(text('SET search_path TO public'))
            
            context.configure(
                connection=connection,
                target_metadata=get_metadata(),
                **conf_args
            )

            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
