#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新云端数据库中的植入数据
根据业务规则计算并更新报价单产品明细的植入小计和报价单的植入总额
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from config import CLOUD_DB_URL
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_connection():
    """验证云端数据库连接"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ 云端数据库连接成功")
            logger.info(f"PostgreSQL版本: {version}")
            return True
    except Exception as e:
        logger.error(f"✗ 云端数据库连接失败: {str(e)}")
        return False

def check_current_implant_data():
    """检查当前植入数据状态"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            # 检查产品明细中的植入小计
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_details,
                    COUNT(CASE WHEN brand = '和源通信' THEN 1 END) as heyuan_details,
                    COUNT(CASE WHEN implant_subtotal > 0 THEN 1 END) as details_with_implant,
                    SUM(implant_subtotal) as total_implant_subtotal
                FROM quotation_details
            """))
            detail_stats = result.fetchone()
            
            # 检查报价单中的植入总额
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_quotations,
                    COUNT(CASE WHEN implant_total_amount > 0 THEN 1 END) as quotations_with_implant,
                    SUM(implant_total_amount) as total_implant_amount
                FROM quotations
            """))
            quotation_stats = result.fetchone()
            
            logger.info("=" * 60)
            logger.info("当前植入数据状态:")
            logger.info("=" * 60)
            logger.info(f"产品明细总数: {detail_stats.total_details}")
            logger.info(f"和源通信产品明细: {detail_stats.heyuan_details}")
            logger.info(f"有植入小计的明细: {detail_stats.details_with_implant}")
            logger.info(f"植入小计总额: {detail_stats.total_implant_subtotal or 0:.2f}")
            logger.info("")
            logger.info(f"报价单总数: {quotation_stats.total_quotations}")
            logger.info(f"有植入总额的报价单: {quotation_stats.quotations_with_implant}")
            logger.info(f"植入总额合计: {quotation_stats.total_implant_amount or 0:.2f}")
            
            return detail_stats, quotation_stats
            
    except Exception as e:
        logger.error(f"检查当前数据状态失败: {str(e)}")
        return None, None

def update_implant_subtotal():
    """更新产品明细的植入小计"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            logger.info("开始更新产品明细的植入小计...")
            
            # 执行植入小计更新
            result = conn.execute(text("""
                UPDATE quotation_details 
                SET implant_subtotal = CASE 
                    WHEN brand = '和源通信' THEN COALESCE(market_price, 0) * COALESCE(quantity, 0)
                    ELSE 0.00
                END
            """))
            
            updated_rows = result.rowcount
            conn.commit()
            
            logger.info(f"✓ 产品明细植入小计更新完成，影响 {updated_rows} 行")
            return True
            
    except Exception as e:
        logger.error(f"更新产品明细植入小计失败: {str(e)}")
        return False

def update_implant_total_amount():
    """更新报价单的植入总额"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            logger.info("开始更新报价单的植入总额...")
            
            # 执行植入总额更新
            result = conn.execute(text("""
                UPDATE quotations 
                SET implant_total_amount = (
                    SELECT COALESCE(SUM(implant_subtotal), 0.00)
                    FROM quotation_details 
                    WHERE quotation_details.quotation_id = quotations.id
                )
            """))
            
            updated_rows = result.rowcount
            conn.commit()
            
            logger.info(f"✓ 报价单植入总额更新完成，影响 {updated_rows} 行")
            return True
            
    except Exception as e:
        logger.error(f"更新报价单植入总额失败: {str(e)}")
        return False

def validate_update_results():
    """验证更新结果"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            logger.info("验证更新结果...")
            
            # 检查和源通信产品的植入小计
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as heyuan_products,
                    SUM(market_price * quantity) as expected_subtotal,
                    SUM(implant_subtotal) as actual_subtotal
                FROM quotation_details 
                WHERE brand = '和源通信'
            """))
            heyuan_check = result.fetchone()
            
            # 检查非和源通信产品的植入小计
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as non_heyuan_products,
                    COUNT(CASE WHEN implant_subtotal = 0 THEN 1 END) as zero_implant_count
                FROM quotation_details 
                WHERE brand != '和源通信'
            """))
            non_heyuan_check = result.fetchone()
            
            # 检查报价单植入总额计算
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as quotations_checked,
                    COUNT(CASE WHEN q.implant_total_amount = detail_sum.total THEN 1 END) as correct_totals
                FROM quotations q
                LEFT JOIN (
                    SELECT 
                        quotation_id,
                        SUM(implant_subtotal) as total
                    FROM quotation_details
                    GROUP BY quotation_id
                ) detail_sum ON q.id = detail_sum.quotation_id
            """))
            total_check = result.fetchone()
            
            logger.info("=" * 60)
            logger.info("验证结果:")
            logger.info("=" * 60)
            logger.info(f"和源通信产品数量: {heyuan_check.heyuan_products}")
            logger.info(f"预期植入小计总额: {heyuan_check.expected_subtotal or 0:.2f}")
            logger.info(f"实际植入小计总额: {heyuan_check.actual_subtotal or 0:.2f}")
            
            if abs((heyuan_check.expected_subtotal or 0) - (heyuan_check.actual_subtotal or 0)) < 0.01:
                logger.info("✅ 和源通信产品植入小计计算正确")
            else:
                logger.warning("⚠️  和源通信产品植入小计计算可能有问题")
            
            logger.info(f"非和源通信产品数量: {non_heyuan_check.non_heyuan_products}")
            logger.info(f"植入小计为0的数量: {non_heyuan_check.zero_implant_count}")
            
            if non_heyuan_check.non_heyuan_products == non_heyuan_check.zero_implant_count:
                logger.info("✅ 非和源通信产品植入小计正确设为0")
            else:
                logger.warning("⚠️  部分非和源通信产品植入小计不为0")
            
            logger.info(f"检查的报价单数量: {total_check.quotations_checked}")
            logger.info(f"植入总额计算正确的报价单: {total_check.correct_totals}")
            
            if total_check.quotations_checked == total_check.correct_totals:
                logger.info("✅ 所有报价单植入总额计算正确")
            else:
                logger.warning(f"⚠️  {total_check.quotations_checked - total_check.correct_totals} 个报价单植入总额计算可能有问题")
            
            return True
            
    except Exception as e:
        logger.error(f"验证更新结果失败: {str(e)}")
        return False

def generate_summary_report():
    """生成最终统计报告"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            # 获取最终统计数据
            result = conn.execute(text("""
                SELECT 
                    '产品明细' as table_name,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN brand = '和源通信' THEN 1 END) as heyuan_records,
                    COUNT(CASE WHEN implant_subtotal > 0 THEN 1 END) as records_with_implant,
                    SUM(implant_subtotal) as total_implant_value
                FROM quotation_details
                UNION ALL
                SELECT 
                    '报价单' as table_name,
                    COUNT(*) as total_records,
                    0 as heyuan_records,
                    COUNT(CASE WHEN implant_total_amount > 0 THEN 1 END) as records_with_implant,
                    SUM(implant_total_amount) as total_implant_value
                FROM quotations
            """))
            
            stats = result.fetchall()
            
            logger.info("\n" + "=" * 60)
            logger.info("🎉 植入数据更新完成统计报告")
            logger.info("=" * 60)
            logger.info(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("")
            
            for stat in stats:
                logger.info(f"📊 {stat.table_name}:")
                logger.info(f"   总记录数: {stat.total_records}")
                if stat.heyuan_records > 0:
                    logger.info(f"   和源通信记录: {stat.heyuan_records}")
                logger.info(f"   有植入数据的记录: {stat.records_with_implant}")
                logger.info(f"   植入数据总额: {stat.total_implant_value or 0:.2f}")
                logger.info("")
            
            return True
            
    except Exception as e:
        logger.error(f"生成统计报告失败: {str(e)}")
        return False

def main():
    """主更新流程"""
    logger.info("=" * 60)
    logger.info("开始更新云端数据库植入数据")
    logger.info("=" * 60)
    
    # 步骤1: 验证连接
    logger.info("\n步骤1: 验证云端数据库连接")
    if not verify_connection():
        logger.error("数据库连接失败，更新中止")
        return False
    
    # 步骤2: 检查当前数据状态
    logger.info("\n步骤2: 检查当前数据状态")
    detail_stats, quotation_stats = check_current_implant_data()
    if detail_stats is None:
        logger.error("无法获取当前数据状态")
        return False
    
    # 步骤3: 更新产品明细植入小计
    logger.info("\n步骤3: 更新产品明细植入小计")
    if not update_implant_subtotal():
        logger.error("更新产品明细植入小计失败")
        return False
    
    # 步骤4: 更新报价单植入总额
    logger.info("\n步骤4: 更新报价单植入总额")
    if not update_implant_total_amount():
        logger.error("更新报价单植入总额失败")
        return False
    
    # 步骤5: 验证更新结果
    logger.info("\n步骤5: 验证更新结果")
    if not validate_update_results():
        logger.error("验证更新结果失败")
        return False
    
    # 步骤6: 生成统计报告
    logger.info("\n步骤6: 生成统计报告")
    if not generate_summary_report():
        logger.error("生成统计报告失败")
        return False
    
    logger.info("=" * 60)
    logger.info("🎉 云端植入数据更新完成!")
    logger.info("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            logger.info("植入数据更新成功完成")
            sys.exit(0)
        else:
            logger.error("植入数据更新失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n用户中断更新过程")
        sys.exit(1)
    except Exception as e:
        logger.error(f"更新过程发生异常: {str(e)}")
        sys.exit(1) 