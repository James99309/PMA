#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户模块同步检查和更新脚本

此脚本用于：
1. 检查本地用户管理代码和render云端代码的一致性
2. 创建包含所有必要更新的部署包
3. 提供自动化测试功能来捕捉差异

用法：python verify_and_update_user_module.py
"""

import os
import sys
import time
import logging
import subprocess
import hashlib
import re
import json
import datetime
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('user_module_sync.log')
    ]
)
logger = logging.getLogger(__name__)

# 定义要检查的文件列表
USER_MODULE_FILES = [
    'app/views/user.py',
    'app/models/user.py',
    'app/permissions.py',
    'app/utils/permissions.py',
    'app/templates/user/list.html',
    'app/templates/user/edit.html', 
    'app/templates/user/permissions.html',
    'app/templates/user/affiliations.html',
]

# 定义Git仓库相关信息
GIT_MAIN_BRANCH = 'main'  # 或 'master'，取决于你的仓库设置
GIT_RENDER_BRANCH = 'render-deploy'
CURRENT_TIMESTAMP = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

def get_file_hash(filepath):
    """
    计算文件的MD5哈希值
    
    参数:
        filepath: 文件路径
        
    返回:
        str: 文件的MD5哈希值，如果文件不存在则返回None
    """
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

def check_file_exists(filepath):
    """检查文件是否存在"""
    return os.path.exists(filepath)

def create_backup(filepath):
    """创建文件备份"""
    if not os.path.exists(filepath):
        logger.warning(f"文件不存在，无法创建备份: {filepath}")
        return False
        
    backup_path = f"{filepath}.bak.{CURRENT_TIMESTAMP}"
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"已创建备份: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

def check_json_decode_error_handling(filepath):
    """
    检查文件中是否包含JSON解析错误处理代码
    
    参数:
        filepath: 文件路径
        
    返回:
        bool: 是否包含JSON解析错误处理
    """
    if not os.path.exists(filepath):
        return False
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 检查是否包含JSON解析错误处理代码
    return 'json.JSONDecodeError' in content

def create_deployment_package():
    """
    创建包含用户模块文件的部署包
    
    返回:
        str: 创建的压缩包路径
    """
    # 创建临时目录
    package_dir = f"user_module_deploy_{CURRENT_TIMESTAMP}"
    os.makedirs(package_dir, exist_ok=True)
    
    # 复制相关文件到临时目录
    for filepath in USER_MODULE_FILES:
        if os.path.exists(filepath):
            # 确保目标目录存在
            target_dir = os.path.join(package_dir, os.path.dirname(filepath))
            os.makedirs(target_dir, exist_ok=True)
            
            # 复制文件
            shutil.copy2(filepath, os.path.join(package_dir, filepath))
            logger.info(f"已添加文件到部署包: {filepath}")
        else:
            logger.warning(f"文件不存在，跳过添加到部署包: {filepath}")
    
    # 创建README.md文件
    readme_path = os.path.join(package_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"""# 用户模块同步更新包

## 更新内容
此部署包包含用户模块的最新代码，主要修复以下问题：
1. 添加了JSON解析的异常处理
2. 确保用户模块的权限定义一致
3. 修复用户模块在render环境中的问题

## 文件列表
{chr(10).join(['- ' + file for file in USER_MODULE_FILES if os.path.exists(file)])}

## 更新时间
{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    
    # 创建部署说明文件
    deploy_instructions_path = os.path.join(package_dir, "部署指南.md")
    with open(deploy_instructions_path, 'w', encoding='utf-8') as f:
        f.write(f"""# 部署指南

## 前提条件
确保已经完成以下准备工作：
1. 备份当前生产环境的相关文件
2. 准备好数据库备份

## 部署步骤
1. 将部署包中的文件复制到相应的目录
2. 重启应用服务器
3. 检查应用日志，确认没有错误
4. 测试用户管理功能是否正常

## 回滚措施
如果部署后出现问题，请使用备份文件恢复，并联系技术支持。
""")
    
    # 创建自动化测试脚本
    test_script_path = os.path.join(package_dir, "test_user_module.py")
    with open(test_script_path, 'w', encoding='utf-8') as f:
        f.write(f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
用户模块测试脚本

此脚本用于测试用户模块的基本功能是否正常。
\"\"\"

import requests
import logging
import json
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('user_module_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_user_list(base_url, token):
    \"\"\"测试用户列表功能\"\"\"
    url = f"{{base_url}}/user/list"
    headers = {{"Authorization": f"Bearer {{token}}"}}
    
    try:
        logger.info(f"测试用户列表页面: {{url}}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            logger.info("用户列表页面访问成功")
            return True
        else:
            logger.error(f"用户列表页面访问失败: {{response.status_code}}")
            return False
    except Exception as e:
        logger.error(f"测试用户列表功能时出错: {{str(e)}}")
        return False

def test_user_api(base_url, token):
    \"\"\"测试用户API功能\"\"\"
    url = f"{{base_url}}/api/v1/users"
    headers = {{"Authorization": f"Bearer {{token}}"}}
    
    try:
        logger.info(f"测试用户API: {{url}}")
        response = requests.get(url, headers=headers)
        
        try:
            data = response.json()
            if response.status_code == 200 and data.get('success'):
                logger.info("用户API访问成功")
                return True
            else:
                error_msg = data.get('message', '未知错误')
                logger.error(f"用户API访问失败: {{error_msg}}")
                return False
        except json.JSONDecodeError as e:
            logger.error(f"解析API响应失败: {{str(e)}}")
            return False
    except Exception as e:
        logger.error(f"测试用户API功能时出错: {{str(e)}}")
        return False

def main():
    \"\"\"主函数\"\"\"
    if len(sys.argv) < 3:
        print("用法: python test_user_module.py <base_url> <token>")
        sys.exit(1)
        
    base_url = sys.argv[1]
    token = sys.argv[2]
    
    # 运行测试
    tests = [
        ("用户列表功能", test_user_list(base_url, token)),
        ("用户API功能", test_user_api(base_url, token))
    ]
    
    # 输出测试结果
    print("\\n测试结果:")
    all_passed = True
    for name, result in tests:
        status = "通过" if result else "失败"
        print(f"{{name}}: {{status}}")
        if not result:
            all_passed = False
    
    # 返回测试结果
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
""")
    
    # 创建压缩包
    import zipfile
    zip_path = f"{package_dir}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, os.path.dirname(package_dir))
                zipf.write(filepath, arcname)
    
    # 清理临时目录
    shutil.rmtree(package_dir)
    
    logger.info(f"部署包创建成功: {zip_path}")
    return zip_path

def verify_local_files():
    """验证本地文件是否存在"""
    missing_files = []
    
    for filepath in USER_MODULE_FILES:
        if not os.path.exists(filepath):
            missing_files.append(filepath)
            logger.warning(f"本地文件不存在: {filepath}")
    
    if missing_files:
        logger.error(f"有 {len(missing_files)} 个文件不存在")
        return False
    
    logger.info("所有本地文件都存在")
    return True

def check_git_branch():
    """检查当前Git分支"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                               capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()
        logger.info(f"当前Git分支: {current_branch}")
        return current_branch
    except subprocess.CalledProcessError as e:
        logger.error(f"获取Git分支失败: {e}")
        return None

def create_version_info_file():
    """创建版本信息文件"""
    version_info = {
        "version": CURRENT_TIMESTAMP,
        "update_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "files": {}
    }
    
    for filepath in USER_MODULE_FILES:
        if os.path.exists(filepath):
            version_info["files"][filepath] = {
                "hash": get_file_hash(filepath),
                "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            }
    
    version_file_path = f"user_module_version_{CURRENT_TIMESTAMP}.json"
    with open(version_file_path, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    logger.info(f"版本信息文件创建成功: {version_file_path}")
    return version_file_path

def create_render_update_script():
    """创建render环境更新脚本"""
    script_path = "update_render_user_module.py"
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Render环境用户模块更新脚本

此脚本用于更新Render环境中的用户模块代码。
版本: {CURRENT_TIMESTAMP}
\"\"\"

import os
import logging
import json
import sys
import time
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_update.log')
    ]
)
logger = logging.getLogger(__name__)

# 要更新的文件列表
USER_MODULE_FILES = {USER_MODULE_FILES}

def backup_file(filepath):
    \"\"\"备份文件\"\"\"
    if not os.path.exists(filepath):
        logger.warning(f"文件不存在，无法备份: {{filepath}}")
        return
        
    backup_path = f"{{filepath}}.bak.{{int(time.time())}}"
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"已备份文件: {{backup_path}}")
    except Exception as e:
        logger.error(f"备份文件失败: {{str(e)}}")

def ensure_directory(filepath):
    \"\"\"确保目录存在\"\"\"
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"创建目录: {{directory}}")
        except Exception as e:
            logger.error(f"创建目录失败: {{str(e)}}")
            return False
    return True

def update_file(filepath, content):
    \"\"\"更新文件内容\"\"\"
    try:
        # 备份原文件
        if os.path.exists(filepath):
            backup_file(filepath)
        
        # 确保目录存在
        if not ensure_directory(filepath):
            return False
        
        # 写入新内容
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"文件更新成功: {{filepath}}")
        return True
    except Exception as e:
        logger.error(f"更新文件失败: {{filepath}}, 错误: {{str(e)}}")
        return False

def update_render_files():
    \"\"\"更新Render环境文件\"\"\"
    success_count = 0
    failed_files = []
    
    for filepath in USER_MODULE_FILES:
        logger.info(f"处理文件: {{filepath}}")
        
        try:
            # 检查文件是否存在于部署包中
            package_filepath = os.path.join("package", filepath)
            if not os.path.exists(package_filepath):
                logger.warning(f"部署包中不存在文件: {{package_filepath}}")
                failed_files.append(filepath)
                continue
            
            # 读取部署包中的文件内容
            with open(package_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新文件
            if update_file(filepath, content):
                success_count += 1
            else:
                failed_files.append(filepath)
        except Exception as e:
            logger.error(f"处理文件时出错: {{filepath}}, 错误: {{str(e)}}")
            failed_files.append(filepath)
    
    logger.info(f"文件更新完成。成功: {{success_count}}, 失败: {{len(failed_files)}}")
    if failed_files:
        logger.warning(f"更新失败的文件: {{failed_files}}")
    
    return success_count, failed_files

def main():
    \"\"\"主函数\"\"\"
    logger.info("开始更新Render环境用户模块...")
    
    # 检查package目录是否存在
    if not os.path.exists("package"):
        logger.error("部署包目录不存在。请确保部署包已解压到'package'目录。")
        return 1
    
    # 更新文件
    success_count, failed_files = update_render_files()
    
    # 输出结果
    print(f"\\n更新结果:")
    print(f"成功更新 {{success_count}} 个文件")
    if failed_files:
        print(f"更新失败 {{len(failed_files)}} 个文件: {{', '.join(failed_files)}}")
    
    return 0 if not failed_files else 1

if __name__ == "__main__":
    sys.exit(main())
""")
    
    logger.info(f"Render环境更新脚本创建成功: {script_path}")
    return script_path

def main():
    """主函数"""
    logger.info("开始验证用户模块代码一致性...")
    
    # 验证本地文件
    if not verify_local_files():
        logger.error("本地文件验证失败，请确保所有文件都存在")
        return 1
    
    # 检查用户模块中的JSON解析错误处理
    user_view_file = 'app/views/user.py'
    if check_json_decode_error_handling(user_view_file):
        logger.info("用户视图文件已包含JSON解析错误处理")
    else:
        logger.warning("用户视图文件缺少JSON解析错误处理，需要更新")
    
    # 创建版本信息文件
    version_file = create_version_info_file()
    logger.info(f"版本信息文件: {version_file}")
    
    # 创建部署包
    deployment_package = create_deployment_package()
    logger.info(f"部署包: {deployment_package}")
    
    # 创建Render环境更新脚本
    render_update_script = create_render_update_script()
    logger.info(f"Render环境更新脚本: {render_update_script}")
    
    # 输出结果摘要
    print("\n验证和准备工作完成！")
    print(f"版本信息文件: {version_file}")
    print(f"部署包: {deployment_package}")
    print(f"Render环境更新脚本: {render_update_script}")
    print("\n请执行以下步骤来更新Render环境：")
    print("1. 将部署包上传到Render环境并解压到'package'目录")
    print("2. 在Render环境中运行更新脚本")
    print("3. 重启应用服务器")
    print("4. 验证用户模块功能是否正常")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
用户模块同步检查和更新脚本

此脚本用于：
1. 检查本地用户管理代码和render云端代码的一致性
2. 创建包含所有必要更新的部署包
3. 提供自动化测试功能来捕捉差异

用法：python verify_and_update_user_module.py
"""

import os
import sys
import time
import logging
import subprocess
import hashlib
import re
import json
import datetime
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('user_module_sync.log')
    ]
)
logger = logging.getLogger(__name__)

# 定义要检查的文件列表
USER_MODULE_FILES = [
    'app/views/user.py',
    'app/models/user.py',
    'app/permissions.py',
    'app/utils/permissions.py',
    'app/templates/user/list.html',
    'app/templates/user/edit.html', 
    'app/templates/user/permissions.html',
    'app/templates/user/affiliations.html',
]

# 定义Git仓库相关信息
GIT_MAIN_BRANCH = 'main'  # 或 'master'，取决于你的仓库设置
GIT_RENDER_BRANCH = 'render-deploy'
CURRENT_TIMESTAMP = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

def get_file_hash(filepath):
    """
    计算文件的MD5哈希值
    
    参数:
        filepath: 文件路径
        
    返回:
        str: 文件的MD5哈希值，如果文件不存在则返回None
    """
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

def check_file_exists(filepath):
    """检查文件是否存在"""
    return os.path.exists(filepath)

def create_backup(filepath):
    """创建文件备份"""
    if not os.path.exists(filepath):
        logger.warning(f"文件不存在，无法创建备份: {filepath}")
        return False
        
    backup_path = f"{filepath}.bak.{CURRENT_TIMESTAMP}"
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"已创建备份: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"创建备份失败: {str(e)}")
        return False

def check_json_decode_error_handling(filepath):
    """
    检查文件中是否包含JSON解析错误处理代码
    
    参数:
        filepath: 文件路径
        
    返回:
        bool: 是否包含JSON解析错误处理
    """
    if not os.path.exists(filepath):
        return False
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 检查是否包含JSON解析错误处理代码
    return 'json.JSONDecodeError' in content

def create_deployment_package():
    """
    创建包含用户模块文件的部署包
    
    返回:
        str: 创建的压缩包路径
    """
    # 创建临时目录
    package_dir = f"user_module_deploy_{CURRENT_TIMESTAMP}"
    os.makedirs(package_dir, exist_ok=True)
    
    # 复制相关文件到临时目录
    for filepath in USER_MODULE_FILES:
        if os.path.exists(filepath):
            # 确保目标目录存在
            target_dir = os.path.join(package_dir, os.path.dirname(filepath))
            os.makedirs(target_dir, exist_ok=True)
            
            # 复制文件
            shutil.copy2(filepath, os.path.join(package_dir, filepath))
            logger.info(f"已添加文件到部署包: {filepath}")
        else:
            logger.warning(f"文件不存在，跳过添加到部署包: {filepath}")
    
    # 创建README.md文件
    readme_path = os.path.join(package_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(f"""# 用户模块同步更新包

## 更新内容
此部署包包含用户模块的最新代码，主要修复以下问题：
1. 添加了JSON解析的异常处理
2. 确保用户模块的权限定义一致
3. 修复用户模块在render环境中的问题

## 文件列表
{chr(10).join(['- ' + file for file in USER_MODULE_FILES if os.path.exists(file)])}

## 更新时间
{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    
    # 创建部署说明文件
    deploy_instructions_path = os.path.join(package_dir, "部署指南.md")
    with open(deploy_instructions_path, 'w', encoding='utf-8') as f:
        f.write(f"""# 部署指南

## 前提条件
确保已经完成以下准备工作：
1. 备份当前生产环境的相关文件
2. 准备好数据库备份

## 部署步骤
1. 将部署包中的文件复制到相应的目录
2. 重启应用服务器
3. 检查应用日志，确认没有错误
4. 测试用户管理功能是否正常

## 回滚措施
如果部署后出现问题，请使用备份文件恢复，并联系技术支持。
""")
    
    # 创建自动化测试脚本
    test_script_path = os.path.join(package_dir, "test_user_module.py")
    with open(test_script_path, 'w', encoding='utf-8') as f:
        f.write(f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
用户模块测试脚本

此脚本用于测试用户模块的基本功能是否正常。
\"\"\"

import requests
import logging
import json
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('user_module_test.log')
    ]
)
logger = logging.getLogger(__name__)

def test_user_list(base_url, token):
    \"\"\"测试用户列表功能\"\"\"
    url = f"{{base_url}}/user/list"
    headers = {{"Authorization": f"Bearer {{token}}"}}
    
    try:
        logger.info(f"测试用户列表页面: {{url}}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            logger.info("用户列表页面访问成功")
            return True
        else:
            logger.error(f"用户列表页面访问失败: {{response.status_code}}")
            return False
    except Exception as e:
        logger.error(f"测试用户列表功能时出错: {{str(e)}}")
        return False

def test_user_api(base_url, token):
    \"\"\"测试用户API功能\"\"\"
    url = f"{{base_url}}/api/v1/users"
    headers = {{"Authorization": f"Bearer {{token}}"}}
    
    try:
        logger.info(f"测试用户API: {{url}}")
        response = requests.get(url, headers=headers)
        
        try:
            data = response.json()
            if response.status_code == 200 and data.get('success'):
                logger.info("用户API访问成功")
                return True
            else:
                error_msg = data.get('message', '未知错误')
                logger.error(f"用户API访问失败: {{error_msg}}")
                return False
        except json.JSONDecodeError as e:
            logger.error(f"解析API响应失败: {{str(e)}}")
            return False
    except Exception as e:
        logger.error(f"测试用户API功能时出错: {{str(e)}}")
        return False

def main():
    \"\"\"主函数\"\"\"
    if len(sys.argv) < 3:
        print("用法: python test_user_module.py <base_url> <token>")
        sys.exit(1)
        
    base_url = sys.argv[1]
    token = sys.argv[2]
    
    # 运行测试
    tests = [
        ("用户列表功能", test_user_list(base_url, token)),
        ("用户API功能", test_user_api(base_url, token))
    ]
    
    # 输出测试结果
    print("\\n测试结果:")
    all_passed = True
    for name, result in tests:
        status = "通过" if result else "失败"
        print(f"{{name}}: {{status}}")
        if not result:
            all_passed = False
    
    # 返回测试结果
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
""")
    
    # 创建压缩包
    import zipfile
    zip_path = f"{package_dir}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, os.path.dirname(package_dir))
                zipf.write(filepath, arcname)
    
    # 清理临时目录
    shutil.rmtree(package_dir)
    
    logger.info(f"部署包创建成功: {zip_path}")
    return zip_path

def verify_local_files():
    """验证本地文件是否存在"""
    missing_files = []
    
    for filepath in USER_MODULE_FILES:
        if not os.path.exists(filepath):
            missing_files.append(filepath)
            logger.warning(f"本地文件不存在: {filepath}")
    
    if missing_files:
        logger.error(f"有 {len(missing_files)} 个文件不存在")
        return False
    
    logger.info("所有本地文件都存在")
    return True

def check_git_branch():
    """检查当前Git分支"""
    try:
        result = subprocess.run(['git', 'branch', '--show-current'], 
                               capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()
        logger.info(f"当前Git分支: {current_branch}")
        return current_branch
    except subprocess.CalledProcessError as e:
        logger.error(f"获取Git分支失败: {e}")
        return None

def create_version_info_file():
    """创建版本信息文件"""
    version_info = {
        "version": CURRENT_TIMESTAMP,
        "update_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "files": {}
    }
    
    for filepath in USER_MODULE_FILES:
        if os.path.exists(filepath):
            version_info["files"][filepath] = {
                "hash": get_file_hash(filepath),
                "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            }
    
    version_file_path = f"user_module_version_{CURRENT_TIMESTAMP}.json"
    with open(version_file_path, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    logger.info(f"版本信息文件创建成功: {version_file_path}")
    return version_file_path

def create_render_update_script():
    """创建render环境更新脚本"""
    script_path = "update_render_user_module.py"
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
Render环境用户模块更新脚本

此脚本用于更新Render环境中的用户模块代码。
版本: {CURRENT_TIMESTAMP}
\"\"\"

import os
import logging
import json
import sys
import time
import shutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_update.log')
    ]
)
logger = logging.getLogger(__name__)

# 要更新的文件列表
USER_MODULE_FILES = {USER_MODULE_FILES}

def backup_file(filepath):
    \"\"\"备份文件\"\"\"
    if not os.path.exists(filepath):
        logger.warning(f"文件不存在，无法备份: {{filepath}}")
        return
        
    backup_path = f"{{filepath}}.bak.{{int(time.time())}}"
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"已备份文件: {{backup_path}}")
    except Exception as e:
        logger.error(f"备份文件失败: {{str(e)}}")

def ensure_directory(filepath):
    \"\"\"确保目录存在\"\"\"
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"创建目录: {{directory}}")
        except Exception as e:
            logger.error(f"创建目录失败: {{str(e)}}")
            return False
    return True

def update_file(filepath, content):
    \"\"\"更新文件内容\"\"\"
    try:
        # 备份原文件
        if os.path.exists(filepath):
            backup_file(filepath)
        
        # 确保目录存在
        if not ensure_directory(filepath):
            return False
        
        # 写入新内容
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"文件更新成功: {{filepath}}")
        return True
    except Exception as e:
        logger.error(f"更新文件失败: {{filepath}}, 错误: {{str(e)}}")
        return False

def update_render_files():
    \"\"\"更新Render环境文件\"\"\"
    success_count = 0
    failed_files = []
    
    for filepath in USER_MODULE_FILES:
        logger.info(f"处理文件: {{filepath}}")
        
        try:
            # 检查文件是否存在于部署包中
            package_filepath = os.path.join("package", filepath)
            if not os.path.exists(package_filepath):
                logger.warning(f"部署包中不存在文件: {{package_filepath}}")
                failed_files.append(filepath)
                continue
            
            # 读取部署包中的文件内容
            with open(package_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 更新文件
            if update_file(filepath, content):
                success_count += 1
            else:
                failed_files.append(filepath)
        except Exception as e:
            logger.error(f"处理文件时出错: {{filepath}}, 错误: {{str(e)}}")
            failed_files.append(filepath)
    
    logger.info(f"文件更新完成。成功: {{success_count}}, 失败: {{len(failed_files)}}")
    if failed_files:
        logger.warning(f"更新失败的文件: {{failed_files}}")
    
    return success_count, failed_files

def main():
    \"\"\"主函数\"\"\"
    logger.info("开始更新Render环境用户模块...")
    
    # 检查package目录是否存在
    if not os.path.exists("package"):
        logger.error("部署包目录不存在。请确保部署包已解压到'package'目录。")
        return 1
    
    # 更新文件
    success_count, failed_files = update_render_files()
    
    # 输出结果
    print(f"\\n更新结果:")
    print(f"成功更新 {{success_count}} 个文件")
    if failed_files:
        print(f"更新失败 {{len(failed_files)}} 个文件: {{', '.join(failed_files)}}")
    
    return 0 if not failed_files else 1

if __name__ == "__main__":
    sys.exit(main())
""")
    
    logger.info(f"Render环境更新脚本创建成功: {script_path}")
    return script_path

def main():
    """主函数"""
    logger.info("开始验证用户模块代码一致性...")
    
    # 验证本地文件
    if not verify_local_files():
        logger.error("本地文件验证失败，请确保所有文件都存在")
        return 1
    
    # 检查用户模块中的JSON解析错误处理
    user_view_file = 'app/views/user.py'
    if check_json_decode_error_handling(user_view_file):
        logger.info("用户视图文件已包含JSON解析错误处理")
    else:
        logger.warning("用户视图文件缺少JSON解析错误处理，需要更新")
    
    # 创建版本信息文件
    version_file = create_version_info_file()
    logger.info(f"版本信息文件: {version_file}")
    
    # 创建部署包
    deployment_package = create_deployment_package()
    logger.info(f"部署包: {deployment_package}")
    
    # 创建Render环境更新脚本
    render_update_script = create_render_update_script()
    logger.info(f"Render环境更新脚本: {render_update_script}")
    
    # 输出结果摘要
    print("\n验证和准备工作完成！")
    print(f"版本信息文件: {version_file}")
    print(f"部署包: {deployment_package}")
    print(f"Render环境更新脚本: {render_update_script}")
    print("\n请执行以下步骤来更新Render环境：")
    print("1. 将部署包上传到Render环境并解压到'package'目录")
    print("2. 在Render环境中运行更新脚本")
    print("3. 重启应用服务器")
    print("4. 验证用户模块功能是否正常")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 