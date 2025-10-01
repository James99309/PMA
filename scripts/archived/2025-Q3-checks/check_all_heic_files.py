#!/usr/bin/env python3
"""
检查所有HEIC文件，统计真实格式分布
"""
import os
from supabase import create_client, Client
import requests
from collections import defaultdict

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

    # HEIC/HEIF: 通常以 ftyp 开始
    if len(content) > 11:
        if content[4:8] == b'ftyp':
            ftyp = content[8:12]
            if ftyp in [b'heic', b'heix', b'hevc', b'hevx', b'heim', b'heis', b'hevm', b'hevs', b'mif1', b'msf1']:
                return "HEIC/HEIF"

    return f"Unknown ({content[:8].hex()})"

def main():
    print("🔍 全面检查Supabase存储桶中的HEIC文件")
    print("=" * 60)

    try:
        # 创建Supabase客户端
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # 递归搜索所有子目录
        heic_files = []

        def search_directory(path=''):
            nonlocal heic_files
            try:
                items = supabase.storage.from_('invoice-images').list(path=path, options={'limit': 1000})
                for item in items:
                    if 'name' in item:
                        full_path = f"{path}/{item['name']}" if path else item['name']
                        if item.get('id'):  # 这是文件
                            if item['name'].lower().endswith('.heic'):
                                heic_files.append({
                                    'path': full_path,
                                    'name': item['name'],
                                    'size': item.get('metadata', {}).get('size', 0)
                                })
                        else:  # 这是目录
                            search_directory(full_path)
            except Exception as e:
                pass

        search_directory()

        print(f"\n📊 找到 {len(heic_files)} 个HEIC文件，正在检查所有文件...")

        # 统计结果
        format_stats = defaultdict(list)
        error_count = 0

        for i, file_info in enumerate(heic_files, 1):
            try:
                # 获取文件URL
                file_url = supabase.storage.from_('invoice-images').get_public_url(file_info['path'])

                # 下载文件头
                response = requests.get(file_url, headers={'Range': 'bytes=0-1024'}, timeout=5)
                if response.status_code in [200, 206]:
                    content = response.content
                    real_format = get_file_magic_bytes(content)
                    format_stats[real_format].append(file_info['name'])

                    # 打印进度
                    if i % 5 == 0:
                        print(f"  已检查 {i}/{len(heic_files)} 个文件...")
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1

        # 显示统计结果
        print("\n" + "=" * 60)
        print("📊 格式分析结果:")
        print("-" * 60)

        total_checked = sum(len(files) for files in format_stats.values())

        for format_type, files in sorted(format_stats.items()):
            percentage = (len(files) / total_checked * 100) if total_checked > 0 else 0
            print(f"\n{format_type}: {len(files)} 个文件 ({percentage:.1f}%)")

            if format_type != "HEIC/HEIF":
                print("  ⚠️ 这些文件扩展名错误（不是真正的HEIC格式）:")
                for filename in files[:5]:  # 显示前5个
                    print(f"    - {filename}")
                if len(files) > 5:
                    print(f"    ... 还有 {len(files) - 5} 个文件")

        if error_count > 0:
            print(f"\n❌ {error_count} 个文件检查失败")

        # 总结
        print("\n" + "=" * 60)
        print("📋 总结:")
        print(f"- 总共检查: {len(heic_files)} 个.heic文件")
        print(f"- 成功分析: {total_checked} 个文件")

        if "HEIC/HEIF" in format_stats:
            print(f"- 真正的HEIC格式: {len(format_stats['HEIC/HEIF'])} 个")

        wrong_format_count = total_checked - len(format_stats.get("HEIC/HEIF", []))
        if wrong_format_count > 0:
            print(f"- 🔴 扩展名错误的文件: {wrong_format_count} 个（需要修复）")

            if "JPEG" in format_stats:
                print(f"  - 实际是JPEG: {len(format_stats['JPEG'])} 个")
            if "PNG" in format_stats:
                print(f"  - 实际是PNG: {len(format_stats['PNG'])} 个")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()