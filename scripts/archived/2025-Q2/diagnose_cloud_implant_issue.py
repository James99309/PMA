#!/usr/bin/env python3
"""
云端数据库植入总额问题诊断脚本
1. 先备份云端数据库到本地
2. 诊断植入总额计算问题
3. 不对云端数据库做任何修改
"""

import os
import sys
import subprocess
from datetime import datetime
from sqlalchemy import create_engine, text
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 云端数据库连接信息
CLOUD_DB_URL = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"

def backup_cloud_database():
    """备份云端数据库到本地"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = "cloud_db_backups"
        
        # 创建备份目录
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        backup_file = os.path.join(backup_dir, f"cloud_implant_diagnosis_backup_{timestamp}.sql")
        
        logger.info("开始备份云端数据库...")
        logger.info(f"备份文件: {backup_file}")
        
        # 使用pg_dump备份数据库
        cmd = [
            "pg_dump",
            "--host=dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com",
            "--port=5432",
            "--username=pma_db_sp8d_user",
            "--dbname=pma_db_sp8d",
            "--no-password",
            "--verbose",
            "--clean",
            "--no-owner",
            "--no-privileges",
            "--file=" + backup_file
        ]
        
        # 设置密码环境变量
        env = os.environ.copy()
        env['PGPASSWORD'] = 'LXNGJmR6bFrNecoaWbdbdzPpltIAd40w'
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ 云端数据库备份成功: {backup_file}")
            
            # 检查备份文件大小
            if os.path.exists(backup_file):
                file_size = os.path.getsize(backup_file)
                logger.info(f"备份文件大小: {file_size:,} 字节")
                return backup_file
            else:
                logger.error("备份文件未创建")
                return None
        else:
            logger.error(f"备份失败: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"备份过程中出错: {e}")
        return None

def diagnose_cloud_implant_issues():
    """诊断云端数据库植入总额问题"""
    try:
        logger.info("=" * 80)
        logger.info("开始诊断云端数据库植入总额问题")
        logger.info("=" * 80)
        
        engine = create_engine(CLOUD_DB_URL)
        
        with engine.connect() as conn:
            # 1. 检查产品表结构
            logger.info("1. 检查产品表结构...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'products' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            has_vendor_field = False
            logger.info("产品表字段:")
            for col in columns:
                logger.info(f"  {col[0]} - {col[1]} - nullable: {col[2]} - default: {col[3]}")
                if col[0] == 'is_vendor_product':
                    has_vendor_field = True
            
            if not has_vendor_field:
                logger.error("❌ 问题发现: 产品表缺少 is_vendor_product 字段!")
                return "missing_vendor_field"
            else:
                logger.info("✅ 产品表包含 is_vendor_product 字段")
            
            # 2. 检查产品数据
            logger.info("\n2. 检查产品数据...")
            result = conn.execute(text("SELECT COUNT(*) FROM products"))
            total_products = result.scalar()
            logger.info(f"总产品数量: {total_products}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM products WHERE is_vendor_product = true"))
            vendor_products = result.scalar()
            logger.info(f"厂商产品数量: {vendor_products}")
            
            result = conn.execute(text("SELECT COUNT(*) FROM products WHERE brand = '和源通信'"))
            heyuan_products = result.scalar()
            logger.info(f"和源通信品牌产品数量: {heyuan_products}")
            
            if vendor_products == 0:
                logger.error("❌ 问题发现: 没有产品被标记为厂商产品!")
                return "no_vendor_products"
            
            # 3. 检查报价单明细表结构
            logger.info("\n3. 检查报价单明细表结构...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'quotation_details' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            has_implant_field = False
            for col in columns:
                if col[0] == 'implant_subtotal':
                    has_implant_field = True
                    logger.info(f"✅ 找到植入小计字段: {col[0]} - {col[1]}")
                    break
            
            if not has_implant_field:
                logger.error("❌ 问题发现: 报价单明细表缺少 implant_subtotal 字段!")
                return "missing_implant_field"
            
            # 4. 检查报价单表结构
            logger.info("\n4. 检查报价单表结构...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'quotations' 
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            has_total_field = False
            for col in columns:
                if col[0] == 'implant_total_amount':
                    has_total_field = True
                    logger.info(f"✅ 找到植入总额字段: {col[0]} - {col[1]}")
                    break
            
            if not has_total_field:
                logger.error("❌ 问题发现: 报价单表缺少 implant_total_amount 字段!")
                return "missing_total_field"
            
            # 5. 检查最新报价单数据
            logger.info("\n5. 检查最新报价单数据...")
            result = conn.execute(text("""
                SELECT id, quotation_number, amount, implant_total_amount, currency, created_at
                FROM quotations 
                ORDER BY created_at DESC 
                LIMIT 10
            """))
            quotations = result.fetchall()
            
            zero_implant_count = 0
            logger.info("最新10个报价单:")
            for q in quotations:
                implant_amount = float(q[3]) if q[3] else 0.0
                if implant_amount == 0:
                    zero_implant_count += 1
                logger.info(f"  {q[1]}: 总额={q[2]}, 植入总额={implant_amount}, 货币={q[4]}")
            
            logger.info(f"植入总额为0的报价单数量: {zero_implant_count}/10")
            
            # 6. 检查报价单明细数据
            logger.info("\n6. 检查报价单明细数据...")
            result = conn.execute(text("""
                SELECT qd.id, qd.product_name, qd.brand, qd.product_mn, qd.market_price, 
                       qd.quantity, qd.implant_subtotal, qd.currency, q.quotation_number
                FROM quotation_details qd 
                JOIN quotations q ON qd.quotation_id = q.id 
                ORDER BY q.created_at DESC 
                LIMIT 10
            """))
            details = result.fetchall()
            
            zero_detail_count = 0
            logger.info("最新10个报价单明细:")
            for detail in details:
                implant_subtotal = float(detail[6]) if detail[6] else 0.0
                if implant_subtotal == 0 and detail[2] == '和源通信':
                    zero_detail_count += 1
                logger.info(f"  {detail[8]} - {detail[1]}: 品牌={detail[2]}, MN={detail[3]}, "
                           f"价格={detail[4]}, 数量={detail[5]}, 植入小计={implant_subtotal}")
            
            # 7. 检查产品MN匹配情况
            logger.info("\n7. 检查产品MN匹配情况...")
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM quotation_details qd
                WHERE qd.product_mn IS NOT NULL 
                AND qd.product_mn != ''
                AND NOT EXISTS (
                    SELECT 1 FROM products p 
                    WHERE p.product_mn = qd.product_mn
                )
            """))
            unmatched_mn_count = result.scalar()
            logger.info(f"报价单明细中无法匹配产品库的MN号数量: {unmatched_mn_count}")
            
            # 8. 检查应该有植入小计但为0的明细
            logger.info("\n8. 检查植入小计计算问题...")
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM quotation_details qd
                LEFT JOIN products p ON qd.product_mn = p.product_mn
                WHERE (
                    (p.is_vendor_product = true AND qd.market_price > 0 AND qd.quantity > 0)
                    OR (qd.brand = '和源通信' AND qd.market_price > 0 AND qd.quantity > 0)
                )
                AND (qd.implant_subtotal IS NULL OR qd.implant_subtotal = 0)
            """))
            problematic_details = result.scalar()
            logger.info(f"应该有植入小计但为0的明细数量: {problematic_details}")
            
            if problematic_details > 0:
                # 显示具体的问题明细
                result = conn.execute(text("""
                    SELECT qd.id, qd.product_name, qd.brand, qd.product_mn, 
                           qd.market_price, qd.quantity, qd.implant_subtotal,
                           p.is_vendor_product, q.quotation_number
                    FROM quotation_details qd
                    LEFT JOIN products p ON qd.product_mn = p.product_mn
                    JOIN quotations q ON qd.quotation_id = q.id
                    WHERE (
                        (p.is_vendor_product = true AND qd.market_price > 0 AND qd.quantity > 0)
                        OR (qd.brand = '和源通信' AND qd.market_price > 0 AND qd.quantity > 0)
                    )
                    AND (qd.implant_subtotal IS NULL OR qd.implant_subtotal = 0)
                    ORDER BY q.created_at DESC
                    LIMIT 5
                """))
                problem_details = result.fetchall()
                
                logger.info("问题明细示例:")
                for pd in problem_details:
                    logger.info(f"  {pd[8]} - {pd[1]}: MN={pd[3]}, 品牌={pd[2]}, "
                               f"价格={pd[4]}, 数量={pd[5]}, 植入小计={pd[6]}, "
                               f"产品库厂商标记={pd[7]}")
            
            # 9. 检查报价单植入总额与明细不匹配的情况
            logger.info("\n9. 检查报价单植入总额匹配情况...")
            result = conn.execute(text("""
                SELECT q.id, q.quotation_number, q.implant_total_amount, 
                       COALESCE(SUM(qd.implant_subtotal), 0) as calculated_total
                FROM quotations q
                LEFT JOIN quotation_details qd ON q.id = qd.quotation_id
                WHERE q.created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY q.id, q.quotation_number, q.implant_total_amount
                HAVING ABS(q.implant_total_amount - COALESCE(SUM(qd.implant_subtotal), 0)) > 0.01
                ORDER BY q.created_at DESC
                LIMIT 10
            """))
            mismatched_quotations = result.fetchall()
            
            logger.info(f"植入总额不匹配的报价单数量: {len(mismatched_quotations)}")
            for mq in mismatched_quotations:
                logger.info(f"  {mq[1]}: 数据库植入总额={mq[2]}, 计算植入总额={mq[3]}")
            
            # 10. 总结问题
            logger.info("\n" + "=" * 80)
            logger.info("诊断结果总结:")
            logger.info("=" * 80)
            
            issues_found = []
            
            if vendor_products == 0:
                issues_found.append("没有产品被标记为厂商产品")
            
            if problematic_details > 0:
                issues_found.append(f"有 {problematic_details} 个明细应该有植入小计但为0")
            
            if len(mismatched_quotations) > 0:
                issues_found.append(f"有 {len(mismatched_quotations)} 个报价单植入总额与明细不匹配")
            
            if unmatched_mn_count > 0:
                issues_found.append(f"有 {unmatched_mn_count} 个明细的MN号在产品库中找不到")
            
            if zero_implant_count >= 8:  # 10个中有8个或以上为0
                issues_found.append("大部分新报价单的植入总额为0")
            
            if issues_found:
                logger.error("❌ 发现的问题:")
                for i, issue in enumerate(issues_found, 1):
                    logger.error(f"  {i}. {issue}")
                return "multiple_issues"
            else:
                logger.info("✅ 未发现明显问题")
                return "no_issues"
                
    except Exception as e:
        logger.error(f"诊断过程中出错: {e}")
        return "diagnosis_error"

def main():
    """主函数"""
    logger.info("开始云端数据库植入总额问题诊断")
    
    # 1. 备份数据库
    backup_file = backup_cloud_database()
    if not backup_file:
        logger.error("❌ 数据库备份失败，终止诊断")
        return
    
    # 2. 诊断问题
    result = diagnose_cloud_implant_issues()
    
    # 3. 生成诊断报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"cloud_implant_diagnosis_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 云端数据库植入总额问题诊断报告\n\n")
        f.write(f"**诊断时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**备份文件**: {backup_file}\n")
        f.write(f"**诊断结果**: {result}\n\n")
        
        f.write("## 诊断说明\n\n")
        f.write("本次诊断检查了以下方面:\n")
        f.write("1. 产品表结构和数据\n")
        f.write("2. 报价单明细表结构和数据\n") 
        f.write("3. 报价单表结构和数据\n")
        f.write("4. 植入小计计算逻辑\n")
        f.write("5. 植入总额匹配情况\n\n")
        
        f.write("## 建议解决方案\n\n")
        if result == "missing_vendor_field":
            f.write("- 需要在产品表中添加 is_vendor_product 字段\n")
        elif result == "no_vendor_products":
            f.write("- 需要将和源通信品牌的产品标记为厂商产品\n")
        elif result == "multiple_issues":
            f.write("- 需要修复多个问题，详见日志输出\n")
        else:
            f.write("- 详见控制台日志输出\n")
    
    logger.info(f"诊断报告已保存: {report_file}")
    logger.info("诊断完成，未对云端数据库做任何修改")

if __name__ == "__main__":
    main() 