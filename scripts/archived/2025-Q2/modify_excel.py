import os
import shutil
from openpyxl import load_workbook
from openpyxl.vba import VBAProject

def modify_excel():
    # 备份原始文件
    shutil.copy2('销售报表模块-v1.47.2.xlsm', '销售报表模块-v1.47.2_backup.xlsm')
    
    # 加载Excel文件
    wb = load_workbook('销售报表模块-v1.47.2.xlsm', keep_vba=True)
    
    # 读取重构后的VBA代码
    with open('refactored_vba.bas', 'r', encoding='utf-8') as f:
        vba_code = f.read()
    
    # 创建新的VBA项目
    vba_project = VBAProject()
    
    # 添加模块
    vba_project.add_module('Module1', vba_code)
    
    # 替换原有的VBA项目
    wb.vba_project = vba_project
    
    # 保存修改后的文件
    wb.save('销售报表模块-v1.47.2_new.xlsm')
    
    print("Excel文件修改完成。新文件已保存为：销售报表模块-v1.47.2_new.xlsm")
    print("原始文件已备份为：销售报表模块-v1.47.2_backup.xlsm")

if __name__ == '__main__':
    modify_excel() 