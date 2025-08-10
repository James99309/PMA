#!/bin/bash

# Supabase 图片存储桶迁移脚本
# 将 product-images 存储桶中的所有文件迁移到 invoice-images 存储桶

SUPABASE_URL="https://pqzviljbpfoqvyfulakl.supabase.co"
SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxenZpbGpicGZvcXZ5ZnVsYWtsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE4OTkzMywiZXhwIjoyMDY5NzY1OTMzfQ.GA3PLKQrERozFM923eEym5KAQvYCGwWCj57BQM5f4rY"

SOURCE_BUCKET="product-images"
DEST_BUCKET="invoice-images"

AUTH_HEADER="Authorization: Bearer $SERVICE_ROLE_KEY"
CONTENT_TYPE="Content-Type: application/json"

# 创建临时目录存储下载的文件
TEMP_DIR="/tmp/supabase_migration_$$"
mkdir -p "$TEMP_DIR"

echo "=========================================="
echo "Supabase 存储桶迁移工具"
echo "源存储桶: $SOURCE_BUCKET"
echo "目标存储桶: $DEST_BUCKET"
echo "临时目录: $TEMP_DIR"
echo "=========================================="

# 函数：获取目录中的所有文件
get_files_in_directory() {
    local bucket_name="$1"
    local prefix="$2"
    
    curl -s -X POST "$SUPABASE_URL/storage/v1/object/list/$bucket_name" \
        -H "$AUTH_HEADER" \
        -H "$CONTENT_TYPE" \
        -d "{\"limit\": 1000, \"offset\": 0, \"prefix\": \"$prefix\"}"
}

# 函数：下载文件
download_file() {
    local bucket_name="$1"
    local file_path="$2"
    local local_path="$3"
    
    curl -s -o "$local_path" "$SUPABASE_URL/storage/v1/object/$bucket_name/$file_path" \
        -H "$AUTH_HEADER"
}

# 函数：上传文件
upload_file() {
    local bucket_name="$1"
    local file_path="$2"
    local local_path="$3"
    
    curl -s -X POST "$SUPABASE_URL/storage/v1/object/$bucket_name/$file_path" \
        -H "$AUTH_HEADER" \
        -T "$local_path"
}

# 函数：递归处理目录
process_directory() {
    local prefix="$1"
    local level="$2"
    
    echo "正在处理目录: $prefix (级别 $level)"
    
    # 获取当前目录的内容
    local response=$(get_files_in_directory "$SOURCE_BUCKET" "$prefix")
    
    # 解析JSON响应（简单的方法，适用于基本结构）
    echo "$response" | grep -o '"name":"[^"]*"' | while read -r line; do
        local item_name=$(echo "$line" | cut -d'"' -f4)
        
        # 检查是否是文件（有ID）或目录
        local has_id=$(echo "$response" | grep -A 5 -B 5 "\"name\":\"$item_name\"" | grep '"id":')
        
        if [ -n "$has_id" ] && [ "$has_id" != '"id":null' ]; then
            # 这是一个文件
            local full_path="$prefix$item_name"
            local local_file="$TEMP_DIR/$(basename "$item_name")"
            
            echo "正在迁移文件: $full_path"
            
            # 下载文件
            if download_file "$SOURCE_BUCKET" "$full_path" "$local_file"; then
                # 上传文件到目标存储桶
                if upload_file "$DEST_BUCKET" "$full_path" "$local_file"; then
                    echo "✓ 成功迁移: $full_path"
                    ((SUCCESS_COUNT++))
                else
                    echo "✗ 上传失败: $full_path"
                    ((FAILED_COUNT++))
                fi
                
                # 删除本地临时文件
                rm -f "$local_file"
            else
                echo "✗ 下载失败: $full_path"
                ((FAILED_COUNT++))
            fi
        elif [ "$has_id" = '"id":null' ]; then
            # 这是一个目录，递归处理
            if [ $level -lt 10 ]; then  # 防止无限递归
                process_directory "$prefix$item_name/" $((level + 1))
            fi
        fi
    done
}

# 初始化计数器
SUCCESS_COUNT=0
FAILED_COUNT=0

# 开始迁移
echo "开始迁移..."

# 首先获取根级别的内容
root_response=$(get_files_in_directory "$SOURCE_BUCKET" "")
echo "根目录响应: $root_response"

# 处理根目录
process_directory "" 0

# 清理临时目录
rm -rf "$TEMP_DIR"

echo "=========================================="
echo "迁移完成!"
echo "成功: $SUCCESS_COUNT"
echo "失败: $FAILED_COUNT" 
echo "总计: $((SUCCESS_COUNT + FAILED_COUNT))"
echo "=========================================="