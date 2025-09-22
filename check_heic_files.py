#!/usr/bin/env python3
"""
检查Supabase存储桶中HEIC文件的真实格式
"""
import os
from supabase import create_client, Client
import requests
from io import BytesIO
import struct

# 加载环境变量
from dotenv import load_dotenv
load_dotenv('.env.supabase.prod')

# Supabase配置
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_file_magic_bytes(content: bytes) -> str:
    """获取文件的魔术字节（文件头）来判断真实格式"""
    if len(content) < 12:
        return "Unknown"

    # JPEG: FF D8 FF
    if content[:3] == b'\xFF\xD8\xFF':
        return "JPEG"

    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if content[:8] == b'\x89PNG\r\n\x1a\n':
        return "PNG"

    # GIF: 47 49 46 38
    if content[:4] == b'GIF8':
        return "GIF"

    # WebP: 52 49 46 46 ... 57 45 42 50
    if content[:4] == b'RIFF' and len(content) > 11 and content[8:12] == b'WEBP':
        return "WebP"

    # PDF: 25 50 44 46
    if content[:4] == b'%PDF':
        return "PDF"

    # HEIC/HEIF: 通常以 ftyp 开始
    if len(content) > 11:
        # 检查是否是ISO基础媒体文件格式
        if content[4:8] == b'ftyp':
            ftyp = content[8:12]
            if ftyp in [b'heic', b'heix', b'hevc', b'hevx', b'heim', b'heis', b'hevm', b'hevs', b'mif1', b'msf1']:
                return "HEIC/HEIF"

    return f"Unknown ({content[:8].hex()})"

def main():
    print("🔍 检查Supabase存储桶中的HEIC文件")
    print("=" * 60)

    try:
        # 创建Supabase客户端
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # 列出invoice-images存储桶中的文件
        print("\n📂 查询invoice-images存储桶中的HEIC文件...")

        # 获取所有文件列表
        result = supabase.storage.from_('invoice-images').list(path='', options={'limit': 1000})

        heic_files = []
        total_files = 0

        # 递归搜索所有子目录
        def search_directory(path=''):
            nonlocal total_files, heic_files
            try:
                items = supabase.storage.from_('invoice-images').list(path=path, options={'limit': 1000})
                for item in items:
                    if 'name' in item:
                        full_path = f"{path}/{item['name']}" if path else item['name']
                        if item.get('id'):  # 这是文件
                            total_files += 1
                            if item['name'].lower().endswith('.heic'):
                                heic_files.append({
                                    'path': full_path,
                                    'name': item['name'],
                                    'size': item.get('metadata', {}).get('size', 0),
                                    'updated_at': item.get('updated_at', '')
                                })
                        else:  # 这是目录
                            search_directory(full_path)
            except Exception as e:
                print(f"  ⚠️ 搜索目录 {path} 时出错: {str(e)}")

        # 搜索根目录
        search_directory()

        print(f"\n📊 统计结果:")
        print(f"  总文件数: {total_files}")
        print(f"  HEIC文件数: {len(heic_files)}")

        if not heic_files:
            print("\n✅ 没有找到HEIC文件")
            return

        print(f"\n📋 找到 {len(heic_files)} 个HEIC文件，分析前5个:")
        print("-" * 60)

        # 分析前5个HEIC文件
        for i, file_info in enumerate(heic_files[:5], 1):
            print(f"\n{i}. 文件: {file_info['name']}")
            print(f"   路径: {file_info['path']}")
            print(f"   大小: {file_info['size']:,} bytes")

            try:
                # 获取文件的公共URL
                file_url = supabase.storage.from_('invoice-images').get_public_url(file_info['path'])
                print(f"   URL: {file_url[:50]}...")

                # 下载文件内容（只读取前1KB用于判断格式）
                response = requests.get(file_url, headers={'Range': 'bytes=0-1024'})
                if response.status_code in [200, 206]:
                    content = response.content
                    real_format = get_file_magic_bytes(content)
                    print(f"   🔍 真实格式: {real_format}")

                    if real_format == "JPEG":
                        print(f"   ⚠️ 这是JPEG文件但扩展名是.heic（后缀问题）")
                    elif real_format == "HEIC/HEIF":
                        print(f"   ✅ 这确实是HEIC格式文件（格式正确）")
                    else:
                        print(f"   ❓ 文件格式与扩展名不匹配")
                else:
                    print(f"   ❌ 无法下载文件: HTTP {response.status_code}")

            except Exception as e:
                print(f"   ❌ 分析失败: {str(e)}")

        # 统计分析结果
        print("\n" + "=" * 60)
        print("📊 分析总结:")
        print(f"- 检查了前 {min(5, len(heic_files))} 个HEIC文件")
        print(f"- 还有 {max(0, len(heic_files) - 5)} 个HEIC文件未分析")

        # 列出所有HEIC文件路径
        if len(heic_files) > 5:
            print(f"\n📄 其他HEIC文件列表:")
            for file_info in heic_files[5:15]:  # 只显示接下来的10个
                print(f"  - {file_info['path']}")
            if len(heic_files) > 15:
                print(f"  ... 还有 {len(heic_files) - 15} 个文件")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()