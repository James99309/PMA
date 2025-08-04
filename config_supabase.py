#!/usr/bin/env python3
"""
直接注入Supabase配置到Flask应用中
"""

import os

def inject_supabase_config():
    """直接设置Supabase配置到环境变量"""
    supabase_config = {
        'SUPABASE_URL': 'https://pqzviljbpfoqvyfulakl.supabase.co',
        'SUPABASE_KEY': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxenZpbGpicGZvcXZ5ZnVsYWtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU5NzMsImV4cCI6MjA0MTU0OTczM30.kSqVh-mTkERrDWrnZx6kJgG3RzmwUW6oV6QN83ehNUM',
        'SUPABASE_BUCKET': 'product-images',
        'FORCE_CLOUD_UPLOAD': 'true'
    }
    
    print("🔧 注入Supabase配置到环境变量...")
    for key, value in supabase_config.items():
        os.environ[key] = value
        display_value = value[:20] + '...' if len(value) > 20 else value
        print(f"   ✅ {key}: {display_value}")
    
    return True

if __name__ == "__main__":
    inject_supabase_config()
    
    # 启动Flask应用
    print("\n🚀 启动Flask应用...")
    from app import create_app
    app = create_app()
    
    # 验证配置
    with app.app_context():
        print(f"\n🔍 Flask应用中的配置:")
        print(f"   SUPABASE_URL: {os.getenv('SUPABASE_URL', 'NOT SET')}")
        print(f"   FORCE_CLOUD_UPLOAD: {os.getenv('FORCE_CLOUD_UPLOAD', 'NOT SET')}")
    
    print("\n🌐 应用启动在 http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)