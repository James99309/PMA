#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
版本检查工具

此模块用于检查应用代码版本一致性，主要功能：
1. 在应用启动时检测当前代码版本
2. 比较本地环境和云环境的代码差异
3. 提供版本信息API供前端显示
"""

import os
import sys
import logging
import json
import hashlib
import time
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

# 关键模块及其文件列表
MODULE_FILES = {
    'user': [
        'app/views/user.py',
        'app/models/user.py',
        'app/permissions.py',
        'app/utils/permissions.py',
    ],
    'customer': [
        'app/views/customer.py',
        'app/models/customer.py',
    ],
    'project': [
        'app/views/project.py',
        'app/models/project.py',
    ],
    'quotation': [
        'app/views/quotation.py',
        'app/models/quotation.py',
    ],
    'product': [
        'app/routes/product.py',
        'app/models/product.py',
        'app/routes/product_management.py',
    ],
}

# 版本信息文件路径
VERSION_FILE = 'app_version.json'

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

def generate_version_info():
    """
    生成应用版本信息，包括各模块代码的哈希值
    
    返回:
        dict: 版本信息字典
    """
    version_info = {
        'app_version': current_app.config.get('APP_VERSION', '1.0.0'),
        'environment': current_app.config.get('FLASK_ENV', 'production'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'modules': {}
    }
    
    # 计算各模块文件的哈希值
    for module_name, files in MODULE_FILES.items():
        module_info = {
            'files': {},
            'status': 'ok'
        }
        
        for filepath in files:
            file_hash = get_file_hash(filepath)
            if file_hash:
                module_info['files'][filepath] = {
                    'hash': file_hash,
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                module_info['status'] = 'incomplete'
                logger.warning(f"模块 {module_name} 缺少文件: {filepath}")
        
        version_info['modules'][module_name] = module_info
    
    return version_info

def save_version_info(version_info):
    """
    保存版本信息到文件
    
    参数:
        version_info: 版本信息字典
    
    返回:
        bool: 操作是否成功
    """
    try:
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2, ensure_ascii=False)
        logger.info(f"版本信息已保存到 {VERSION_FILE}")
        return True
    except Exception as e:
        logger.error(f"保存版本信息失败: {str(e)}")
        return False

def load_version_info():
    """
    从文件加载版本信息
    
    返回:
        dict: 版本信息字典，如果文件不存在则返回None
    """
    if not os.path.exists(VERSION_FILE):
        logger.warning(f"版本信息文件不存在: {VERSION_FILE}")
        return None
        
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            version_info = json.load(f)
        return version_info
    except Exception as e:
        logger.error(f"加载版本信息失败: {str(e)}")
        return None

def check_module_consistency(module_name):
    """
    检查指定模块的代码一致性
    
    参数:
        module_name: 模块名称
    
    返回:
        tuple: (是否一致, 不一致的文件列表)
    """
    version_info = load_version_info()
    if not version_info:
        return False, []
        
    if module_name not in version_info['modules']:
        logger.warning(f"版本信息中不存在模块: {module_name}")
        return False, []
        
    module_info = version_info['modules'][module_name]
    inconsistent_files = []
    
    for filepath in MODULE_FILES.get(module_name, []):
        current_hash = get_file_hash(filepath)
        if not current_hash:
            inconsistent_files.append(filepath)
            continue
            
        saved_hash = module_info['files'].get(filepath, {}).get('hash')
        if not saved_hash or current_hash != saved_hash:
            inconsistent_files.append(filepath)
    
    return len(inconsistent_files) == 0, inconsistent_files

def check_all_modules_consistency():
    """
    检查所有模块的代码一致性
    
    返回:
        dict: 各模块的一致性状态
    """
    result = {}
    
    for module_name in MODULE_FILES.keys():
        is_consistent, inconsistent_files = check_module_consistency(module_name)
        result[module_name] = {
            'is_consistent': is_consistent,
            'inconsistent_files': inconsistent_files
        }
    
    return result

def update_version_check():
    """
    更新版本检查信息
    
    此函数在应用启动时调用，用于更新版本信息文件
    
    返回:
        bool: 操作是否成功
    """
    try:
        version_info = generate_version_info()
        save_version_info(version_info)
        
        # 检查各模块一致性
        consistency_result = check_all_modules_consistency()
        
        # 输出检查结果
        for module_name, status in consistency_result.items():
            if status['is_consistent']:
                logger.info(f"模块 {module_name} 代码一致")
            else:
                logger.warning(f"模块 {module_name} 代码不一致，不一致文件: {status['inconsistent_files']}")
        
        return True
    except Exception as e:
        logger.error(f"更新版本检查信息失败: {str(e)}")
        return False

def get_app_version():
    """
    获取应用版本信息
    
    此函数供API调用，用于返回当前应用版本信息
    
    返回:
        dict: 应用版本信息
    """
    version_info = load_version_info()
    if not version_info:
        return {
            'app_version': current_app.config.get('APP_VERSION', '1.0.0'),
            'environment': current_app.config.get('FLASK_ENV', 'production'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'unknown'
        }
    
    # 添加环境标识
    is_render = os.environ.get('RENDER', False)
    version_info['is_render'] = bool(is_render)
    
    # 检查一致性
    consistency_result = check_all_modules_consistency()
    version_info['consistency'] = consistency_result
    
    # 总体状态
    all_consistent = all(status['is_consistent'] for status in consistency_result.values())
    version_info['status'] = 'consistent' if all_consistent else 'inconsistent'
    
    return version_info 
# -*- coding: utf-8 -*-
"""
版本检查工具

此模块用于检查应用代码版本一致性，主要功能：
1. 在应用启动时检测当前代码版本
2. 比较本地环境和云环境的代码差异
3. 提供版本信息API供前端显示
"""

import os
import sys
import logging
import json
import hashlib
import time
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

# 关键模块及其文件列表
MODULE_FILES = {
    'user': [
        'app/views/user.py',
        'app/models/user.py',
        'app/permissions.py',
        'app/utils/permissions.py',
    ],
    'customer': [
        'app/views/customer.py',
        'app/models/customer.py',
    ],
    'project': [
        'app/views/project.py',
        'app/models/project.py',
    ],
    'quotation': [
        'app/views/quotation.py',
        'app/models/quotation.py',
    ],
    'product': [
        'app/routes/product.py',
        'app/models/product.py',
        'app/routes/product_management.py',
    ],
}

# 版本信息文件路径
VERSION_FILE = 'app_version.json'

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

def generate_version_info():
    """
    生成应用版本信息，包括各模块代码的哈希值
    
    返回:
        dict: 版本信息字典
    """
    version_info = {
        'app_version': current_app.config.get('APP_VERSION', '1.0.0'),
        'environment': current_app.config.get('FLASK_ENV', 'production'),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'modules': {}
    }
    
    # 计算各模块文件的哈希值
    for module_name, files in MODULE_FILES.items():
        module_info = {
            'files': {},
            'status': 'ok'
        }
        
        for filepath in files:
            file_hash = get_file_hash(filepath)
            if file_hash:
                module_info['files'][filepath] = {
                    'hash': file_hash,
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                module_info['status'] = 'incomplete'
                logger.warning(f"模块 {module_name} 缺少文件: {filepath}")
        
        version_info['modules'][module_name] = module_info
    
    return version_info

def save_version_info(version_info):
    """
    保存版本信息到文件
    
    参数:
        version_info: 版本信息字典
    
    返回:
        bool: 操作是否成功
    """
    try:
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2, ensure_ascii=False)
        logger.info(f"版本信息已保存到 {VERSION_FILE}")
        return True
    except Exception as e:
        logger.error(f"保存版本信息失败: {str(e)}")
        return False

def load_version_info():
    """
    从文件加载版本信息
    
    返回:
        dict: 版本信息字典，如果文件不存在则返回None
    """
    if not os.path.exists(VERSION_FILE):
        logger.warning(f"版本信息文件不存在: {VERSION_FILE}")
        return None
        
    try:
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            version_info = json.load(f)
        return version_info
    except Exception as e:
        logger.error(f"加载版本信息失败: {str(e)}")
        return None

def check_module_consistency(module_name):
    """
    检查指定模块的代码一致性
    
    参数:
        module_name: 模块名称
    
    返回:
        tuple: (是否一致, 不一致的文件列表)
    """
    version_info = load_version_info()
    if not version_info:
        return False, []
        
    if module_name not in version_info['modules']:
        logger.warning(f"版本信息中不存在模块: {module_name}")
        return False, []
        
    module_info = version_info['modules'][module_name]
    inconsistent_files = []
    
    for filepath in MODULE_FILES.get(module_name, []):
        current_hash = get_file_hash(filepath)
        if not current_hash:
            inconsistent_files.append(filepath)
            continue
            
        saved_hash = module_info['files'].get(filepath, {}).get('hash')
        if not saved_hash or current_hash != saved_hash:
            inconsistent_files.append(filepath)
    
    return len(inconsistent_files) == 0, inconsistent_files

def check_all_modules_consistency():
    """
    检查所有模块的代码一致性
    
    返回:
        dict: 各模块的一致性状态
    """
    result = {}
    
    for module_name in MODULE_FILES.keys():
        is_consistent, inconsistent_files = check_module_consistency(module_name)
        result[module_name] = {
            'is_consistent': is_consistent,
            'inconsistent_files': inconsistent_files
        }
    
    return result

def update_version_check():
    """
    更新版本检查信息
    
    此函数在应用启动时调用，用于更新版本信息文件
    
    返回:
        bool: 操作是否成功
    """
    try:
        version_info = generate_version_info()
        save_version_info(version_info)
        
        # 检查各模块一致性
        consistency_result = check_all_modules_consistency()
        
        # 输出检查结果
        for module_name, status in consistency_result.items():
            if status['is_consistent']:
                logger.info(f"模块 {module_name} 代码一致")
            else:
                logger.warning(f"模块 {module_name} 代码不一致，不一致文件: {status['inconsistent_files']}")
        
        return True
    except Exception as e:
        logger.error(f"更新版本检查信息失败: {str(e)}")
        return False

def get_app_version():
    """
    获取应用版本信息
    
    此函数供API调用，用于返回当前应用版本信息
    
    返回:
        dict: 应用版本信息
    """
    version_info = load_version_info()
    if not version_info:
        return {
            'app_version': current_app.config.get('APP_VERSION', '1.0.0'),
            'environment': current_app.config.get('FLASK_ENV', 'production'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'unknown'
        }
    
    # 添加环境标识
    is_render = os.environ.get('RENDER', False)
    version_info['is_render'] = bool(is_render)
    
    # 检查一致性
    consistency_result = check_all_modules_consistency()
    version_info['consistency'] = consistency_result
    
    # 总体状态
    all_consistent = all(status['is_consistent'] for status in consistency_result.values())
    version_info['status'] = 'consistent' if all_consistent else 'inconsistent'
    
    return version_info 