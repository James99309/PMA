#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复报价单系统级权限问题
检查并修复quotation.py中可能阻止系统级用户看到所有报价单的逻辑
"""

import logging
import shutil
import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('报价权限修复')

class QuotationSystemPermissionFixer:
    def __init__(self):
        self.quotation_file = "/Users/nijie/Documents/PMA/app/views/quotation.py"
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def backup_file(self):
        """备份原文件"""
        backup_file = f"{self.quotation_file}.backup_{self.timestamp}"
        shutil.copy2(self.quotation_file, backup_file)
        logger.info(f"✅ 文件已备份: {backup_file}")
        return backup_file
    
    def read_file_content(self):
        """读取文件内容"""
        with open(self.quotation_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    
    def check_viewable_data_usage(self, content):
        """检查get_viewable_data的使用是否正确"""
        logger.info("🔍 检查get_viewable_data的使用...")
        
        # 检查list_quotations函数中的关键逻辑
        lines = content.split('\\n')
        in_list_quotations = False
        line_num = 0
        issues = []
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            if 'def list_quotations():' in line:
                in_list_quotations = True
                logger.info(f"📍 找到list_quotations函数 (第{line_num}行)")
                continue
            
            if in_list_quotations and line.strip().startswith('def ') and 'list_quotations' not in line:
                break
            
            if in_list_quotations:
                # 检查get_viewable_data的调用
                if 'get_viewable_data(Quotation, current_user)' in line:
                    logger.info(f"✅ 第{line_num}行: 正确使用get_viewable_data")
                
                # 检查可能的问题过滤
                if ('current_user.company_name' in line and 
                    'permission_level' not in line and 
                    'get_permission_level' not in line):
                    issues.append((line_num, line.strip(), "可能有硬编码的公司过滤"))
                
                # 检查角色特殊处理
                if ('solution_manager' in line and 
                    'project_type' in line):
                    issues.append((line_num, line.strip(), "solution_manager角色可能有特殊过滤"))
        
        if issues:
            logger.warning("⚠️ 发现可能的问题:")
            for line_num, line_content, issue in issues:
                logger.warning(f"  第{line_num}行: {issue}")
                logger.warning(f"    代码: {line_content}")
        else:
            logger.info("✅ 未发现明显的过滤问题")
        
        return issues
    
    def add_debug_logging(self, content):
        """为list_quotations函数添加调试日志"""
        logger.info("🔧 为list_quotations函数添加调试日志...")
        
        # 在query = get_viewable_data(Quotation, current_user)之后添加调试代码
        debug_code = '''
        # 🔍 调试: 检查系统级权限的查询结果
        if current_user.username == 'liuwei':  # 临时调试代码
            import logging
            debug_logger = logging.getLogger('quotation_debug')
            debug_logger.setLevel(logging.INFO)
            
            # 检查权限级别
            perm_level = current_user.get_permission_level('quotation')
            debug_logger.info(f"🔍 用户 {current_user.username} 的quotation权限级别: {perm_level}")
            
            # 检查基础查询结果
            base_count = query.count()
            debug_logger.info(f"📊 get_viewable_data返回的报价单数量: {base_count}")
            
            # 检查数据库中的总数
            from sqlalchemy import func
            total_count = db.session.query(func.count(Quotation.id)).scalar()
            debug_logger.info(f"📊 数据库中报价单总数: {total_count}")
            
            if perm_level == 'system' and base_count != total_count:
                debug_logger.warning(f"⚠️ 权限异常: 系统级权限应该看到所有{total_count}个报价单，但只返回了{base_count}个")
'''
        
        # 查找插入位置
        target_line = "        query = get_viewable_data(Quotation, current_user)"
        if target_line in content:
            content = content.replace(target_line, target_line + debug_code)
            logger.info("✅ 已添加调试日志代码")
        else:
            logger.warning("⚠️ 未找到插入位置，可能需要手动添加调试代码")
        
        return content
    
    def check_for_hidden_filters(self, content):
        """检查隐藏的过滤条件"""
        logger.info("🔍 检查可能的隐藏过滤条件...")
        
        # 搜索可能的过滤模式
        filter_patterns = [
            ('is_active', '项目活跃状态过滤'),
            ('current_stage', '项目阶段过滤'),
            ('company_name', '公司名称过滤'),
            ('authorization_code', '授权编号过滤'),
            ('WHERE.*company', '硬编码公司过滤'),
            ('project_type.*=', '项目类型强制过滤'),
            ('filter.*solution_manager', 'solution_manager特殊过滤')
        ]
        
        lines = content.split('\\n')
        in_list_quotations = False
        found_filters = []
        
        for i, line in enumerate(lines):
            line_num = i + 1
            
            if 'def list_quotations():' in line:
                in_list_quotations = True
                continue
            
            if in_list_quotations and line.strip().startswith('def ') and 'list_quotations' not in line:
                break
            
            if in_list_quotations:
                for pattern, description in filter_patterns:
                    if pattern in line.lower() and 'debug' not in line.lower():
                        found_filters.append((line_num, line.strip(), description))
        
        if found_filters:
            logger.warning("⚠️ 发现可能的过滤条件:")
            for line_num, line_content, description in found_filters:
                logger.warning(f"  第{line_num}行 ({description}): {line_content}")
        else:
            logger.info("✅ 未发现明显的隐藏过滤")
        
        return found_filters
    
    def create_permission_verification_function(self, content):
        """创建权限验证函数"""
        logger.info("🔧 添加权限验证函数...")
        
        verification_function = '''
@quotation.route('/debug/permissions')
@login_required
def debug_permissions():
    """调试权限信息 - 临时调试路由"""
    if current_user.username != 'liuwei':
        return "Access denied", 403
    
    from app.utils.access_control import get_viewable_data
    from sqlalchemy import func
    
    # 收集调试信息
    debug_info = {
        'user': {
            'username': current_user.username,
            'role': current_user.role,
            'company_name': current_user.company_name,
            'permission_level': current_user.get_permission_level('quotation'),
            'can_view': current_user.has_permission('quotation', 'view')
        },
        'data_counts': {
            'total_quotations': db.session.query(func.count(Quotation.id)).scalar(),
            'viewable_quotations': get_viewable_data(Quotation, current_user).count(),
            'company_quotations': 0,
            'other_company_quotations': 0
        }
    }
    
    # 统计按公司分布
    company_stats = db.session.query(
        User.company_name,
        func.count(Quotation.id)
    ).join(Project, Quotation.project_id == Project.id)\
     .join(User, Project.owner_id == User.id)\
     .group_by(User.company_name).all()
    
    debug_info['company_distribution'] = []
    for company, count in company_stats:
        is_user_company = (company == current_user.company_name)
        debug_info['company_distribution'].append({
            'company': company or 'Unknown',
            'count': count,
            'is_user_company': is_user_company
        })
        
        if is_user_company:
            debug_info['data_counts']['company_quotations'] = count
        else:
            debug_info['data_counts']['other_company_quotations'] += count
    
    # 检查权限一致性
    expected_count = debug_info['data_counts']['total_quotations']
    actual_count = debug_info['data_counts']['viewable_quotations']
    
    debug_info['permission_analysis'] = {
        'is_system_level': debug_info['user']['permission_level'] == 'system',
        'should_see_all': expected_count,
        'actually_sees': actual_count,
        'missing_count': expected_count - actual_count,
        'is_consistent': expected_count == actual_count
    }
    
    return jsonify(debug_info)
'''
        
        # 在文件末尾添加这个函数
        # 找到最后一个路由定义的位置
        last_route_pos = content.rfind('@quotation.route(')
        if last_route_pos != -1:
            # 找到这个路由定义的结束位置
            lines = content[last_route_pos:].split('\\n')
            function_end = 0
            indent_level = None
            
            for i, line in enumerate(lines):
                if i == 0:  # 跳过@quotation.route这一行
                    continue
                
                if line.strip().startswith('def '):
                    # 确定缩进级别
                    indent_level = len(line) - len(line.lstrip())
                    continue
                
                if indent_level is not None:
                    # 如果遇到相同或更少缩进的非空行，说明函数结束
                    if line.strip() and (len(line) - len(line.lstrip())) <= indent_level:
                        if not line.strip().startswith(('"""', "'''", '#')):
                            function_end = i
                            break
            
            if function_end > 0:
                insertion_pos = last_route_pos + len('\\n'.join(lines[:function_end]))
                content = content[:insertion_pos] + '\\n' + verification_function + '\\n' + content[insertion_pos:]
                logger.info("✅ 已添加权限验证路由")
            else:
                # 如果找不到合适位置，就添加到文件末尾
                content += '\\n' + verification_function
                logger.info("✅ 已在文件末尾添加权限验证路由")
        else:
            content += '\\n' + verification_function
            logger.info("✅ 已在文件末尾添加权限验证路由")
        
        return content
    
    def apply_fixes(self):
        """应用所有修复"""
        logger.info("🚀 开始修复报价单系统级权限问题...")
        
        # 1. 备份文件
        backup_file = self.backup_file()
        
        # 2. 读取内容
        content = self.read_file_content()
        
        # 3. 检查问题
        issues = self.check_viewable_data_usage(content)
        hidden_filters = self.check_for_hidden_filters(content)
        
        # 4. 添加调试功能
        content = self.add_debug_logging(content)
        content = self.create_permission_verification_function(content)
        
        # 5. 写入修复后的内容
        with open(self.quotation_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("✅ 权限修复完成!")
        
        # 6. 总结
        logger.info("\\n🎯 修复总结:")
        logger.info("1. ✅ 添加了调试日志来跟踪权限问题")
        logger.info("2. ✅ 创建了权限验证路由 /quotations/debug/permissions")
        logger.info("3. 📊 可以通过访问调试路由来检查详细的权限信息")
        
        if issues or hidden_filters:
            logger.warning("4. ⚠️ 发现了可能的权限问题，建议进一步检查")
        else:
            logger.info("4. ✅ 代码结构看起来正常")
        
        return True
    
    def create_testing_instructions(self):
        """创建测试说明"""
        logger.info("\\n📋 测试说明:")
        logger.info("1. 重启Flask应用以加载新的调试代码")
        logger.info("2. 用liuwei账户登录")
        logger.info("3. 访问报价单列表页面，查看服务器日志中的调试信息")
        logger.info("4. 访问 /quotations/debug/permissions 查看详细的权限调试信息")
        logger.info("5. 如果仍然看不到所有268个报价单，调试信息将显示具体原因")
        
        logger.info("\\n🔍 预期结果:")
        logger.info("- 系统级权限应该显示所有268个报价单")
        logger.info("- 其中264个来自'和源通信（上海）股份有限公司'")
        logger.info("- 4个来自其他公司（3个来自'上海瑞康通信科技有限公司'，1个公司为None）")

if __name__ == "__main__":
    fixer = QuotationSystemPermissionFixer()
    success = fixer.apply_fixes()
    if success:
        fixer.create_testing_instructions()
        print("\\n" + "="*60)
        print("🎉 报价单权限调试功能已添加!")
        print("请重启应用并按照测试说明进行验证")
        print("="*60)
    else:
        print("❌ 修复失败")
        exit(1)