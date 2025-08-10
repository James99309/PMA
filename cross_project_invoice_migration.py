#!/usr/bin/env python3
"""
跨项目发票迁移脚本
从PMA-SA项目迁移发票文件到PMA项目
"""

import requests
import json
import sys
import time
import psycopg2
from typing import List, Dict, Any
from urllib.parse import urlparse

class CrossProjectInvoiceMigrator:
    def __init__(self):
        # PMA-SA项目配置 (源)
        self.pma_sa_url = "https://pqzviljbpfoqvyfulakl.supabase.co"
        self.pma_sa_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxenZpbGpicGZvcXZ5ZnVsYWtsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE4OTkzMywiZXhwIjoyMDY5NzY1OTMzfQ.GA3PLKQrERozFM923eEym5KAQvYCGwWCj57BQM5f4rY"
        self.pma_sa_bucket = "invoice-images"
        
        # PMA项目配置 (目标)
        self.pma_url = "https://iqcyimnjtnmomvfuwjzw.supabase.co"
        self.pma_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlxY3lpbW5qdG5tb212ZnV3anp3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDc1Mjg5NiwiZXhwIjoyMDcwMzI4ODk2fQ.ivIwtz0Icp0eBibB4RAVh9iAULTHhCkKfPF9QOFnvfY"
        self.pma_bucket = "invoice-images"
        
        # 数据库连接配置
        self.pma_db_url = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        
        # HTTP请求头
        self.pma_sa_headers = {
            'Authorization': f'Bearer {self.pma_sa_key}',
            'Content-Type': 'application/json'
        }
        
        self.pma_headers = {
            'Authorization': f'Bearer {self.pma_key}',
            'Content-Type': 'application/json'
        }
    
    def get_database_connection(self):
        """获取PMA数据库连接"""
        try:
            conn = psycopg2.connect(self.pma_db_url)
            return conn
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return None
    
    def get_invoice_records_to_migrate(self) -> List[Dict]:
        """获取需要迁移的发票记录"""
        conn = self.get_database_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = """
            SELECT id, expense_id, description, invoice_images
            FROM expense_details 
            WHERE invoice_images LIKE %s
            ORDER BY id;
            """
            cursor.execute(query, ('%pqzviljbpfoqvyfulakl%',))
            
            records = []
            for row in cursor.fetchall():
                record_id, expense_id, description, invoice_images_json = row
                try:
                    invoice_images = json.loads(invoice_images_json) if invoice_images_json else []
                    records.append({
                        'id': record_id,
                        'expense_id': expense_id,
                        'description': description,
                        'invoice_images': invoice_images,
                        'original_json': invoice_images_json
                    })
                except json.JSONDecodeError:
                    print(f"警告: 记录 {record_id} 的invoice_images JSON解析失败")
                    continue
            
            cursor.close()
            conn.close()
            return records
            
        except Exception as e:
            print(f"查询数据库失败: {e}")
            conn.close()
            return []
    
    def download_file_from_pma_sa(self, file_path: str) -> bytes:
        """从PMA-SA项目下载文件"""
        url = f"{self.pma_sa_url}/storage/v1/object/{self.pma_sa_bucket}/{file_path}"
        
        try:
            response = requests.get(url, headers={'Authorization': f'Bearer {self.pma_sa_key}'})
            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"下载失败: HTTP {response.status_code} - {response.text}")
        except Exception as e:
            print(f"下载文件失败 {file_path}: {e}")
            raise
    
    def upload_file_to_pma(self, file_path: str, file_content: bytes) -> bool:
        """上传文件到PMA项目"""
        url = f"{self.pma_url}/storage/v1/object/{self.pma_bucket}/{file_path}"
        
        try:
            # 检测文件类型
            content_type = self.get_content_type(file_path)
            headers = {
                'Authorization': f'Bearer {self.pma_key}',
                'Content-Type': content_type,
                'x-upsert': 'true'  # 允许覆盖
            }
            
            response = requests.post(url, data=file_content, headers=headers)
            
            if response.status_code in [200, 201]:
                return True
            else:
                print(f"上传失败: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"上传文件失败 {file_path}: {e}")
            return False
    
    def get_content_type(self, filename: str) -> str:
        """根据文件扩展名获取Content-Type"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        content_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'heic': 'image/heic',
            'heif': 'image/heif',
            'pdf': 'application/pdf'
        }
        return content_types.get(ext, 'application/octet-stream')
    
    def extract_file_path_from_url(self, url: str) -> str:
        """从URL中提取文件路径"""
        # URL格式: https://domain/storage/v1/object/public/bucket/path/file
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            # 移除前面的路径部分: ['', 'storage', 'v1', 'object', 'public', 'bucket']
            if len(path_parts) > 6:
                return '/'.join(path_parts[6:])  # 从bucket之后的路径开始
            return None
        except Exception as e:
            print(f"解析URL失败 {url}: {e}")
            return None
    
    def migrate_single_record(self, record: Dict) -> Dict[str, Any]:
        """迁移单个记录的发票文件"""
        result = {
            'record_id': record['id'],
            'success': False,
            'migrated_files': [],
            'failed_files': [],
            'new_invoice_images': [],
            'error': None
        }
        
        try:
            for image_info in record['invoice_images']:
                original_url = image_info.get('url', '')
                filename = image_info.get('filename', '')
                file_size = image_info.get('size', 0)
                
                print(f"  正在处理文件: {filename}")
                
                # 提取文件路径
                file_path = self.extract_file_path_from_url(original_url)
                if not file_path:
                    result['failed_files'].append(f"无法解析URL: {original_url}")
                    continue
                
                try:
                    # 从PMA-SA下载文件
                    print(f"    从PMA-SA下载: {file_path}")
                    file_content = self.download_file_from_pma_sa(file_path)
                    
                    # 上传到PMA项目
                    print(f"    上传到PMA项目: {file_path}")
                    if self.upload_file_to_pma(file_path, file_content):
                        # 构建新的URL
                        new_url = f"{self.pma_url}/storage/v1/object/public/{self.pma_bucket}/{file_path}"
                        
                        # 创建新的图片信息
                        new_image_info = {
                            'filename': filename,
                            'url': new_url,
                            'size': file_size
                        }
                        result['new_invoice_images'].append(new_image_info)
                        result['migrated_files'].append(filename)
                        
                        print(f"    ✓ 成功迁移: {filename}")
                    else:
                        result['failed_files'].append(f"上传失败: {filename}")
                        
                except Exception as e:
                    error_msg = f"处理文件失败 {filename}: {str(e)}"
                    print(f"    ✗ {error_msg}")
                    result['failed_files'].append(error_msg)
                
                # 添加延迟避免API限流
                time.sleep(0.2)
            
            result['success'] = len(result['failed_files']) == 0
            
        except Exception as e:
            result['error'] = str(e)
            print(f"  记录处理失败: {e}")
        
        return result
    
    def update_database_url(self, record_id: int, new_invoice_images: List[Dict]) -> bool:
        """更新数据库中的发票URL"""
        conn = self.get_database_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            new_json = json.dumps(new_invoice_images)
            
            query = "UPDATE expense_details SET invoice_images = %s WHERE id = %s"
            cursor.execute(query, (new_json, record_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"更新数据库失败 记录{record_id}: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def run_migration(self):
        """执行完整的迁移流程"""
        print("=" * 60)
        print("跨项目发票迁移工具")
        print(f"源: PMA-SA项目 ({self.pma_sa_url})")
        print(f"目标: PMA项目 ({self.pma_url})")
        print("=" * 60)
        
        # 获取需要迁移的记录
        print("正在获取需要迁移的发票记录...")
        records = self.get_invoice_records_to_migrate()
        
        if not records:
            print("没有找到需要迁移的记录")
            return
        
        print(f"找到 {len(records)} 条记录需要迁移")
        
        # 统计信息
        total_records = len(records)
        success_records = 0
        failed_records = 0
        total_files = 0
        success_files = 0
        failed_files = 0
        
        # 逐条处理记录
        for i, record in enumerate(records, 1):
            print(f"\\n[{i}/{total_records}] 处理记录 ID: {record['id']} - {record['description'][:30]}...")
            
            # 迁移文件
            result = self.migrate_single_record(record)
            
            total_files += len(record['invoice_images'])
            success_files += len(result['migrated_files'])
            failed_files += len(result['failed_files'])
            
            if result['success'] and result['new_invoice_images']:
                # 更新数据库
                if self.update_database_url(record['id'], result['new_invoice_images']):
                    print(f"  ✓ 数据库更新成功")
                    success_records += 1
                else:
                    print(f"  ✗ 数据库更新失败")
                    failed_records += 1
            else:
                print(f"  ✗ 文件迁移失败")
                failed_records += 1
                for error in result['failed_files']:
                    print(f"    - {error}")
        
        # 输出最终统计
        print("\\n" + "=" * 60)
        print("迁移完成!")
        print(f"记录统计: 成功 {success_records}/{total_records}")
        print(f"文件统计: 成功 {success_files}/{total_files}")
        print(f"成功率: {(success_records/total_records)*100:.1f}%")
        print("=" * 60)
        
        # 验证迁移结果
        if success_records > 0:
            self.verify_migration()
    
    def verify_migration(self):
        """验证迁移结果"""
        print("\\n正在验证迁移结果...")
        
        conn = self.get_database_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # 检查是否还有指向PMA-SA的URL
            cursor.execute("""
                SELECT COUNT(*) 
                FROM expense_details 
                WHERE invoice_images LIKE %s
            """, ('%pqzviljbpfoqvyfulakl%',))
            
            remaining_old_urls = cursor.fetchone()[0]
            
            # 检查新的PMA项目URL数量
            cursor.execute("""
                SELECT COUNT(*) 
                FROM expense_details 
                WHERE invoice_images LIKE %s
            """, ('%iqcyimnjtnmomvfuwjzw%',))
            
            new_urls = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"验证结果:")
            print(f"  剩余旧URL (PMA-SA): {remaining_old_urls}")
            print(f"  新URL (PMA): {new_urls}")
            
            if remaining_old_urls == 0:
                print("  ✓ 所有URL已成功迁移!")
            else:
                print(f"  ⚠ 还有 {remaining_old_urls} 个URL需要处理")
                
        except Exception as e:
            print(f"验证失败: {e}")


def main():
    migrator = CrossProjectInvoiceMigrator()
    
    try:
        migrator.run_migration()
    except KeyboardInterrupt:
        print("\\n迁移被用户中断")
    except Exception as e:
        print(f"迁移过程发生错误: {e}")


if __name__ == "__main__":
    main()