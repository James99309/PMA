#!/usr/bin/env python3
"""
映射管理和检查工具
提供映射完整性检查、覆盖率分析、批量管理等功能
"""

import sys
import os
import json
import csv
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text
from app.utils.table_chinese_mapping import get_all_table_mappings, is_table_mapped
from app.utils.field_chinese_mapping import get_all_field_mappings, is_field_mapped
from app.utils.chinese_mapping_manager import mapping_manager

class MappingManagementTools:
    """映射管理工具类"""
    
    def __init__(self):
        self.app = create_app()
    
    def generate_comprehensive_report(self):
        """生成全面的映射分析报告"""
        with self.app.app_context():
            print("📊 生成全面映射分析报告")
            print("=" * 70)
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'table_analysis': self._analyze_table_mappings(),
                'field_analysis': self._analyze_field_mappings(),
                'coverage_stats': self._calculate_coverage_stats(),
                'quality_assessment': self._assess_mapping_quality(),
                'recommendations': self._generate_recommendations()
            }
            
            # 保存报告到文件
            report_file = f"mapping_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # 显示报告摘要
            self._display_report_summary(report)
            
            print(f"\n📄 详细报告已保存到: {report_file}")
            return report
    
    def check_mapping_integrity(self):
        """检查映射完整性"""
        with self.app.app_context():
            print("🔍 检查映射完整性")
            print("=" * 50)
            
            issues = []
            
            # 1. 检查孤立的字段配置
            orphaned_fields = self._find_orphaned_field_configs()
            if orphaned_fields:
                issues.append({
                    'type': 'orphaned_fields',
                    'severity': 'warning',
                    'count': len(orphaned_fields),
                    'description': '存在没有对应数据表的字段配置',
                    'items': orphaned_fields
                })
            
            # 2. 检查缺失的表配置
            missing_tables = self._find_missing_table_configs()
            if missing_tables:
                issues.append({
                    'type': 'missing_tables',
                    'severity': 'info',
                    'count': len(missing_tables),
                    'description': '存在但未配置的数据表',
                    'items': missing_tables
                })
            
            # 3. 检查英文字段映射
            english_fields = self._find_english_field_mappings()
            if english_fields:
                issues.append({
                    'type': 'english_fields',
                    'severity': 'low',
                    'count': len(english_fields),
                    'description': '仍为英文显示的字段',
                    'items': english_fields[:10]  # 只显示前10个
                })
            
            # 4. 检查重复映射
            duplicate_mappings = self._find_duplicate_mappings()
            if duplicate_mappings:
                issues.append({
                    'type': 'duplicate_mappings',
                    'severity': 'warning',
                    'count': len(duplicate_mappings),
                    'description': '可能存在重复的映射配置',
                    'items': duplicate_mappings
                })
            
            self._display_integrity_results(issues)
            return issues
    
    def export_mappings_to_csv(self):
        """导出映射配置到CSV文件"""
        with self.app.app_context():
            print("📤 导出映射配置到CSV")
            print("=" * 40)
            
            # 导出表映射
            table_csv = f"table_mappings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self._export_table_mappings_csv(table_csv)
            
            # 导出字段映射
            field_csv = f"field_mappings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self._export_field_mappings_csv(field_csv)
            
            print(f"✅ 表映射已导出到: {table_csv}")
            print(f"✅ 字段映射已导出到: {field_csv}")
            
            return table_csv, field_csv
    
    def batch_update_missing_mappings(self):
        """批量更新缺失的映射"""
        with self.app.app_context():
            print("🔧 批量更新缺失的映射")
            print("=" * 50)
            
            try:
                # 1. 更新缺失的表配置
                missing_tables = self._find_missing_table_configs()[:20]  # 限制批量数量
                table_count = self._batch_add_table_configs(missing_tables)
                
                # 2. 更新英文字段映射
                english_fields = self._find_english_field_mappings()[:50]  # 限制批量数量
                field_count = self._batch_update_field_mappings(english_fields)
                
                db.session.commit()
                
                print(f"✅ 成功添加 {table_count} 个表配置")
                print(f"✅ 成功更新 {field_count} 个字段映射")
                
                # 清除缓存
                mapping_manager.update_field_mapping_cache()
                print("✅ 已清除映射缓存")
                
                return table_count, field_count
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ 批量更新失败: {e}")
                return 0, 0
    
    def validate_mapping_consistency(self):
        """验证映射一致性"""
        with self.app.app_context():
            print("🔬 验证映射一致性")
            print("=" * 50)
            
            inconsistencies = []
            
            # 1. 检查语言一致性 - 确保中文映射质量
            try:
                query = text("""
                    SELECT dtc.table_name, dfc.field_name, dfc.display_name
                    FROM data_field_config dfc
                    JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
                    WHERE dtc.is_active = true
                    AND LENGTH(dfc.display_name) < 2
                """)
                result = db.session.execute(query)
                
                short_names = []
                for row in result:
                    short_names.append(f"{row.table_name}.{row.field_name}: '{row.display_name}'")
                
                if short_names:
                    inconsistencies.append(f"发现 {len(short_names)} 个过短的字段名")
                
            except Exception as e:
                inconsistencies.append(f"语言一致性检查失败: {e}")
            
            # 2. 检查重复映射
            try:
                query = text("""
                    SELECT dfc.display_name, COUNT(*) as count
                    FROM data_field_config dfc
                    JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
                    WHERE dtc.is_active = true
                    AND dfc.display_name ~ '[一-龟]'
                    GROUP BY dfc.display_name
                    HAVING COUNT(*) > 3
                """)
                result = db.session.execute(query)
                
                duplicates = []
                for row in result:
                    duplicates.append(f"'{row.display_name}' 出现 {row.count} 次")
                
                if duplicates:
                    inconsistencies.append(f"发现 {len(duplicates)} 个高频重复映射")
                
            except Exception as e:
                inconsistencies.append(f"重复映射检查失败: {e}")
            
            self._display_consistency_results(inconsistencies)
            return inconsistencies
    
    def _analyze_table_mappings(self):
        """分析表映射情况"""
        query = text("""
            SELECT 
                COUNT(*) as total_tables,
                COUNT(CASE WHEN dtc.table_name IS NOT NULL THEN 1 END) as configured_tables
            FROM (
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE '%_seq'
            ) all_tables
            LEFT JOIN data_table_config dtc ON all_tables.table_name = dtc.table_name
        """)
        
        result = db.session.execute(query).fetchone()
        
        return {
            'total_tables': result.total_tables,
            'configured_tables': result.configured_tables,
            'coverage_percentage': (result.configured_tables / result.total_tables * 100) if result.total_tables > 0 else 0
        }
    
    def _analyze_field_mappings(self):
        """分析字段映射情况"""
        query = text("""
            SELECT 
                COUNT(*) as total_fields,
                COUNT(CASE WHEN dfc.display_name ~ '[一-龟]' THEN 1 END) as chinese_fields,
                COUNT(CASE WHEN dfc.display_name !~ '[一-龟]' THEN 1 END) as english_fields
            FROM data_field_config dfc
            JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
            WHERE dtc.is_active = true
        """)
        
        result = db.session.execute(query).fetchone()
        
        return {
            'total_fields': result.total_fields,
            'chinese_fields': result.chinese_fields,
            'english_fields': result.english_fields,
            'chinese_percentage': (result.chinese_fields / result.total_fields * 100) if result.total_fields > 0 else 0
        }
    
    def _calculate_coverage_stats(self):
        """计算覆盖率统计"""
        table_mappings = get_all_table_mappings()
        field_mappings = get_all_field_mappings()
        
        # 获取数据库中实际的表数量
        tables_query = text("""
            SELECT COUNT(*) as count
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            AND table_name NOT LIKE '%_seq'
        """)
        total_db_tables = db.session.execute(tables_query).scalar()
        
        return {
            'code_mappings': {
                'tables': len(table_mappings),
                'fields': len(field_mappings)
            },
            'database_reality': {
                'total_tables': total_db_tables,
                'mapping_coverage': len([t for t in table_mappings.keys() if self._table_exists(t)]) / total_db_tables * 100
            }
        }
    
    def _assess_mapping_quality(self):
        """评估映射质量"""
        quality_scores = {
            'completeness': 0,  # 完整性
            'consistency': 0,   # 一致性
            'accuracy': 0,      # 准确性
            'maintainability': 0  # 可维护性
        }
        
        # 计算完整性分数
        table_analysis = self._analyze_table_mappings()
        field_analysis = self._analyze_field_mappings()
        
        quality_scores['completeness'] = (
            table_analysis['coverage_percentage'] * 0.3 +
            field_analysis['chinese_percentage'] * 0.7
        )
        
        # 计算一致性分数（基于英文字段比例）
        quality_scores['consistency'] = max(0, 100 - field_analysis['english_fields'] / field_analysis['total_fields'] * 100)
        
        # 计算准确性分数（基于中文字段质量）
        quality_scores['accuracy'] = min(100, field_analysis['chinese_percentage'] + 10)
        
        # 计算可维护性分数（基于配置化程度）
        quality_scores['maintainability'] = table_analysis['coverage_percentage']
        
        # 计算总分
        overall_score = sum(quality_scores.values()) / len(quality_scores)
        
        return {
            'scores': quality_scores,
            'overall_score': overall_score,
            'grade': self._get_quality_grade(overall_score)
        }
    
    def _generate_recommendations(self):
        """生成改进建议"""
        recommendations = []
        
        # 基于当前状态生成建议
        table_analysis = self._analyze_table_mappings()
        field_analysis = self._analyze_field_mappings()
        
        if table_analysis['coverage_percentage'] < 80:
            recommendations.append({
                'priority': 'high',
                'category': 'completeness',
                'title': '提升表配置覆盖率',
                'description': f"当前表配置覆盖率仅为 {table_analysis['coverage_percentage']:.1f}%，建议配置更多重要业务表"
            })
        
        if field_analysis['chinese_percentage'] < 80:
            recommendations.append({
                'priority': 'medium',
                'category': 'localization',
                'title': '继续中文化字段映射',
                'description': f"当前字段中文化率为 {field_analysis['chinese_percentage']:.1f}%，还有 {field_analysis['english_fields']} 个字段需要中文化"
            })
        
        if field_analysis['english_fields'] > 20:
            recommendations.append({
                'priority': 'low',
                'category': 'maintenance',
                'title': '批量处理英文字段',
                'description': "建议使用批量更新工具处理剩余的英文字段映射"
            })
        
        return recommendations
    
    def _find_orphaned_field_configs(self):
        """查找孤立的字段配置"""
        query = text("""
            SELECT dfc.field_name, dtc.table_name
            FROM data_field_config dfc
            JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
            WHERE dtc.table_name NOT IN (
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            )
        """)
        
        result = db.session.execute(query)
        return [{'field': row.field_name, 'table': row.table_name} for row in result]
    
    def _find_missing_table_configs(self):
        """查找缺失的表配置"""
        query = text("""
            SELECT t.table_name
            FROM information_schema.tables t
            LEFT JOIN data_table_config dtc ON t.table_name = dtc.table_name
            WHERE t.table_schema = 'public' 
            AND t.table_type = 'BASE TABLE'
            AND t.table_name NOT LIKE '%_seq'
            AND dtc.table_name IS NULL
        """)
        
        result = db.session.execute(query)
        return [row.table_name for row in result]
    
    def _find_english_field_mappings(self):
        """查找英文字段映射"""
        query = text("""
            SELECT dfc.field_name, dtc.table_name, dfc.display_name
            FROM data_field_config dfc
            JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
            WHERE dtc.is_active = true
            AND dfc.display_name !~ '[一-龟]'
            ORDER BY dtc.table_name, dfc.field_name
        """)
        
        result = db.session.execute(query)
        return [{'field': row.field_name, 'table': row.table_name, 'current_name': row.display_name} for row in result]
    
    def _find_duplicate_mappings(self):
        """查找重复映射"""
        # 这里可以实现检查重复映射的逻辑
        # 暂时返回空列表
        return []
    
    def _display_report_summary(self, report):
        """显示报告摘要"""
        print(f"\n📊 映射分析报告摘要")
        print(f"生成时间: {report['generated_at']}")
        print(f"\n表映射分析:")
        print(f"  总表数: {report['table_analysis']['total_tables']}")
        print(f"  已配置: {report['table_analysis']['configured_tables']}")
        print(f"  覆盖率: {report['table_analysis']['coverage_percentage']:.1f}%")
        
        print(f"\n字段映射分析:")
        print(f"  总字段数: {report['field_analysis']['total_fields']}")
        print(f"  中文字段: {report['field_analysis']['chinese_fields']}")
        print(f"  中文化率: {report['field_analysis']['chinese_percentage']:.1f}%")
        
        print(f"\n质量评分: {report['quality_assessment']['overall_score']:.1f}/100 ({report['quality_assessment']['grade']})")
        
        if report['recommendations']:
            print(f"\n💡 主要建议:")
            for rec in report['recommendations'][:3]:
                print(f"  • {rec['title']}: {rec['description']}")
    
    def _display_integrity_results(self, issues):
        """显示完整性检查结果"""
        if not issues:
            print("✅ 映射完整性检查通过，未发现问题")
            return
        
        print(f"发现 {len(issues)} 类问题:")
        for issue in issues:
            severity_icon = {"warning": "⚠️", "info": "ℹ️", "low": "🔸"}
            icon = severity_icon.get(issue['severity'], "❓")
            print(f"\n{icon} {issue['description']} ({issue['count']} 项)")
            
            # 显示前几个示例
            for item in issue['items'][:3]:
                if isinstance(item, dict):
                    print(f"    - {item}")
                else:
                    print(f"    - {item}")
    
    def _display_consistency_results(self, inconsistencies):
        """显示一致性检查结果"""
        if not inconsistencies:
            print("✅ 映射一致性检查通过")
        else:
            print(f"发现 {len(inconsistencies)} 个一致性问题")
            for issue in inconsistencies:
                print(f"  • {issue}")
    
    def _get_quality_grade(self, score):
        """获取质量等级"""
        if score >= 90:
            return "优秀 (A)"
        elif score >= 80:
            return "良好 (B)"
        elif score >= 70:
            return "中等 (C)"
        elif score >= 60:
            return "及格 (D)"
        else:
            return "不及格 (F)"
    
    def _table_exists(self, table_name):
        """检查表是否存在"""
        query = text("""
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = :table_name
        """)
        return db.session.execute(query, {'table_name': table_name}).fetchone() is not None
    
    def _export_table_mappings_csv(self, filename):
        """导出表映射到CSV"""
        query = text("""
            SELECT 
                COALESCE(dtc.table_name, t.table_name) as table_name,
                dtc.display_name,
                dtc.is_active,
                CASE WHEN dtc.table_name IS NULL THEN 'Missing Config' ELSE 'Configured' END as status
            FROM information_schema.tables t
            FULL OUTER JOIN data_table_config dtc ON t.table_name = dtc.table_name
            WHERE (t.table_schema = 'public' AND t.table_type = 'BASE TABLE' AND t.table_name NOT LIKE '%_seq')
            OR dtc.table_name IS NOT NULL
            ORDER BY table_name
        """)
        
        result = db.session.execute(query)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Table Name', 'Chinese Name', 'Is Active', 'Status'])
            
            for row in result:
                writer.writerow([row.table_name, row.display_name or '', row.is_active or False, row.status])
    
    def _export_field_mappings_csv(self, filename):
        """导出字段映射到CSV"""
        query = text("""
            SELECT 
                dtc.table_name,
                dfc.field_name,
                dfc.display_name,
                dfc.is_filterable,
                CASE WHEN dfc.display_name ~ '[一-龟]' THEN 'Chinese' ELSE 'English' END as language
            FROM data_field_config dfc
            JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
            WHERE dtc.is_active = true
            ORDER BY dtc.table_name, dfc.field_name
        """)
        
        result = db.session.execute(query)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Table Name', 'Field Name', 'Chinese Name', 'Is Filterable', 'Language'])
            
            for row in result:
                writer.writerow([row.table_name, row.field_name, row.display_name, row.is_filterable, row.language])

def main():
    """主函数"""
    tools = MappingManagementTools()
    
    print("🛠️ 映射管理工具")
    print("=" * 50)
    print("1. 生成全面分析报告")
    print("2. 检查映射完整性")
    print("3. 导出映射到CSV")
    print("4. 批量更新缺失映射")
    print("5. 验证映射一致性")
    print("6. 执行所有检查")
    
    choice = input("\n请选择功能 (1-6): ").strip()
    
    if choice == '1':
        tools.generate_comprehensive_report()
    elif choice == '2':
        tools.check_mapping_integrity()
    elif choice == '3':
        tools.export_mappings_to_csv()
    elif choice == '4':
        tools.batch_update_missing_mappings()
    elif choice == '5':
        tools.validate_mapping_consistency()
    elif choice == '6':
        print("\n🔄 执行所有检查...")
        tools.generate_comprehensive_report()
        tools.check_mapping_integrity()
        tools.validate_mapping_consistency()
        tools.export_mappings_to_csv()
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()