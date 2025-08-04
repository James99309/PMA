#!/usr/bin/env python3
"""
启动应用并加载 Supabase 配置
"""

import os
import sys

def load_env_file(filepath):
    """加载 .env 文件"""
    if not os.path.exists(filepath):
        print(f"❌ 环境文件不存在: {filepath}")
        return False
        
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value
            print(f"✅ 设置环境变量: {key}={value[:20]}{'...' if len(value) > 20 else ''}")
    
    return True

def main():
    """主函数"""
    print("🚀 启动 PMA 应用，使用 Supabase 云端上传...")
    print("=" * 60)
    
    # 加载 Supabase 环境变量
    if load_env_file('.env.supabase'):
        print("\n✅ Supabase 配置加载成功!")
        print(f"   SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
        print(f"   SUPABASE_BUCKET: {os.getenv('SUPABASE_BUCKET')}")
        print(f"   FORCE_CLOUD_UPLOAD: {os.getenv('FORCE_CLOUD_UPLOAD')}")
        
        print("\n🚀 启动 Flask 应用...")
        print("=" * 60)
        
        # 验证环境变量是否正确设置
        print(f"\n🔍 最终验证环境变量:")
        print(f"   SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
        print(f"   SUPABASE_KEY: {os.getenv('SUPABASE_KEY', 'Not Set')[:20]}...")
        print(f"   SUPABASE_BUCKET: {os.getenv('SUPABASE_BUCKET')}")
        print(f"   FORCE_CLOUD_UPLOAD: {os.getenv('FORCE_CLOUD_UPLOAD')}")
        
        # 导入并启动应用
        try:
            # 在导入之前再次确认环境变量
            print(f"\n🔍 导入前最终检查:")
            print(f"   os.environ['SUPABASE_URL']: {os.environ.get('SUPABASE_URL', 'NOT SET')}")
            print(f"   os.environ['FORCE_CLOUD_UPLOAD']: {os.environ.get('FORCE_CLOUD_UPLOAD', 'NOT SET')}")
            
            from app import create_app
            app = create_app()
            
            # 在Flask app创建后验证环境变量是否传递
            with app.app_context():
                import os as app_os
                print(f"\n🔍 Flask上下文中的环境变量:")
                print(f"   SUPABASE_URL: {app_os.getenv('SUPABASE_URL', 'NOT SET')}")
                print(f"   FORCE_CLOUD_UPLOAD: {app_os.getenv('FORCE_CLOUD_UPLOAD', 'NOT SET')}")
            
            print("\n🌐 应用将在 http://localhost:5001 启动")
            print("📝 测试步骤：")
            print("   1. 访问 http://localhost:5001")
            print("   2. 进入报销单创建页面")
            print("   3. 上传文件查看日志")
            app.run(debug=True, host='0.0.0.0', port=5001)
        except ImportError as e:
            print(f"❌ 导入应用失败: {e}")
            print("请确保在项目根目录运行此脚本")
            return 1
    else:
        print("❌ 环境变量加载失败")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())