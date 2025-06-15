#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复后验证脚本
验证关键业务数据的完整性和一致性
"""

import psycopg2
from urllib.parse import urlparse
from config import CLOUD_DB_URL
from datetime import datetime

class PostRecoveryVerification:
    def __init__(self):
        self.parsed_url = urlparse(CLOUD_DB_URL)
        self.verification_log = []
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.verification_log.append(log_entry)
    
    def verify_quotation_details_recovery(self):
        """验证报价单明细数据恢复情况"""
        self.log("🔍 验证报价单明细数据恢复...")
        
        try:
            conn = psycopg2.connect(
                host=self.parsed_url.hostname,
                port=self.parsed_url.port or 5432,
                database=self.parsed_url.path.strip('/'),
                user=self.parsed_url.username,
                password=self.parsed_url.password
            )
            
            with conn.cursor() as cursor:
                # 检查总记录数
                cursor.execute("SELECT COUNT(*) FROM quotation_details")
                total_count = cursor.fetchone()[0]
                
                # 检查最新记录时间
                cursor.execute("SELECT MAX(created_at) FROM quotation_details")
                latest_time = cursor.fetchone()[0]
                
                # 检查ID范围
                cursor.execute("SELECT MIN(id), MAX(id) FROM quotation_details")
                min_id, max_id = cursor.fetchone()
                
                # 检查关键字段完整性
                cursor.execute("""
                    SELECT COUNT(*) FROM quotation_details 
                    WHERE quotation_id IS NOT NULL 
                    AND product_mn IS NOT NULL 
                    AND quantity > 0
                """)
                valid_records = cursor.fetchone()[0]
                
                # 检查与报价单的关联
                cursor.execute("""
                    SELECT COUNT(DISTINCT qd.quotation_id) 
                    FROM quotation_details qd 
                    JOIN quotations q ON qd.quotation_id = q.id
                """)
                linked_quotations = cursor.fetchone()[0]
                
                self.log(f"   📊 总记录数: {total_count:,}")
                self.log(f"   📅 最新时间: {latest_time}")
                self.log(f"   🆔 ID范围: {min_id} - {max_id}")
                self.log(f"   ✅ 有效记录: {valid_records:,} ({valid_records/total_count*100:.1f}%)")
                self.log(f"   🔗 关联报价单: {linked_quotations}")
                
                # 验证合肥新桥机场项目数据
                cursor.execute("""
                    SELECT COUNT(*) FROM quotation_details qd
                    JOIN quotations q ON qd.quotation_id = q.id
                    JOIN projects p ON q.project_id = p.id
                    WHERE p.project_name LIKE '%合肥新桥机场%'
                """)
                hefei_records = cursor.fetchone()[0]
                
                if hefei_records > 0:
                    self.log(f"   🎯 合肥新桥机场项目明细: {hefei_records} 条记录")
                else:
                    self.log("   ⚠️ 未找到合肥新桥机场项目明细")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"❌ 报价单明细验证失败: {str(e)}")
            return False
    
    def verify_projects_recovery(self):
        """验证项目数据恢复情况"""
        self.log("🔍 验证项目数据恢复...")
        
        try:
            conn = psycopg2.connect(
                host=self.parsed_url.hostname,
                port=self.parsed_url.port or 5432,
                database=self.parsed_url.path.strip('/'),
                user=self.parsed_url.username,
                password=self.parsed_url.password
            )
            
            with conn.cursor() as cursor:
                # 检查总项目数
                cursor.execute("SELECT COUNT(*) FROM projects")
                total_projects = cursor.fetchone()[0]
                
                # 检查合肥新桥机场项目
                cursor.execute("""
                    SELECT id, project_name, created_at, updated_at 
                    FROM projects 
                    WHERE project_name LIKE '%合肥新桥机场%'
                """)
                hefei_project = cursor.fetchone()
                
                # 检查项目状态分布
                cursor.execute("""
                    SELECT current_stage, COUNT(*) 
                    FROM projects 
                    GROUP BY current_stage 
                    ORDER BY COUNT(*) DESC
                """)
                stage_distribution = cursor.fetchall()
                
                self.log(f"   📊 总项目数: {total_projects}")
                
                if hefei_project:
                    self.log(f"   ✅ 合肥新桥机场项目已恢复:")
                    self.log(f"      - ID: {hefei_project[0]}")
                    self.log(f"      - 名称: {hefei_project[1]}")
                    self.log(f"      - 创建时间: {hefei_project[2]}")
                    self.log(f"      - 更新时间: {hefei_project[3]}")
                else:
                    self.log("   ❌ 合肥新桥机场项目未找到")
                
                self.log("   📈 项目状态分布:")
                for stage, count in stage_distribution[:5]:
                    self.log(f"      - {stage}: {count} 个项目")
            
            conn.close()
            return hefei_project is not None
            
        except Exception as e:
            self.log(f"❌ 项目数据验证失败: {str(e)}")
            return False
    
    def verify_quotations_recovery(self):
        """验证报价单数据恢复情况"""
        self.log("🔍 验证报价单数据恢复...")
        
        try:
            conn = psycopg2.connect(
                host=self.parsed_url.hostname,
                port=self.parsed_url.port or 5432,
                database=self.parsed_url.path.strip('/'),
                user=self.parsed_url.username,
                password=self.parsed_url.password
            )
            
            with conn.cursor() as cursor:
                # 检查总报价单数
                cursor.execute("SELECT COUNT(*) FROM quotations")
                total_quotations = cursor.fetchone()[0]
                
                # 检查合肥新桥机场项目的报价单
                cursor.execute("""
                    SELECT q.id, q.quotation_number, q.amount, q.created_at
                    FROM quotations q
                    JOIN projects p ON q.project_id = p.id
                    WHERE p.project_name LIKE '%合肥新桥机场%'
                """)
                hefei_quotations = cursor.fetchall()
                
                # 检查报价单金额统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as count,
                        SUM(amount) as total_amount,
                        AVG(amount) as avg_amount,
                        MAX(amount) as max_amount
                    FROM quotations 
                    WHERE amount > 0
                """)
                amount_stats = cursor.fetchone()
                
                self.log(f"   📊 总报价单数: {total_quotations}")
                
                if hefei_quotations:
                    self.log(f"   ✅ 合肥新桥机场项目报价单: {len(hefei_quotations)} 个")
                    for quotation in hefei_quotations:
                        self.log(f"      - {quotation[1]}: ¥{quotation[2]:,.2f} ({quotation[3]})")
                else:
                    self.log("   ❌ 合肥新桥机场项目报价单未找到")
                
                if amount_stats:
                    self.log(f"   💰 金额统计:")
                    self.log(f"      - 有效报价单: {amount_stats[0]} 个")
                    self.log(f"      - 总金额: ¥{amount_stats[1]:,.2f}")
                    self.log(f"      - 平均金额: ¥{amount_stats[2]:,.2f}")
                    self.log(f"      - 最大金额: ¥{amount_stats[3]:,.2f}")
            
            conn.close()
            return len(hefei_quotations) > 0
            
        except Exception as e:
            self.log(f"❌ 报价单数据验证失败: {str(e)}")
            return False
    
    def verify_data_integrity(self):
        """验证数据完整性"""
        self.log("🔍 验证数据完整性...")
        
        try:
            conn = psycopg2.connect(
                host=self.parsed_url.hostname,
                port=self.parsed_url.port or 5432,
                database=self.parsed_url.path.strip('/'),
                user=self.parsed_url.username,
                password=self.parsed_url.password
            )
            
            integrity_issues = []
            
            with conn.cursor() as cursor:
                # 检查孤立的报价单明细
                cursor.execute("""
                    SELECT COUNT(*) FROM quotation_details qd
                    LEFT JOIN quotations q ON qd.quotation_id = q.id
                    WHERE q.id IS NULL
                """)
                orphaned_details = cursor.fetchone()[0]
                
                if orphaned_details > 0:
                    integrity_issues.append(f"孤立报价单明细: {orphaned_details} 条")
                
                # 检查孤立的报价单
                cursor.execute("""
                    SELECT COUNT(*) FROM quotations q
                    LEFT JOIN projects p ON q.project_id = p.id
                    WHERE p.id IS NULL
                """)
                orphaned_quotations = cursor.fetchone()[0]
                
                if orphaned_quotations > 0:
                    integrity_issues.append(f"孤立报价单: {orphaned_quotations} 个")
                
                # 检查产品引用完整性
                cursor.execute("""
                    SELECT COUNT(*) FROM quotation_details qd
                    LEFT JOIN products p ON qd.product_mn = p.product_mn
                    WHERE p.id IS NULL AND qd.product_mn IS NOT NULL
                """)
                missing_products = cursor.fetchone()[0]
                
                if missing_products > 0:
                    integrity_issues.append(f"缺失产品引用: {missing_products} 条")
                
                # 检查联系人引用完整性
                cursor.execute("""
                    SELECT COUNT(*) FROM quotations q
                    LEFT JOIN contacts c ON q.contact_id = c.id
                    WHERE c.id IS NULL AND q.contact_id IS NOT NULL
                """)
                missing_companies = cursor.fetchone()[0]
                
                if missing_companies > 0:
                    integrity_issues.append(f"缺失联系人引用: {missing_companies} 个报价单")
            
            if integrity_issues:
                self.log("   ⚠️ 发现数据完整性问题:")
                for issue in integrity_issues:
                    self.log(f"      - {issue}")
            else:
                self.log("   ✅ 数据完整性检查通过")
            
            conn.close()
            return len(integrity_issues) == 0
            
        except Exception as e:
            self.log(f"❌ 数据完整性验证失败: {str(e)}")
            return False
    
    def generate_verification_report(self, results):
        """生成验证报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"POST_RECOVERY_VERIFICATION_REPORT_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 恢复后验证报告\n\n")
            f.write(f"**验证时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 验证结果概要
            f.write("## 📊 验证结果概要\n\n")
            f.write("| 验证项目 | 状态 |\n")
            f.write("|----------|------|\n")
            
            for test_name, result in results.items():
                status = "✅ 通过" if result else "❌ 失败"
                f.write(f"| {test_name} | {status} |\n")
            
            # 总体评估
            passed_tests = sum(1 for result in results.values() if result)
            total_tests = len(results)
            success_rate = passed_tests / total_tests * 100
            
            f.write(f"\n**通过率**: {passed_tests}/{total_tests} ({success_rate:.1f}%)\n\n")
            
            if success_rate >= 80:
                f.write("✅ **恢复成功**: 关键数据已成功恢复，系统可以正常使用。\n\n")
            elif success_rate >= 60:
                f.write("⚠️ **部分成功**: 大部分数据已恢复，但存在一些问题需要关注。\n\n")
            else:
                f.write("❌ **恢复失败**: 存在严重问题，需要进一步处理。\n\n")
            
            # 验证日志
            f.write("## 📋 验证日志\n\n")
            f.write("```\n")
            for log_entry in self.verification_log:
                f.write(f"{log_entry}\n")
            f.write("```\n")
            
            # 建议
            f.write("\n## 💡 建议\n\n")
            f.write("### 立即措施\n")
            f.write("1. 测试关键业务功能（创建项目、生成报价单等）\n")
            f.write("2. 验证用户登录和权限系统\n")
            f.write("3. 检查数据导出功能\n\n")
            
            f.write("### 长期措施\n")
            f.write("1. 建立自动化备份系统\n")
            f.write("2. 实施数据监控告警\n")
            f.write("3. 制定灾难恢复计划\n")
            f.write("4. 考虑平台迁移到生产环境\n")
        
        self.log(f"📄 验证报告已生成: {report_file}")
        return report_file
    
    def run_verification(self):
        """执行完整的验证流程"""
        self.log("=" * 80)
        self.log("🚀 开始恢复后验证")
        self.log("=" * 80)
        
        results = {}
        
        # 执行各项验证
        results["报价单明细数据恢复"] = self.verify_quotation_details_recovery()
        results["项目数据恢复"] = self.verify_projects_recovery()
        results["报价单数据恢复"] = self.verify_quotations_recovery()
        results["数据完整性检查"] = self.verify_data_integrity()
        
        # 生成报告
        report_file = self.generate_verification_report(results)
        
        self.log("=" * 80)
        self.log("✅ 恢复后验证完成")
        self.log("=" * 80)
        
        return results

def main():
    """主函数"""
    verification = PostRecoveryVerification()
    results = verification.run_verification()
    
    # 显示结果摘要
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"\n📊 验证结果: {passed}/{total} 项通过")
    
    if passed == total:
        print("🎉 所有验证项目都通过了！")
    else:
        print("⚠️ 部分验证项目未通过，请查看详细报告。")

if __name__ == "__main__":
    main() 