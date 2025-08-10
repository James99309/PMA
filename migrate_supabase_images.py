#!/usr/bin/env python3
"""
Supabase 图片存储桶迁移脚本
将 product-images 存储桶中的所有文件迁移到 invoice-images 存储桶
"""

import requests
import json
import sys
import time
from typing import List, Dict, Any

class SupabaseMigrator:
    def __init__(self, supabase_url: str, service_role_key: str):
        self.base_url = supabase_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {service_role_key}',
            'Content-Type': 'application/json'
        }
        
    def list_files_in_bucket(self, bucket_name: str, prefix: str = "") -> List[Dict[str, Any]]:
        """列出存储桶中的所有文件"""
        url = f"{self.base_url}/storage/v1/object/list/{bucket_name}"
        
        all_files = []
        offset = 0
        limit = 1000
        
        while True:
            payload = {
                "limit": limit,
                "offset": offset,
                "prefix": prefix
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                print(f"错误: 获取 {bucket_name} 中的文件列表失败")
                print(f"状态码: {response.status_code}")
                print(f"响应: {response.text}")
                return []
            
            files = response.json()
            
            if not files:
                break
                
            # 过滤掉目录，只保留文件
            actual_files = [f for f in files if f.get('id') is not None]
            all_files.extend(actual_files)
            
            if len(files) < limit:
                break
                
            offset += limit
        
        return all_files
    
    def get_all_files_recursively(self, bucket_name: str) -> List[Dict[str, Any]]:
        """递归获取所有文件，包括子目录中的文件"""
        print(f"正在获取 {bucket_name} 中的所有文件...")
        
        # 首先获取根目录的内容
        root_items = self.list_files_in_bucket(bucket_name, "")
        
        all_files = []
        directories_to_explore = []
        
        for item in root_items:
            if item.get('id') is None:  # 这是一个目录
                directories_to_explore.append(item['name'])
            else:  # 这是一个文件
                all_files.append(item)
        
        # 探索每个目录
        for directory in directories_to_explore:
            print(f"正在探索目录: {directory}")
            self._explore_directory_recursively(bucket_name, directory + "/", all_files)
        
        return all_files
    
    def _explore_directory_recursively(self, bucket_name: str, prefix: str, all_files: List[Dict[str, Any]]):
        """递归探索目录"""
        items = self.list_files_in_bucket(bucket_name, prefix)
        
        for item in items:
            if item.get('id') is None:  # 这是一个子目录
                subdir_prefix = prefix + item['name'] + "/"
                print(f"正在探索子目录: {subdir_prefix}")
                self._explore_directory_recursively(bucket_name, subdir_prefix, all_files)
            else:  # 这是一个文件
                # 构建完整的文件路径
                full_path = prefix + item['name']
                item['full_path'] = full_path
                all_files.append(item)
    
    def download_file(self, bucket_name: str, file_path: str) -> bytes:
        """从存储桶下载文件"""
        url = f"{self.base_url}/storage/v1/object/{bucket_name}/{file_path}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"下载文件失败: {file_path}, 状态码: {response.status_code}")
        
        return response.content
    
    def upload_file(self, bucket_name: str, file_path: str, file_content: bytes, content_type: str = None) -> bool:
        """上传文件到存储桶"""
        url = f"{self.base_url}/storage/v1/object/{bucket_name}/{file_path}"
        
        headers = self.headers.copy()
        if content_type:
            headers['Content-Type'] = content_type
        else:
            headers.pop('Content-Type', None)  # 让系统自动检测
        
        response = requests.post(url, headers=headers, data=file_content)
        
        if response.status_code not in [200, 201]:
            print(f"上传文件失败: {file_path}")
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return False
        
        return True
    
    def migrate_files(self, source_bucket: str, dest_bucket: str) -> Dict[str, int]:
        """迁移文件从源存储桶到目标存储桶"""
        print(f"开始迁移: {source_bucket} -> {dest_bucket}")
        
        # 获取所有文件
        source_files = self.get_all_files_recursively(source_bucket)
        
        if not source_files:
            print("没有找到需要迁移的文件")
            return {"success": 0, "failed": 0, "total": 0}
        
        print(f"找到 {len(source_files)} 个文件需要迁移")
        
        success_count = 0
        failed_count = 0
        
        for i, file_info in enumerate(source_files, 1):
            file_path = file_info.get('full_path') or file_info['name']
            print(f"[{i}/{len(source_files)}] 正在迁移: {file_path}")
            
            try:
                # 下载文件
                file_content = self.download_file(source_bucket, file_path)
                
                # 获取文件的MIME类型
                content_type = file_info.get('metadata', {}).get('mimetype')
                
                # 上传到目标存储桶
                if self.upload_file(dest_bucket, file_path, file_content, content_type):
                    print(f"✓ 成功迁移: {file_path}")
                    success_count += 1
                else:
                    print(f"✗ 迁移失败: {file_path}")
                    failed_count += 1
                
                # 添加短暂延迟避免API限流
                time.sleep(0.1)
                
            except Exception as e:
                print(f"✗ 迁移出错: {file_path} - {str(e)}")
                failed_count += 1
        
        return {
            "success": success_count,
            "failed": failed_count,
            "total": len(source_files)
        }
    
    def verify_migration(self, source_bucket: str, dest_bucket: str) -> bool:
        """验证迁移结果"""
        print("正在验证迁移结果...")
        
        source_files = self.get_all_files_recursively(source_bucket)
        dest_files = self.get_all_files_recursively(dest_bucket)
        
        # 构建文件路径集合用于比较
        source_paths = set()
        for f in source_files:
            path = f.get('full_path') or f['name']
            source_paths.add(path)
        
        dest_paths = set()
        for f in dest_files:
            path = f.get('full_path') or f['name']
            dest_paths.add(path)
        
        missing_files = source_paths - dest_paths
        
        if missing_files:
            print(f"警告: 以下 {len(missing_files)} 个文件未能成功迁移:")
            for file_path in sorted(missing_files):
                print(f"  - {file_path}")
            return False
        else:
            print("✓ 所有文件迁移成功!")
            return True


def main():
    # Supabase 配置
    SUPABASE_URL = "https://pqzviljbpfoqvyfulakl.supabase.co"
    SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxenZpbGpicGZvcXZ5ZnVsYWtsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE4OTkzMywiZXhwIjoyMDY5NzY1OTMzfQ.GA3PLKQrERozFM923eEym5KAQvYCGwWCj57BQM5f4rY"
    
    # 源和目标存储桶
    SOURCE_BUCKET = "product-images"
    DEST_BUCKET = "invoice-images"
    
    try:
        migrator = SupabaseMigrator(SUPABASE_URL, SERVICE_ROLE_KEY)
        
        print("="*50)
        print("Supabase 存储桶迁移工具")
        print(f"源存储桶: {SOURCE_BUCKET}")
        print(f"目标存储桶: {DEST_BUCKET}")
        print("="*50)
        
        # 执行迁移
        result = migrator.migrate_files(SOURCE_BUCKET, DEST_BUCKET)
        
        # 显示结果
        print("\n" + "="*50)
        print("迁移完成!")
        print(f"总文件数: {result['total']}")
        print(f"成功: {result['success']}")
        print(f"失败: {result['failed']}")
        print("="*50)
        
        # 验证迁移
        if result['failed'] == 0:
            migrator.verify_migration(SOURCE_BUCKET, DEST_BUCKET)
        
    except Exception as e:
        print(f"迁移过程中发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()