#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新app/__init__.py，集成版本检查功能

此脚本用于：
1. 将版本检查功能集成到应用初始化过程中
2. 添加API endpoint用于查询版本信息
3. 在生产环境启动时检查代码一致性
"""

import os
import re
import sys
import logging
import shutil
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_init.log')
    ]
)
logger = logging.getLogger(__name__)

# 应用初始化文件路径
INIT_FILE = 'app/__init__.py'

# 备份原始文件
def backup_file(filepath):
    """创建文件备份"""
    if not os.path.exists(filepath):
        logger.error(f"文件不存在，无法备份: {filepath}")
        return False
        
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{filepath}.bak.{timestamp}"
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"已创建备份: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

# 添加版本检查代码
def add_version_check_to_init(init_file=INIT_FILE):
    """
    更新app/__init__.py，添加版本检查功能
    
    参数:
        init_file: 初始化文件路径
        
    返回:
        bool: 操作是否成功
    """
    if not os.path.exists(init_file):
        logger.error(f"文件不存在: {init_file}")
        return False
    
    # 备份原始文件
    if not backup_file(init_file):
        return False
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 在导入部分添加版本检查模块
        import_pattern = r'from datetime import timedelta'
        import_replacement = """from datetime import timedelta
from app.utils import version_check"""
        
        content = re.sub(import_pattern, import_replacement, content)
        
        # 2. 在应用初始化完成后添加版本检查
        init_end_pattern = r'logger\.info\("数据库表创建成功"\)'
        init_end_replacement = """logger.info("数据库表创建成功")
            
            # 版本检查
            try:
                from app.utils.version_check import update_version_check
                update_version_check()
                logger.info("应用版本检查完成")
            except Exception as e:
                logger.error(f"应用版本检查失败: {str(e)}")"""
                
        content = re.sub(init_end_pattern, init_end_replacement, content)
        
        # 3. 添加版本信息API路由
        api_pattern = r'# 注册API v1蓝图\s+app\.register_blueprint\(api_v1_bp, url_prefix=\'\/api\/v1\'\)'
        api_replacement = """# 注册API v1蓝图
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    # 添加版本信息API路由
    @app.route('/api/version', methods=['GET'])
    def get_app_version():
        \"\"\"返回应用版本信息\"\"\"
        try:
            from app.utils.version_check import get_app_version
            version_info = get_app_version()
            return {'success': True, 'data': version_info}
        except Exception as e:
            logger.error(f"获取应用版本信息失败: {str(e)}")
            return {'success': False, 'message': '获取版本信息失败', 'error': str(e)}, 500"""
                
        content = re.sub(api_pattern, api_replacement, content)
        
        # 4. 添加配置项
        config_pattern = r'app\.config\.from_object\(config_class\)'
        config_replacement = """app.config.from_object(config_class)
    
    # 设置应用版本
    app.config['APP_VERSION'] = '1.0.1'  # 根据实际版本修改"""
                
        content = re.sub(config_pattern, config_replacement, content)
        
        # 写入更新后的内容
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"已更新 {init_file}，集成了版本检查功能")
        return True
        
    except Exception as e:
        logger.error(f"更新 {init_file} 失败: {str(e)}")
        return False

# 添加版本检查API测试脚本
def create_api_test_script():
    """创建API测试脚本"""
    test_script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
版本API测试脚本

此脚本用于测试版本信息API功能
\"\"\"

import requests
import json
import sys

def test_version_api(base_url):
    \"\"\"测试版本信息API\"\"\"
    url = f"{base_url}/api/version"
    
    try:
        print(f"正在请求版本信息: {url}")
        response = requests.get(url)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("API响应:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                if data.get('success'):
                    print("\n版本信息获取成功!")
                    
                    # 检查一致性
                    consistency = data.get('data', {}).get('consistency', {})
                    if consistency:
                        print("\n模块一致性状态:")
                        for module, status in consistency.items():
                            is_consistent = status.get('is_consistent', False)
                            status_str = "一致" if is_consistent else "不一致"
                            print(f"  {module}: {status_str}")
                            
                            if not is_consistent:
                                print(f"    不一致文件: {status.get('inconsistent_files', [])}")
                    
                    return True
                else:
                    print(f"版本信息获取失败: {data.get('message', '未知错误')}")
                    return False
            except json.JSONDecodeError:
                print("解析API响应失败，返回的不是有效的JSON")
                print(f"响应内容: {response.text}")
                return False
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"测试版本API时出错: {str(e)}")
        return False

def main():
    \"\"\"主函数\"\"\"
    if len(sys.argv) < 2:
        print("用法: python test_version_api.py <base_url>")
        print("示例: python test_version_api.py http://localhost:5000")
        return 1
    
    base_url = sys.argv[1]
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url
    
    success = test_version_api(base_url)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    script_path = "test_version_api.py"
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(test_script)
        logger.info(f"已创建API测试脚本: {script_path}")
        return True
    except Exception as e:
        logger.error(f"创建API测试脚本失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始更新应用初始化文件，集成版本检查功能...")
    
    # 添加版本检查到初始化文件
    if add_version_check_to_init():
        logger.info("成功将版本检查功能集成到应用初始化过程中")
    else:
        logger.error("集成版本检查功能失败")
        return 1
    
    # 创建API测试脚本
    if create_api_test_script():
        logger.info("成功创建版本API测试脚本")
    else:
        logger.warning("创建版本API测试脚本失败")
    
    # 输出结果
    print("\n更新完成！")
    print("请重启应用，版本检查功能将在应用启动时自动运行")
    print("使用 test_version_api.py 脚本测试版本信息API功能")
    print("示例: python test_version_api.py http://localhost:8082")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
更新app/__init__.py，集成版本检查功能

此脚本用于：
1. 将版本检查功能集成到应用初始化过程中
2. 添加API endpoint用于查询版本信息
3. 在生产环境启动时检查代码一致性
"""

import os
import re
import sys
import logging
import shutil
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_init.log')
    ]
)
logger = logging.getLogger(__name__)

# 应用初始化文件路径
INIT_FILE = 'app/__init__.py'

# 备份原始文件
def backup_file(filepath):
    """创建文件备份"""
    if not os.path.exists(filepath):
        logger.error(f"文件不存在，无法备份: {filepath}")
        return False
        
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{filepath}.bak.{timestamp}"
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"已创建备份: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

# 添加版本检查代码
def add_version_check_to_init(init_file=INIT_FILE):
    """
    更新app/__init__.py，添加版本检查功能
    
    参数:
        init_file: 初始化文件路径
        
    返回:
        bool: 操作是否成功
    """
    if not os.path.exists(init_file):
        logger.error(f"文件不存在: {init_file}")
        return False
    
    # 备份原始文件
    if not backup_file(init_file):
        return False
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 在导入部分添加版本检查模块
        import_pattern = r'from datetime import timedelta'
        import_replacement = """from datetime import timedelta
from app.utils import version_check"""
        
        content = re.sub(import_pattern, import_replacement, content)
        
        # 2. 在应用初始化完成后添加版本检查
        init_end_pattern = r'logger\.info\("数据库表创建成功"\)'
        init_end_replacement = """logger.info("数据库表创建成功")
            
            # 版本检查
            try:
                from app.utils.version_check import update_version_check
                update_version_check()
                logger.info("应用版本检查完成")
            except Exception as e:
                logger.error(f"应用版本检查失败: {str(e)}")"""
                
        content = re.sub(init_end_pattern, init_end_replacement, content)
        
        # 3. 添加版本信息API路由
        api_pattern = r'# 注册API v1蓝图\s+app\.register_blueprint\(api_v1_bp, url_prefix=\'\/api\/v1\'\)'
        api_replacement = """# 注册API v1蓝图
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    # 添加版本信息API路由
    @app.route('/api/version', methods=['GET'])
    def get_app_version():
        \"\"\"返回应用版本信息\"\"\"
        try:
            from app.utils.version_check import get_app_version
            version_info = get_app_version()
            return {'success': True, 'data': version_info}
        except Exception as e:
            logger.error(f"获取应用版本信息失败: {str(e)}")
            return {'success': False, 'message': '获取版本信息失败', 'error': str(e)}, 500"""
                
        content = re.sub(api_pattern, api_replacement, content)
        
        # 4. 添加配置项
        config_pattern = r'app\.config\.from_object\(config_class\)'
        config_replacement = """app.config.from_object(config_class)
    
    # 设置应用版本
    app.config['APP_VERSION'] = '1.0.1'  # 根据实际版本修改"""
                
        content = re.sub(config_pattern, config_replacement, content)
        
        # 写入更新后的内容
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"已更新 {init_file}，集成了版本检查功能")
        return True
        
    except Exception as e:
        logger.error(f"更新 {init_file} 失败: {str(e)}")
        return False

# 添加版本检查API测试脚本
def create_api_test_script():
    """创建API测试脚本"""
    test_script = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
版本API测试脚本

此脚本用于测试版本信息API功能
\"\"\"

import requests
import json
import sys

def test_version_api(base_url):
    \"\"\"测试版本信息API\"\"\"
    url = f"{base_url}/api/version"
    
    try:
        print(f"正在请求版本信息: {url}")
        response = requests.get(url)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("API响应:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                if data.get('success'):
                    print("\n版本信息获取成功!")
                    
                    # 检查一致性
                    consistency = data.get('data', {}).get('consistency', {})
                    if consistency:
                        print("\n模块一致性状态:")
                        for module, status in consistency.items():
                            is_consistent = status.get('is_consistent', False)
                            status_str = "一致" if is_consistent else "不一致"
                            print(f"  {module}: {status_str}")
                            
                            if not is_consistent:
                                print(f"    不一致文件: {status.get('inconsistent_files', [])}")
                    
                    return True
                else:
                    print(f"版本信息获取失败: {data.get('message', '未知错误')}")
                    return False
            except json.JSONDecodeError:
                print("解析API响应失败，返回的不是有效的JSON")
                print(f"响应内容: {response.text}")
                return False
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"测试版本API时出错: {str(e)}")
        return False

def main():
    \"\"\"主函数\"\"\"
    if len(sys.argv) < 2:
        print("用法: python test_version_api.py <base_url>")
        print("示例: python test_version_api.py http://localhost:5000")
        return 1
    
    base_url = sys.argv[1]
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url
    
    success = test_version_api(base_url)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    script_path = "test_version_api.py"
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(test_script)
        logger.info(f"已创建API测试脚本: {script_path}")
        return True
    except Exception as e:
        logger.error(f"创建API测试脚本失败: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("开始更新应用初始化文件，集成版本检查功能...")
    
    # 添加版本检查到初始化文件
    if add_version_check_to_init():
        logger.info("成功将版本检查功能集成到应用初始化过程中")
    else:
        logger.error("集成版本检查功能失败")
        return 1
    
    # 创建API测试脚本
    if create_api_test_script():
        logger.info("成功创建版本API测试脚本")
    else:
        logger.warning("创建版本API测试脚本失败")
    
    # 输出结果
    print("\n更新完成！")
    print("请重启应用，版本检查功能将在应用启动时自动运行")
    print("使用 test_version_api.py 脚本测试版本信息API功能")
    print("示例: python test_version_api.py http://localhost:8082")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 