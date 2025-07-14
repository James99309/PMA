#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复报价单权限函数的系统级权限支持
"""

import logging
import shutil
import datetime
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('权限函数修复')

class QuotationPermissionFixer:
    def __init__(self):
        self.quotation_file = "/Users/nijie/Documents/PMA/app/views/quotation.py"
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def backup_original_file(self):
        """备份原文件"""
        backup_file = f"{self.quotation_file}.backup_{self.timestamp}"
        shutil.copy2(self.quotation_file, backup_file)
        logger.info(f"✅ 原文件已备份: {backup_file}")
        return backup_file
    
    def read_current_function(self):
        """读取当前的can_view_quotation函数"""
        with open(self.quotation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 找到函数的开始和结束
        start_marker = "def can_view_quotation(user, quotation):"
        start_pos = content.find(start_marker)
        
        if start_pos == -1:
            logger.error("❌ 未找到can_view_quotation函数")
            return None
        
        # 找到函数的结束（下一个def或文件结尾）
        lines = content[start_pos:].split('\n')
        function_lines = [lines[0]]  # 包含函数定义行
        
        for i, line in enumerate(lines[1:], 1):
            # 如果遇到新的函数定义（不缩进的def），则停止
            if line.strip().startswith('def ') and not line.startswith('    '):
                break
            # 如果遇到新的@装饰器（不缩进），则停止
            if line.strip().startswith('@') and not line.startswith('    '):
                break
            function_lines.append(line)
        
        current_function = '\n'.join(function_lines)
        logger.info("📋 找到当前的can_view_quotation函数")
        return current_function, start_pos, start_pos + len('\n'.join(lines[:len(function_lines)]))
    
    def generate_fixed_function(self):
        """生成修复后的函数"""
        fixed_function = '''def can_view_quotation(user, quotation):
    """
    判断用户是否有权查看该报价单：
    1. 归属人
    2. 厂商负责人（项目的厂商负责人可以查看项目相关的报价单）
    3. 归属链
    4. 基于四级权限系统的访问控制
    5. 特殊角色权限
    暂不考虑共享
    """
    if user.role == 'admin':
        return True
    if user.id == quotation.owner_id:
        return True
    
    # 厂商负责人可以查看项目相关的报价单
    if (hasattr(quotation, 'project') and quotation.project and 
        hasattr(quotation.project, 'vendor_sales_manager_id') and 
        quotation.project.vendor_sales_manager_id == user.id):
        return True
    
    # 统一处理角色字符串，去除空格
    user_role = user.role.strip() if user.role else ''
    
    # 财务总监可以查看所有报价单
    if user_role in ['finance_director', 'finace_director']:
        return True
    
    # 🔧 修复：使用四级权限系统进行权限判断
    if user.has_permission('quotation', 'view'):
        permission_level = user.get_permission_level('quotation')
        
        if permission_level == 'system':
            # 系统级权限：可以查看所有报价单
            return True
        elif permission_level == 'company' and user.company_name:
            # 企业级权限：可以查看企业下所有报价单
            if hasattr(quotation, 'project') and quotation.project:
                from app.models.user import User
                project_owner = User.query.get(quotation.project.owner_id)
                return project_owner and project_owner.company_name == user.company_name
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以查看部门下所有报价单
            if hasattr(quotation, 'project') and quotation.project:
                from app.models.user import User
                project_owner = User.query.get(quotation.project.owner_id)
                return (project_owner and 
                       project_owner.company_name == user.company_name and
                       project_owner.department == user.department)
        # 个人级权限会在下面的归属链检查中处理
    
    # 归属链检查
    from app.models.user import Affiliation
    affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
    if quotation.owner_id in affiliation_owner_ids:
        return True
        
    # 营销总监特殊处理：可以查看销售重点和渠道跟进项目的报价单
    if user_role == 'sales_director':
        # 获取关联项目
        from app.models.project import Project
        project = Project.query.get(quotation.project_id)
        if project and project.project_type in ['sales_focus', 'channel_follow', '销售重点', '渠道跟进']:
            return True
        
    # 渠道经理特殊处理：可以查看渠道跟进项目的报价单
    if user_role == 'channel_manager':
        from app.models.project import Project
        project = Project.query.get(quotation.project_id)
        if project and project.project_type in ['channel_follow', '渠道跟进']:
            return True
    
    return False'''
        
        return fixed_function
    
    def apply_fix(self):
        """应用修复"""
        logger.info("🚀 开始修复报价单权限函数...")
        
        # 1. 备份原文件
        backup_file = self.backup_original_file()
        
        # 2. 读取当前函数
        function_info = self.read_current_function()
        if not function_info:
            return False
        
        current_function, start_pos, end_pos = function_info
        
        # 3. 生成修复后的函数
        fixed_function = self.generate_fixed_function()
        
        # 4. 读取整个文件内容
        with open(self.quotation_file, 'r', encoding='utf-8') as f:
            full_content = f.read()
        
        # 5. 替换函数
        new_content = full_content[:start_pos] + fixed_function + full_content[end_pos:]
        
        # 6. 写入修复后的内容
        with open(self.quotation_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info("✅ 报价单权限函数修复完成!")
        
        # 7. 显示修复内容
        logger.info("\n🔧 主要修复内容:")
        logger.info("1. 添加了四级权限系统支持")
        logger.info("2. 系统级权限现在可以查看所有报价单")
        logger.info("3. 企业级权限可以查看企业内所有报价单")
        logger.info("4. 部门级权限可以查看部门内所有报价单")
        logger.info("5. 保留了特殊角色的权限逻辑")
        
        return True
    
    def verify_fix(self):
        """验证修复结果"""
        logger.info("\n🔍 验证修复结果...")
        
        with open(self.quotation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键修复点
        checks = [
            ("permission_level = user.get_permission_level('quotation')", "权限级别获取"),
            ("if permission_level == 'system':", "系统级权限检查"),
            ("return True  # 系统级权限", "系统级权限返回"),
            ("elif permission_level == 'company'", "企业级权限检查"),
            ("elif permission_level == 'department'", "部门级权限检查")
        ]
        
        for check_text, description in checks:
            if check_text in content:
                logger.info(f"✅ {description}: 已添加")
            else:
                logger.warning(f"⚠️ {description}: 未找到")
        
        logger.info("\n💡 测试建议:")
        logger.info("1. 重启Flask应用")
        logger.info("2. 用liuwei账户登录")
        logger.info("3. 测试报价单列表页面")
        logger.info("4. 测试从项目详情页面访问报价单")
        logger.info("5. 确认能看到所有268个报价单")

if __name__ == "__main__":
    fixer = QuotationPermissionFixer()
    success = fixer.apply_fix()
    if success:
        fixer.verify_fix()
        print("\n" + "="*60)
        print("🎉 修复完成! liuwei用户现在应该能够访问所有报价单")
        print("="*60)
    else:
        print("❌ 修复失败")
        exit(1)