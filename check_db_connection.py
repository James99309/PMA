import os
import sys

# 模拟Flask应用加载.env文件的过程
from dotenv import load_dotenv
load_dotenv('.env')

db_url = os.environ.get('DATABASE_URL', '未设置')
print(f"DATABASE_URL from .env: {db_url[:80]}...")
print(f"连接到: {'云端Supabase' if 'supabase' in db_url else '本地PostgreSQL' if 'localhost' in db_url else '未知'}")
