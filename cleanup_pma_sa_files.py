#!/usr/bin/env python3
"""
清理PMA-SA项目中已迁移的PMA发票文件
从PMA-SA项目的invoice-images存储桶中删除已经成功迁移到PMA项目的文件
"""

import requests
import json
import sys
import time
from urllib.parse import urlparse

class PmaSaCleanupTool:
    def __init__(self):
        # PMA-SA项目配置
        self.pma_sa_url = "https://pqzviljbpfoqvyfulakl.supabase.co"
        self.pma_sa_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxenZpbGpicGZvcXZ5ZnVsYWtsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE4OTkzMywiZXhwIjoyMDY5NzY1OTMzfQ.GA3PLKQrERozFM923eEym5KAQvYCGwWCj57BQM5f4rY"
        self.pma_sa_bucket = "invoice-images"
        
        # HTTP请求头
        self.pma_sa_headers = {
            'Authorization': f'Bearer {self.pma_sa_key}',
            'Content-Type': 'application/json'
        }
        
        # 已迁移的文件路径列表 (从迁移脚本的输出中提取)
        self.migrated_files = [
            "expense_invoices/25/expense_invoice_25_d44050e6.png",
            "expense_invoices/26/expense_invoice_26_4f1117dc.png", 
            "expense_invoices/27/expense_invoice_27_b7608271.png",
            "expense_invoices/28/expense_invoice_28_4e5a4ed7.png",
            "expense_invoices/29/expense_invoice_29_5a4422bc.png",
            "expense_invoices/31/expense_invoice_31_891f6c26.png",
            "expense_invoices/32/expense_invoice_32_3d2d8814.png",
            "expense_invoices/33/expense_invoice_33_30199ed9.png",
            "expense_invoices/34/expense_invoice_34_e8604714.png",
            "expense_invoices/35/expense_invoice_35_1d8e638f.png",
            "expense_invoices/36/expense_invoice_36_6b0f0fb8.png",
            "expense_invoices/37/expense_invoice_37_fb523021.png",
            "expense_invoices/38/expense_invoice_38_5571c1fb.png"
        ]
    
    def list_files_in_bucket(self):
        """列出PMA-SA存储桶中的所有文件"""
        try:
            url = f"{self.pma_sa_url}/storage/v1/object/list/{self.pma_sa_bucket}"
            
            # 列出根目录
            response = requests.post(url, 
                                   json={"limit": 1000, "offset": 0, "sortBy": {"column": "name", "order": "asc"}},
                                   headers=self.pma_sa_headers)
            
            if response.status_code == 200:
                files = response.json()
                print(f"PMA-SA存储桶中共有 {len(files)} 个文件/目录:")
                
                for file_info in files[:20]:  # 只显示前20个
                    name = file_info.get('name', '')
                    size = file_info.get('metadata', {}).get('size', 0)
                    updated = file_info.get('updated_at', '')
                    print(f"  {name} ({size} bytes) - {updated}")
                
                if len(files) > 20:
                    print(f"  ... 还有 {len(files) - 20} 个文件")
                
                return files
            else:
                print(f"列出文件失败: HTTP {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"列出文件时发生错误: {e}")
            return []
    
    def list_expense_invoices_directory(self):
        """列出expense_invoices目录中的文件"""
        try:
            url = f"{self.pma_sa_url}/storage/v1/object/list/{self.pma_sa_bucket}"
            
            # 列出expense_invoices目录
            response = requests.post(url, 
                                   json={"limit": 1000, "offset": 0, "prefix": "expense_invoices/"},
                                   headers=self.pma_sa_headers)
            
            if response.status_code == 200:
                files = response.json()
                print(f"\nexpense_invoices目录中共有 {len(files)} 个文件:")
                
                # 按目录分组
                directories = {}
                for file_info in files:
                    name = file_info.get('name', '')
                    if '/' in name:
                        dir_name = '/'.join(name.split('/')[:-1])
                        if dir_name not in directories:
                            directories[dir_name] = []
                        directories[dir_name].append(file_info)
                
                # 统计需要清理和保留的文件数
                to_cleanup = 0
                to_keep = 0
                
                for dir_name, dir_files in sorted(directories.items()):
                    print(f"\n  📁 {dir_name}/ ({len(dir_files)} 文件)")
                    for file_info in dir_files:
                        name = file_info.get('name', '')
                        size = file_info.get('metadata', {}).get('size', 0)
                        filename = name.split('/')[-1]
                        if name in self.migrated_files:
                            status = "🔴 需要清理"
                            to_cleanup += 1
                        else:
                            status = "✅ 保留"
                            to_keep += 1
                        print(f"    {filename} ({size} bytes) - {status}")
                
                print(f"\n📊 统计: 需要清理 {to_cleanup} 个文件, 保留 {to_keep} 个文件")
                return files
            else:
                print(f"列出expense_invoices目录失败: HTTP {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"列出expense_invoices目录时发生错误: {e}")
            return []
    
    def delete_file_from_pma_sa(self, file_path: str) -> bool:
        """从PMA-SA项目删除文件"""
        try:
            url = f"{self.pma_sa_url}/storage/v1/object/{self.pma_sa_bucket}/{file_path}"
            
            # DELETE请求不需要Content-Type header
            headers = {
                'Authorization': f'Bearer {self.pma_sa_key}'
            }
            
            response = requests.delete(url, headers=headers)
            
            if response.status_code in [200, 204]:
                return True
            else:
                print(f"删除失败 {file_path}: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"删除文件失败 {file_path}: {e}")
            return False
    
    def cleanup_migrated_files(self, dry_run=True):
        """清理已迁移的文件"""
        print("=" * 60)
        if dry_run:
            print("🔍 清理预览模式 (不会实际删除文件)")
        else:
            print("🗑️  正在执行文件清理")
        print("=" * 60)
        
        success_count = 0
        failed_count = 0
        
        print(f"准备清理 {len(self.migrated_files)} 个已迁移的文件:")
        
        for i, file_path in enumerate(self.migrated_files, 1):
            print(f"\n[{i}/{len(self.migrated_files)}] {file_path}")
            
            if dry_run:
                print(f"  📋 预览: 将删除此文件")
                success_count += 1
            else:
                if self.delete_file_from_pma_sa(file_path):
                    print(f"  ✅ 删除成功")
                    success_count += 1
                else:
                    print(f"  ❌ 删除失败")
                    failed_count += 1
                
                # 添加延迟避免API限流
                time.sleep(0.2)
        
        print(f"\n" + "=" * 60)
        if dry_run:
            print(f"预览完成: 将清理 {success_count} 个文件")
        else:
            print(f"清理完成: 成功 {success_count}, 失败 {failed_count}")
            print(f"成功率: {(success_count/(success_count+failed_count))*100:.1f}%")
        print("=" * 60)
    
    def cleanup_empty_directories(self, dry_run=True):
        """清理空目录"""
        print(f"\n{'🔍 检查空目录' if dry_run else '🗂️  清理空目录'}")
        
        # 提取需要检查的目录列表
        directories_to_check = set()
        for file_path in self.migrated_files:
            if '/' in file_path:
                dir_path = '/'.join(file_path.split('/')[:-1])
                directories_to_check.add(dir_path)
        
        print(f"需要检查的目录: {len(directories_to_check)} 个")
        for dir_path in sorted(directories_to_check):
            print(f"  📁 {dir_path}/")
        
        if not dry_run:
            print("注意: 目录清理需要手动执行，因为Supabase Storage API不直接支持删除空目录")
        
    def run_cleanup(self, dry_run=True):
        """执行清理流程"""
        print("PMA-SA发票文件清理工具")
        print("=" * 60)
        
        # 1. 列出当前文件
        print("1. 检查当前文件结构...")
        self.list_expense_invoices_directory()
        
        # 2. 清理已迁移的文件
        print(f"\n2. {'预览' if dry_run else '执行'}文件清理...")
        self.cleanup_migrated_files(dry_run)
        
        # 3. 检查空目录
        print(f"\n3. 检查空目录...")
        self.cleanup_empty_directories(dry_run)


def main():
    cleanup_tool = PmaSaCleanupTool()
    
    # 默认先运行预览模式
    print("首次运行 - 预览模式")
    cleanup_tool.run_cleanup(dry_run=True)
    
    print("\n" + "="*80)
    print("如果要执行实际清理，请运行:")
    print("python3 cleanup_pma_sa_files.py --execute")
    
    # 检查是否有 --execute 参数
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        print("\n" + "="*80)
        print("⚠️  即将执行实际文件删除操作!")
        
        if len(sys.argv) > 2 and sys.argv[2] == '--force':
            print("🚀 强制执行模式")
            cleanup_tool.run_cleanup(dry_run=False)
        else:
            try:
                response = input("确认要删除PMA-SA中的已迁移文件吗? (输入 'YES' 确认): ")
                
                if response == 'YES':
                    print("\n开始执行文件清理...")
                    cleanup_tool.run_cleanup(dry_run=False)
                else:
                    print("操作已取消")
            except EOFError:
                print("\n输入被中断，操作取消")
    elif len(sys.argv) > 1 and sys.argv[1] == '--force-execute':
        print("\n" + "="*80)
        print("🚀 强制执行文件清理...")
        cleanup_tool.run_cleanup(dry_run=False)


if __name__ == "__main__":
    main()