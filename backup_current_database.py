#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用数据库备份工具 - 配置驱动

📌 核心特性：
- 从 DATABASE_URL 环境变量读取当前数据库配置
- 自动识别数据库类型（local/sp8d/ovs/unknown）
- 支持 PostgreSQL 和 SQLite
- 配置驱动，不是硬编码

🎯 使用场景：
- Web 界面自动备份当前数据库
- 本地开发环境备份本地数据库
- 云端环境备份远端数据库

⚠️ 与旧脚本的区别：
- backup_cloud_pma_db.py   → 硬编码备份 SP8D 云端数据库
- simple_ovs_backup.py     → 硬编码备份 OVS 云端数据库
- backup_current_database.py → 读取 DATABASE_URL，备份当前数据库

使用方法：
    python3 backup_current_database.py

遵循 CLAUDE.md 中的备份工具规范
"""

import os
import sys
import psycopg2
import logging
import subprocess
import datetime
import shutil
from urllib.parse import urlparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('通用数据库备份')


class CurrentDatabaseBackup:
    """通用数据库备份类 - 从配置读取"""

    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = os.path.join(os.getcwd(), 'cloud_db_backups')
        os.makedirs(self.backup_dir, exist_ok=True)

        # 从 config.py 读取当前数据库配置
        self.db_url = self._get_database_url()
        self.db_config = self.parse_db_url(self.db_url)
        self.db_type = self.identify_db_type()

        logger.info(f"目标数据库: {self.db_type}")
        logger.info(f"数据库URL: {self._mask_password(self.db_url)}")

    def _get_database_url(self):
        """获取数据库URL - 优先从config.py读取"""
        try:
            # 尝试从config.py读取
            from config import Config
            db_url = Config.SQLALCHEMY_DATABASE_URI
            if db_url:
                logger.info("✅ 从config.py获取到DATABASE_URL")
                return db_url
        except Exception as e:
            logger.warning(f"从config.py读取失败: {e}")

        # 尝试从环境变量读取
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            logger.info("✅ 从环境变量获取到DATABASE_URL")
            return db_url

        # 默认使用本地SQLite
        logger.warning("⚠️ 未找到DATABASE_URL配置，使用默认SQLite")
        return 'sqlite:///pma.db'

    def _mask_password(self, db_url):
        """隐藏密码显示"""
        if ':' in db_url and '@' in db_url:
            try:
                parsed = urlparse(db_url)
                if parsed.password:
                    return db_url.replace(parsed.password, '***')
            except:
                pass
        return db_url

    def identify_db_type(self):
        """根据数据库URL识别类型（用于文件命名）"""
        db_url_lower = self.db_url.lower()

        # 本地数据库
        if 'localhost' in db_url_lower or '127.0.0.1' in db_url_lower or 'sqlite' in db_url_lower:
            return 'local'

        # SP8D云端数据库
        if 'iqcyimnjtnmomvfuwjzw' in db_url_lower or 'sp8d' in db_url_lower:
            return 'sp8d'

        # OVS云端数据库
        if 'pqzviljbpfoqvyfulakl' in db_url_lower or 'ovs' in db_url_lower or 'pma_db_ovs' in db_url_lower:
            return 'ovs'

        # 未知类型
        return 'unknown'

    def parse_db_url(self, db_url):
        """解析数据库URL"""
        if db_url.startswith('sqlite'):
            return {
                'type': 'sqlite',
                'path': db_url.replace('sqlite:///', '').replace('sqlite://', '')
            }

        # PostgreSQL
        try:
            parsed = urlparse(db_url)
            return {
                'type': 'postgresql',
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'user': parsed.username,
                'password': parsed.password,
                'dbname': parsed.path.lstrip('/')
            }
        except Exception as e:
            logger.error(f"解析数据库URL失败: {e}")
            return {'type': 'unknown'}

    def test_connection(self):
        """测试数据库连接"""
        logger.info("测试数据库连接...")

        if self.db_config['type'] == 'sqlite':
            # SQLite 检查文件是否存在
            db_path = self.db_config['path']
            if os.path.exists(db_path):
                logger.info(f"✅ SQLite数据库存在: {db_path}")
                return True
            else:
                logger.error(f"❌ SQLite数据库不存在: {db_path}")
                return False

        elif self.db_config['type'] == 'postgresql':
            # PostgreSQL 连接测试
            try:
                conn = psycopg2.connect(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    dbname=self.db_config['dbname']
                )
                cursor = conn.cursor()

                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                logger.info(f"✅ 连接成功: {version[0][:50]}...")

                # 获取基本信息
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
                db_size = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """)
                table_count = cursor.fetchone()[0]

                logger.info(f"数据库大小: {db_size}, 表数量: {table_count}")

                cursor.close()
                conn.close()
                return True
            except Exception as e:
                logger.error(f"❌ 连接失败: {str(e)}")
                return False
        else:
            logger.error(f"❌ 不支持的数据库类型: {self.db_config['type']}")
            return False

    def backup_database(self):
        """备份数据库"""
        logger.info(f"开始备份 {self.db_type} 数据库...")

        if self.db_config['type'] == 'sqlite':
            return self._backup_sqlite()
        elif self.db_config['type'] == 'postgresql':
            return self._backup_postgresql()
        else:
            logger.error(f"不支持的数据库类型: {self.db_config['type']}")
            return None

    def _backup_sqlite(self):
        """备份SQLite数据库"""
        logger.info("执行SQLite备份...")

        db_path = self.db_config['path']
        backup_file = os.path.join(
            self.backup_dir,
            f'pma_db_{self.db_type}_backup_{self.timestamp}.db'
        )

        try:
            shutil.copy2(db_path, backup_file)
            file_size = os.path.getsize(backup_file)
            logger.info(f"✅ SQLite备份成功: {backup_file}")
            logger.info(f"📁 文件大小: {file_size / 1024 / 1024:.2f} MB")
            return backup_file
        except Exception as e:
            logger.error(f"SQLite备份失败: {e}")
            return None

    def _backup_postgresql(self):
        """备份PostgreSQL数据库 - 使用 pg_dump"""
        logger.info("执行PostgreSQL备份（使用pg_dump）...")

        # 备份文件路径
        backup_file = os.path.join(
            self.backup_dir,
            f'pma_db_{self.db_type}_backup_{self.timestamp}.sql'
        )

        # 构造 pg_dump 命令
        env = os.environ.copy()
        if self.db_config['password']:
            env['PGPASSWORD'] = self.db_config['password']

        cmd = [
            'pg_dump',
            '-h', self.db_config['host'],
            '-p', str(self.db_config['port']),
            '-U', self.db_config['user'],
            '-d', self.db_config['dbname'],
            '-F', 'p',  # plain text format
            '-f', backup_file,
            '--no-owner',
            '--no-privileges'
        ]

        try:
            # 执行备份
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode == 0:
                file_size = os.path.getsize(backup_file)
                logger.info(f"✅ PostgreSQL备份成功: {backup_file}")
                logger.info(f"📁 文件大小: {file_size / 1024 / 1024:.2f} MB")
                return backup_file
            else:
                logger.error(f"pg_dump执行失败: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.error("备份超时（10分钟）")
            return None
        except Exception as e:
            logger.error(f"备份失败: {e}")
            return None

    def generate_stats(self, backup_file):
        """生成备份统计信息"""
        if self.db_config['type'] != 'postgresql':
            return

        logger.info("📊 统计备份数据...")

        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                dbname=self.db_config['dbname']
            )
            cursor = conn.cursor()

            # 统计总行数
            cursor.execute("""
                SELECT SUM(n_live_tup)
                FROM pg_stat_user_tables
            """)
            total_rows = cursor.fetchone()[0] or 0

            logger.info(f"📊 数据统计: {total_rows:,} 行")

            cursor.close()
            conn.close()
        except Exception as e:
            logger.warning(f"统计数据失败: {e}")

    def run(self):
        """执行备份流程"""
        logger.info("🚀 开始数据库备份流程...")
        logger.info(f"数据库类型: {self.db_type}")
        logger.info(f"备份时间: {self.timestamp}")

        # 测试连接
        if not self.test_connection():
            logger.error("❌ 数据库连接失败，备份终止")
            sys.exit(1)

        # 执行备份
        backup_file = self.backup_database()

        if not backup_file:
            logger.error("❌ 备份失败")
            sys.exit(1)

        # 生成统计信息
        self.generate_stats(backup_file)

        logger.info("🎉 数据库备份完成!")
        logger.info(f"📁 备份文件: {backup_file}")
        logger.info("🎯 备份操作成功!")

        return backup_file


def main():
    """主函数"""
    try:
        backup = CurrentDatabaseBackup()
        backup.run()
    except KeyboardInterrupt:
        logger.info("\n备份被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"备份过程出错: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
