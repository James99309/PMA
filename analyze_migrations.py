#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
迁移文件分析工具

此脚本用于分析Flask-Migrate生成的数据库迁移文件，查找潜在问题和冗余。
它可以检测迁移链中的问题，如循环依赖、孤立迁移文件和冗余操作。

用法: python analyze_migrations.py
"""

import os
import re
import sys
import importlib.util
from datetime import datetime
from collections import defaultdict

# 配置
MIGRATIONS_DIR = 'migrations/versions'  # 迁移文件目录
REPORT_FILE = 'unused/analysis/migration_analysis_report.md'  # 报告输出文件

def extract_migration_info(file_path):
    """从迁移文件中提取关键信息
    
    参数:
        file_path: 迁移文件的路径
    
    返回:
        包含迁移文件信息的字典，如果解析失败则返回None
    """
    try:
        # 从文件名中提取迁移ID
        file_name = os.path.basename(file_path)
        migration_id = file_name.split('_')[0]
        
        # 从文件内容中提取信息
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取修订号 (revision)
        revision_match = re.search(r'revision\s*=\s*[\'"]([0-9a-f]+)[\'"]', content)
        revision = revision_match.group(1) if revision_match else None
        
        # 提取依赖 (down_revision)
        down_revision_match = re.search(r'down_revision\s*=\s*[\'"]?([0-9a-f]+|None)[\'"]?', content)
        down_revision = down_revision_match.group(1) if down_revision_match else None
        if down_revision == 'None':
            down_revision = None
        
        # 提取分支标记 (branch_labels)
        branch_labels_match = re.search(r'branch_labels\s*=\s*([^#\n]+)', content)
        branch_labels = branch_labels_match.group(1).strip() if branch_labels_match else None
        
        # 提取时间戳
        timestamp_match = re.search(r'Create Date: ([0-9-]+ [0-9:]+)', content)
        create_date = timestamp_match.group(1) if timestamp_match else None
        
        # 提取操作类型
        operations = {
            'create_table': len(re.findall(r'op\.create_table', content)),
            'drop_table': len(re.findall(r'op\.drop_table', content)),
            'add_column': len(re.findall(r'op\.add_column', content)),
            'drop_column': len(re.findall(r'op\.drop_column', content)),
            'alter_column': len(re.findall(r'op\.alter_column', content)),
            'create_index': len(re.findall(r'op\.create_index', content)),
            'drop_index': len(re.findall(r'op\.drop_index', content)),
            'create_foreign_key': len(re.findall(r'op\.create_foreign_key', content)),
            'drop_foreign_key': len(re.findall(r'op\.drop_foreign_key', content)),
            'bulk_insert': len(re.findall(r'op\.bulk_insert', content)),
        }
        
        # 提取表名
        table_matches = re.findall(r'op\.create_table\([\'"]([^\'"]+)[\'"]', content)
        tables_created = list(set(table_matches))
        
        table_drop_matches = re.findall(r'op\.drop_table\([\'"]([^\'"]+)[\'"]', content)
        tables_dropped = list(set(table_drop_matches))
        
        # 尝试提取迁移说明/注释
        comment_match = re.search(r'"""(.+?)"""', content, re.DOTALL)
        comment = comment_match.group(1).strip() if comment_match else ""
        
        return {
            'file_name': file_name,
            'file_path': file_path,
            'migration_id': migration_id,
            'revision': revision,
            'down_revision': down_revision,
            'branch_labels': branch_labels,
            'create_date': create_date,
            'operations': operations,
            'tables_created': tables_created,
            'tables_dropped': tables_dropped,
            'comment': comment
        }
    except Exception as e:
        print(f"解析迁移文件 {file_path} 时出错: {e}")
        return None

def build_migration_tree(migrations):
    """构建迁移树，分析迁移之间的关系
    
    参数:
        migrations: 包含所有迁移信息的列表
    
    返回:
        迁移树的字典表示
    """
    tree = {}
    for migration in migrations:
        tree[migration['revision']] = {
            'down_revision': migration['down_revision'],
            'children': [],
            'info': migration
        }
    
    # 连接父子关系
    for revision, node in tree.items():
        if node['down_revision'] in tree:
            tree[node['down_revision']]['children'].append(revision)
    
    return tree

def check_for_issues(migrations, tree):
    """检查迁移中的潜在问题
    
    参数:
        migrations: 迁移信息列表
        tree: 迁移树
    
    返回:
        发现的问题列表
    """
    issues = []
    
    # 检查多个头节点
    heads = [m for m in migrations if not any(m['revision'] == x['down_revision'] for x in migrations)]
    if len(heads) > 1:
        head_revisions = [h['revision'] for h in heads]
        issues.append({
            'type': 'multiple_heads',
            'severity': 'high',
            'description': f"发现多个头节点: {', '.join(head_revisions)}",
            'migrations': head_revisions
        })
    
    # 检查孤立节点（没有与主链相连）
    root_nodes = [m for m in migrations if m['down_revision'] is None]
    if len(root_nodes) > 1:
        root_revisions = [r['revision'] for r in root_nodes]
        issues.append({
            'type': 'multiple_roots',
            'severity': 'high',
            'description': f"发现多个根节点: {', '.join(root_revisions)}",
            'migrations': root_revisions
        })
    
    # 检查近期有冲突的操作（比如创建和删除同一张表）
    table_operations = defaultdict(list)
    for m in migrations:
        for table in m['tables_created']:
            table_operations[table].append({
                'operation': 'create',
                'migration': m['revision'],
                'date': m['create_date']
            })
        for table in m['tables_dropped']:
            table_operations[table].append({
                'operation': 'drop',
                'migration': m['revision'],
                'date': m['create_date']
            })
    
    for table, operations in table_operations.items():
        if len(operations) > 1:
            # 按时间排序操作
            try:
                sorted_ops = sorted(operations, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'))
                
                # 检查是否有创建后又删除的模式
                for i in range(len(sorted_ops) - 1):
                    if sorted_ops[i]['operation'] == 'create' and sorted_ops[i+1]['operation'] == 'drop':
                        issues.append({
                            'type': 'table_created_then_dropped',
                            'severity': 'medium',
                            'description': f"表 '{table}' 在迁移 {sorted_ops[i]['migration']} 中创建，随后在迁移 {sorted_ops[i+1]['migration']} 中删除",
                            'migrations': [sorted_ops[i]['migration'], sorted_ops[i+1]['migration']]
                        })
            except Exception as e:
                print(f"无法分析表 {table} 的操作: {e}")
    
    return issues

def analyze_migrations():
    """分析所有迁移文件并生成报告"""
    print("开始分析迁移文件...")
    
    # 确保迁移目录存在
    if not os.path.exists(MIGRATIONS_DIR):
        print(f"错误: 迁移目录 '{MIGRATIONS_DIR}' 不存在")
        return
    
    # 获取所有迁移文件
    migration_files = []
    for file in os.listdir(MIGRATIONS_DIR):
        if file.endswith('.py') and not file.startswith('__'):
            migration_files.append(os.path.join(MIGRATIONS_DIR, file))
    
    print(f"找到 {len(migration_files)} 个迁移文件")
    
    # 解析迁移文件
    migrations = []
    for file_path in migration_files:
        info = extract_migration_info(file_path)
        if info:
            migrations.append(info)
    
    # 按创建时间排序
    try:
        migrations.sort(key=lambda x: datetime.strptime(x['create_date'], '%Y-%m-%d %H:%M:%S') if x['create_date'] else datetime.min)
    except Exception as e:
        print(f"警告: 无法按日期排序迁移: {e}")
        # 尝试按文件名排序作为备选方案
        migrations.sort(key=lambda x: x['file_name'])
    
    # 构建迁移树
    tree = build_migration_tree(migrations)
    
    # 检查问题
    issues = check_for_issues(migrations, tree)
    
    # 生成报告
    report = []
    report.append("# 数据库迁移分析报告")
    report.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n## 概况")
    report.append(f"\n- 总迁移数量: {len(migrations)}")
    
    # 获取最早和最新的迁移
    if migrations:
        earliest = migrations[0]
        latest = migrations[-1]
        report.append(f"- 最早迁移: {earliest['file_name']} ({earliest['create_date']})")
        report.append(f"- 最新迁移: {latest['file_name']} ({latest['create_date']})")
    
    # 统计操作类型
    operation_counts = defaultdict(int)
    for m in migrations:
        for op_type, count in m['operations'].items():
            operation_counts[op_type] += count
    
    report.append("\n## 操作统计")
    for op_type, count in sorted(operation_counts.items(), key=lambda x: x[1], reverse=True):
        report.append(f"\n- {op_type}: {count}")
    
    # 报告问题
    if issues:
        report.append("\n## 检测到的问题")
        for issue in issues:
            severity_mark = {
                'high': '🔴',
                'medium': '🟠',
                'low': '🟡'
            }.get(issue['severity'], '⚪')
            
            report.append(f"\n### {severity_mark} {issue['type']}")
            report.append(f"\n{issue['description']}")
            report.append(f"\n相关迁移: {', '.join(issue['migrations'])}")
    else:
        report.append("\n## 检测到的问题\n\n未发现问题，迁移链完整。")
    
    # 迁移列表
    report.append("\n## 迁移列表")
    for m in migrations:
        report.append(f"\n### {m['file_name']}")
        report.append(f"\n- 修订号: {m['revision']}")
        report.append(f"- 依赖修订: {m['down_revision'] or 'None (根节点)'}")
        report.append(f"- 创建时间: {m['create_date']}")
        
        # 添加操作摘要
        active_ops = {k: v for k, v in m['operations'].items() if v > 0}
        if active_ops:
            report.append(f"- 操作: {', '.join([f'{k} ({v})' for k, v in active_ops.items()])}")
        else:
            report.append("- 操作: 无操作或无法解析")
        
        # 添加表操作
        if m['tables_created']:
            report.append(f"- 创建的表: {', '.join(m['tables_created'])}")
        if m['tables_dropped']:
            report.append(f"- 删除的表: {', '.join(m['tables_dropped'])}")
        
        # 添加注释/说明
        if m['comment']:
            comment_summary = m['comment']
            if len(comment_summary) > 100:
                comment_summary = comment_summary[:97] + "..."
            report.append(f"- 说明: {comment_summary}")
    
    # 保存报告
    report_dir = os.path.dirname(REPORT_FILE)
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"分析完成，报告已保存到 {REPORT_FILE}")
    
    return {
        'migrations': migrations,
        'issues': issues,
        'tree': tree
    }

def main():
    """主函数"""
    try:
        result = analyze_migrations()
        if result:
            issues_count = len(result['issues'])
            print(f"分析结果: 找到 {len(result['migrations'])} 个迁移文件，检测到 {issues_count} 个问题")
            
            if issues_count > 0:
                print("\n检测到的问题:")
                for issue in result['issues']:
                    print(f"- {issue['description']}")
    except Exception as e:
        print(f"执行分析时出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 