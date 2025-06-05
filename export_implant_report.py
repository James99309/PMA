#!/usr/bin/env python3
"""
植入小计统计报告导出脚本
生成详细的植入小计和植入总额合计统计报告，并导出为CSV文件
"""

import sys
import os
import csv
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.quotation import Quotation, QuotationDetail
from sqlalchemy import func, text

def export_implant_report():
    """导出植入小计统计报告"""
    app = create_app()
    
    with app.app_context():
        print("📊 开始生成植入小计统计报告")
        print("=" * 80)
        
        # 创建报告目录
        report_dir = "implant_reports"
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. 收集所有数据
        print("🔍 正在收集数据...")
        
        # 查询所有报价单及其植入信息
        quotations = Quotation.query.all()
        quotation_data = []
        
        total_implant_amount = 0.0
        total_quotation_amount = 0.0
        
        for quotation in quotations:
            # 计算该报价单的植入信息
            heyuan_products = []
            quotation_implant_total = 0.0
            total_products = len(quotation.details)
            heyuan_count = 0
            
            for detail in quotation.details:
                if detail.brand == '和源通信':
                    heyuan_count += 1
                    if detail.market_price and detail.quantity:
                        implant_subtotal = float(detail.market_price) * detail.quantity
                        quotation_implant_total += implant_subtotal
                        
                        heyuan_products.append({
                            'product_name': detail.product_name,
                            'product_model': detail.product_model,
                            'market_price': float(detail.market_price),
                            'quantity': detail.quantity,
                            'implant_subtotal': implant_subtotal
                        })
            
            quotation_amount = float(quotation.amount) if quotation.amount else 0.0
            implant_ratio = (quotation_implant_total / quotation_amount * 100) if quotation_amount > 0 else 0
            
            quotation_info = {
                'quotation_number': quotation.quotation_number,
                'project_name': quotation.project.project_name if quotation.project else '无项目',
                'project_id': quotation.project_id,
                'created_at': quotation.created_at.strftime('%Y-%m-%d') if quotation.created_at else '',
                'owner_name': quotation.owner.real_name if quotation.owner else '无',
                'total_products': total_products,
                'heyuan_products_count': heyuan_count,
                'heyuan_products': heyuan_products,
                'implant_total': quotation_implant_total,
                'quotation_total': quotation_amount,
                'implant_ratio': implant_ratio
            }
            
            quotation_data.append(quotation_info)
            total_implant_amount += quotation_implant_total
            total_quotation_amount += quotation_amount
        
        # 2. 导出报价单汇总CSV
        print("📄 正在生成报价单汇总CSV...")
        
        quotation_csv_file = os.path.join(report_dir, f"quotation_implant_summary_{timestamp}.csv")
        with open(quotation_csv_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = [
                '报价单编号', '项目名称', '项目ID', '创建日期', '负责人',
                '总产品数', '和源产品数', '植入金额', '报价总额', '植入占比(%)'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for data in sorted(quotation_data, key=lambda x: x['implant_total'], reverse=True):
                writer.writerow({
                    '报价单编号': data['quotation_number'],
                    '项目名称': data['project_name'],
                    '项目ID': data['project_id'],
                    '创建日期': data['created_at'],
                    '负责人': data['owner_name'],
                    '总产品数': data['total_products'],
                    '和源产品数': data['heyuan_products_count'],
                    '植入金额': f"{data['implant_total']:.2f}",
                    '报价总额': f"{data['quotation_total']:.2f}",
                    '植入占比(%)': f"{data['implant_ratio']:.1f}"
                })
        
        print(f"✅ 报价单汇总CSV已保存: {quotation_csv_file}")
        
        # 3. 导出产品明细CSV
        print("📄 正在生成产品明细CSV...")
        
        detail_csv_file = os.path.join(report_dir, f"product_detail_implant_{timestamp}.csv")
        with open(detail_csv_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = [
                '报价单编号', '项目名称', '产品名称', '产品型号', '品牌',
                '市场价', '数量', '植入小计'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for quotation_info in quotation_data:
                for product in quotation_info['heyuan_products']:
                    writer.writerow({
                        '报价单编号': quotation_info['quotation_number'],
                        '项目名称': quotation_info['project_name'],
                        '产品名称': product['product_name'],
                        '产品型号': product['product_model'],
                        '品牌': '和源通信',
                        '市场价': f"{product['market_price']:.2f}",
                        '数量': product['quantity'],
                        '植入小计': f"{product['implant_subtotal']:.2f}"
                    })
        
        print(f"✅ 产品明细CSV已保存: {detail_csv_file}")
        
        # 4. 生成详细统计报告
        print("📄 正在生成详细统计报告...")
        
        report_file = os.path.join(report_dir, f"implant_statistics_report_{timestamp}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("植入小计和植入总额合计统计报告\n")
            f.write("=" * 80 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # 总体统计
            f.write("📊 总体统计\n")
            f.write("-" * 50 + "\n")
            f.write(f"总报价单数量: {len(quotation_data):,}\n")
            f.write(f"包含和源产品的报价单数量: {sum(1 for q in quotation_data if q['implant_total'] > 0):,}\n")
            f.write(f"植入总额合计: ¥{total_implant_amount:,.2f}\n")
            f.write(f"报价总额合计: ¥{total_quotation_amount:,.2f}\n")
            f.write(f"植入金额占比: {(total_implant_amount/total_quotation_amount*100):.1f}%\n\n")
            
            # 产品明细统计
            total_details = QuotationDetail.query.count()
            heyuan_details_count = QuotationDetail.query.filter_by(brand='和源通信').count()
            
            f.write("📦 产品明细统计\n")
            f.write("-" * 50 + "\n")
            f.write(f"总产品明细数量: {total_details:,}\n")
            f.write(f"和源通信产品数量: {heyuan_details_count:,}\n")
            f.write(f"和源通信产品占比: {(heyuan_details_count/total_details*100):.1f}%\n\n")
            
            # 金额分布统计
            f.write("💰 植入金额分布统计\n")
            f.write("-" * 50 + "\n")
            
            ranges = [
                (0, 10000, "1万以下"),
                (10000, 50000, "1-5万"),
                (50000, 100000, "5-10万"),
                (100000, 500000, "10-50万"),
                (500000, 1000000, "50-100万"),
                (1000000, float('inf'), "100万以上")
            ]
            
            for min_amount, max_amount, label in ranges:
                filtered_quotations = [q for q in quotation_data 
                                     if min_amount <= q['implant_total'] < max_amount]
                count = len(filtered_quotations)
                total_amount = sum(q['implant_total'] for q in filtered_quotations)
                
                if count > 0:
                    f.write(f"{label:<10}: {count:>3}个报价单, 总金额: ¥{total_amount:>12,.0f}\n")
            
            f.write("\n")
            
            # 前20个植入金额最高的报价单
            f.write("🏆 植入金额最高的前20个报价单\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'序号':<4} {'报价单编号':<15} {'项目名称':<35} {'植入金额':<15} {'报价总额':<15} {'植入占比':<10}\n")
            f.write("-" * 100 + "\n")
            
            sorted_quotations = sorted(quotation_data, key=lambda x: x['implant_total'], reverse=True)
            for i, q in enumerate(sorted_quotations[:20], 1):
                project_name = q['project_name'][:33] + '...' if len(q['project_name']) > 35 else q['project_name']
                f.write(f"{i:<4} {q['quotation_number']:<15} {project_name:<35} "
                       f"¥{q['implant_total']:>12,.0f} ¥{q['quotation_total']:>12,.0f} {q['implant_ratio']:>8.1f}%\n")
            
            f.write("\n")
            
            # 按负责人统计
            f.write("👥 按负责人统计植入金额\n")
            f.write("-" * 50 + "\n")
            
            owner_stats = {}
            for q in quotation_data:
                owner = q['owner_name']
                if owner not in owner_stats:
                    owner_stats[owner] = {
                        'quotation_count': 0,
                        'implant_total': 0.0,
                        'quotation_total': 0.0
                    }
                owner_stats[owner]['quotation_count'] += 1
                owner_stats[owner]['implant_total'] += q['implant_total']
                owner_stats[owner]['quotation_total'] += q['quotation_total']
            
            sorted_owners = sorted(owner_stats.items(), key=lambda x: x[1]['implant_total'], reverse=True)
            f.write(f"{'负责人':<15} {'报价单数':<10} {'植入金额':<15} {'报价总额':<15} {'植入占比':<10}\n")
            f.write("-" * 70 + "\n")
            
            for owner, stats in sorted_owners[:15]:  # 显示前15名
                if stats['implant_total'] > 0:
                    ratio = (stats['implant_total'] / stats['quotation_total'] * 100) if stats['quotation_total'] > 0 else 0
                    f.write(f"{owner:<15} {stats['quotation_count']:<10} "
                           f"¥{stats['implant_total']:>12,.0f} ¥{stats['quotation_total']:>12,.0f} {ratio:>8.1f}%\n")
        
        print(f"✅ 详细统计报告已保存: {report_file}")
        
        # 5. 生成数据库验证报告
        print("🔍 正在验证数据库字段...")
        
        try:
            # 检查数据库字段一致性
            result = db.session.execute(text("""
                SELECT 
                    COUNT(*) as total_quotations,
                    COUNT(CASE WHEN implant_total_amount > 0 THEN 1 END) as with_implant_quotations,
                    SUM(COALESCE(implant_total_amount, 0)) as db_total_implant
                FROM quotations
            """))
            
            row = result.fetchone()
            db_total_quotations = row[0]
            db_with_implant_quotations = row[1]
            db_total_implant = float(row[2]) if row[2] else 0.0
            
            validation_file = os.path.join(report_dir, f"database_validation_{timestamp}.txt")
            with open(validation_file, 'w', encoding='utf-8') as f:
                f.write("数据库字段验证报告\n")
                f.write("=" * 50 + "\n")
                f.write(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("📊 数据库字段统计\n")
                f.write("-" * 30 + "\n")
                f.write(f"数据库中报价单总数: {db_total_quotations:,}\n")
                f.write(f"数据库中有植入金额的报价单数: {db_with_implant_quotations:,}\n")
                f.write(f"数据库中植入总额合计: ¥{db_total_implant:,.2f}\n\n")
                
                f.write("🔍 计算结果对比\n")
                f.write("-" * 30 + "\n")
                f.write(f"计算得出的植入总额: ¥{total_implant_amount:,.2f}\n")
                f.write(f"数据库字段植入总额: ¥{db_total_implant:,.2f}\n")
                
                difference = abs(total_implant_amount - db_total_implant)
                f.write(f"差异: ¥{difference:,.2f}\n")
                
                if difference < 0.01:
                    f.write("✅ 数据库字段与计算结果一致\n")
                else:
                    f.write("⚠️ 数据库字段需要更新\n")
            
            print(f"✅ 数据库验证报告已保存: {validation_file}")
            
        except Exception as e:
            print(f"❌ 数据库验证失败: {str(e)}")
        
        print(f"\n📁 所有报告文件已保存到目录: {report_dir}/")
        print("=" * 80)
        print("📊 报告生成完成！")
        
        # 显示文件列表
        print(f"\n生成的文件:")
        for file in os.listdir(report_dir):
            if timestamp in file:
                file_path = os.path.join(report_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  📄 {file} ({file_size:,} bytes)")

if __name__ == "__main__":
    export_implant_report() 