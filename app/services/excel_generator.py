#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel生成服务
用于生成报价单的Excel文档
"""

import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import logging

logger = logging.getLogger(__name__)

class ExcelGenerator:
    """Excel生成器"""
    
    def __init__(self):
        # 定义样式
        self.header_font = Font(name='微软雅黑', size=14, bold=True, color='FFFFFF')
        self.title_font = Font(name='微软雅黑', size=16, bold=True, color='0066CC')
        self.normal_font = Font(name='微软雅黑', size=11)
        self.bold_font = Font(name='微软雅黑', size=11, bold=True)
        
        self.center_alignment = Alignment(horizontal='center', vertical='center')
        self.left_alignment = Alignment(horizontal='left', vertical='center')
        self.right_alignment = Alignment(horizontal='right', vertical='center')
        
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        self.header_fill = PatternFill(start_color='0066CC', end_color='0066CC', fill_type='solid')
        self.light_fill = PatternFill(start_color='F8F9FA', end_color='F8F9FA', fill_type='solid')
    
    def generate_quotation_excel(self, quotation):
        """生成报价单Excel"""
        try:
            # 创建工作簿
            wb = Workbook()
            ws = wb.active
            ws.title = "报价单"
            
            # 设置列宽
            column_widths = {
                'A': 8,   # 序号
                'B': 25,  # 产品名称
                'C': 18,  # 型号
                'D': 30,  # 指标描述
                'E': 12,  # 品牌
                'F': 8,   # 单位
                'G': 8,   # 数量
                'H': 12,  # 单价
                'I': 12,  # 小计
                'J': 15   # MN
            }
            
            for col, width in column_widths.items():
                ws.column_dimensions[col].width = width
            
            current_row = 1
            
            # 公司信息头部
            ws.merge_cells(f'A{current_row}:E{current_row}')
            ws[f'A{current_row}'] = '和源通信（上海）股份有限公司'
            ws[f'A{current_row}'].font = self.title_font
            ws[f'A{current_row}'].alignment = self.left_alignment
            
            ws.merge_cells(f'F{current_row}:J{current_row}')
            ws[f'F{current_row}'] = '报价单'
            ws[f'F{current_row}'].font = Font(name='微软雅黑', size=18, bold=True, color='0066CC')
            ws[f'F{current_row}'].alignment = self.right_alignment
            
            current_row += 1
            
            # 公司地址信息
            company_info = [
                '武威路88号19楼6楼',
                '普陀区 上海市',
                '中国 (200335)',
                '021-62596028',
                'www.evertac.net'
            ]
            
            for info in company_info:
                ws.merge_cells(f'A{current_row}:E{current_row}')
                ws[f'A{current_row}'] = info
                ws[f'A{current_row}'].font = Font(name='微软雅黑', size=10, color='666666')
                ws[f'A{current_row}'].alignment = self.left_alignment
                current_row += 1
            
            current_row += 1  # 空行
            
            # 基本信息表格
            info_data = [
                ['项目名称', quotation.project.project_name if quotation.project else '-', 
                 '报价单编号', quotation.quotation_number],
                ['客户单位', quotation.project.end_user if quotation.project and quotation.project.end_user else '-', 
                 '货币类型', '人民币（CNY）'],
                ['报价日期', quotation.created_at.strftime('%Y年%m月%d日') if quotation.created_at else '-', 
                 '拥有者', quotation.owner.real_name or quotation.owner.username if quotation.owner else '-']
            ]
            
            for row_data in info_data:
                # 标签列
                ws[f'A{current_row}'] = row_data[0]
                ws[f'A{current_row}'].font = self.bold_font
                ws[f'A{current_row}'].fill = self.light_fill
                ws[f'A{current_row}'].border = self.thin_border
                ws[f'A{current_row}'].alignment = self.center_alignment
                
                # 值列
                ws.merge_cells(f'B{current_row}:C{current_row}')
                ws[f'B{current_row}'] = row_data[1]
                ws[f'B{current_row}'].font = self.normal_font
                ws[f'B{current_row}'].border = self.thin_border
                ws[f'B{current_row}'].alignment = self.left_alignment
                
                # 第二个标签列
                ws[f'D{current_row}'] = row_data[2]
                ws[f'D{current_row}'].font = self.bold_font
                ws[f'D{current_row}'].fill = self.light_fill
                ws[f'D{current_row}'].border = self.thin_border
                ws[f'D{current_row}'].alignment = self.center_alignment
                
                # 第二个值列
                ws.merge_cells(f'E{current_row}:J{current_row}')
                ws[f'E{current_row}'] = row_data[3]
                ws[f'E{current_row}'].font = self.normal_font
                ws[f'E{current_row}'].border = self.thin_border
                ws[f'E{current_row}'].alignment = self.left_alignment
                
                current_row += 1
            
            current_row += 1  # 空行
            
            # 产品明细标题
            ws.merge_cells(f'A{current_row}:J{current_row}')
            ws[f'A{current_row}'] = '产品明细'
            ws[f'A{current_row}'].font = Font(name='微软雅黑', size=14, bold=True, color='0066CC')
            ws[f'A{current_row}'].alignment = self.left_alignment
            current_row += 1
            
            # 产品明细表头
            headers = ['序号', '产品名称', '型号', '指标描述', '品牌', '单位', '数量', '单价', '小计', 'MN']
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=current_row, column=col_idx, value=header)
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.border = self.thin_border
                cell.alignment = self.center_alignment
            
            current_row += 1
            
            # 产品明细数据
            if quotation.details:
                for idx, detail in enumerate(quotation.details, 1):
                    row_data = [
                        idx,
                        detail.product_name or '-',
                        detail.product_model or '-',
                        detail.product_desc or '-',
                        detail.brand or '-',
                        detail.unit or '-',
                        detail.quantity or 0,
                        detail.unit_price or 0,
                        detail.total_price or 0,
                        detail.product_mn or '-'
                    ]
                    
                    for col_idx, value in enumerate(row_data, 1):
                        cell = ws.cell(row=current_row, column=col_idx, value=value)
                        cell.font = self.normal_font
                        cell.border = self.thin_border
                        
                        # 设置对齐方式
                        if col_idx == 1:  # 序号
                            cell.alignment = self.center_alignment
                        elif col_idx in [7, 8, 9]:  # 数量、单价、小计
                            cell.alignment = self.right_alignment
                            if col_idx in [8, 9]:  # 单价、小计格式化为货币
                                cell.number_format = '#,##0.00'
                        else:
                            cell.alignment = self.left_alignment
                    
                    current_row += 1
            else:
                # 无数据行
                ws.merge_cells(f'A{current_row}:J{current_row}')
                cell = ws[f'A{current_row}']
                cell.value = '暂无产品明细'
                cell.font = Font(name='微软雅黑', size=11, color='666666')
                cell.border = self.thin_border
                cell.alignment = self.center_alignment
                current_row += 1
            
            current_row += 1  # 空行
            
            # 总价
            ws.merge_cells(f'A{current_row}:I{current_row}')
            ws[f'A{current_row}'] = '总价'
            ws[f'A{current_row}'].font = Font(name='微软雅黑', size=14, bold=True)
            ws[f'A{current_row}'].alignment = self.right_alignment
            
            ws[f'J{current_row}'] = quotation.amount or 0
            ws[f'J{current_row}'].font = Font(name='微软雅黑', size=14, bold=True, color='0066CC')
            ws[f'J{current_row}'].alignment = self.right_alignment
            ws[f'J{current_row}'].number_format = '¥#,##0.00'
            
            current_row += 2  # 空行
            
            # 页脚信息
            ws.merge_cells(f'A{current_row}:J{current_row}')
            ws[f'A{current_row}'] = f'生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")} | 此报价单由系统自动生成'
            ws[f'A{current_row}'].font = Font(name='微软雅黑', size=9, color='666666')
            ws[f'A{current_row}'].alignment = self.center_alignment
            
            # 保存到内存
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"生成报价单Excel失败: {str(e)}")
            raise

# 创建全局实例
excel_generator = ExcelGenerator()

# 便捷函数
def generate_quotation_excel(quotation):
    """生成报价单Excel的便捷函数"""
    return excel_generator.generate_quotation_excel(quotation) 