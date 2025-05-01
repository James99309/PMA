import zipfile
import os
import shutil

def extract_vba(file_path):
    try:
        # 创建临时目录
        temp_dir = "temp_vba"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # 解压xlsm文件
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 查找vbaProject.bin文件
        vba_path = os.path.join(temp_dir, 'xl', 'vbaProject.bin')
        if os.path.exists(vba_path):
            print(f"找到VBA项目文件: {vba_path}")
            # 复制到当前目录
            shutil.copy2(vba_path, 'vbaProject.bin')
            print("VBA项目文件已提取到当前目录")
        else:
            print("未找到VBA项目文件")
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"提取VBA代码时出错: {str(e)}")

# 提取销售报表模块的VBA代码
extract_vba("销售报表模块-v1.47.2.xlsm") 