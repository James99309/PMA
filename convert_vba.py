import os
import shutil
from pyvba import VBAProject

def convert_vba_to_bin():
    # 读取重构后的VBA代码
    with open('refactored_vba.bas', 'r', encoding='utf-8') as f:
        vba_code = f.read()
    
    # 创建VBA项目
    project = VBAProject()
    
    # 添加模块
    project.add_module('Module1', vba_code)
    
    # 保存为二进制文件
    project.save('excel_unpacked/xl/vbaProject.bin')
    
    # 重新打包Excel文件
    shutil.make_archive('销售报表模块-v1.47.2_new', 'zip', 'excel_unpacked')
    os.rename('销售报表模块-v1.47.2_new.zip', '销售报表模块-v1.47.2_new.xlsm')

if __name__ == '__main__':
    convert_vba_to_bin() 