#!/bin/bash

# 批量迁移Supabase存储桶文件脚本
# 从 product-images 迁移所有文件到 invoice-images

set -e  # 遇到错误立即停止

SUPABASE_URL="https://pqzviljbpfoqvyfulakl.supabase.co"
SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxenZpbGpicGZvcXZ5ZnVsYWtsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDE4OTkzMywiZXhwIjoyMDY5NzY1OTMzfQ.GA3PLKQrERozFM923eEym5KAQvYCGwWCj57BQM5f4rY"

SOURCE_BUCKET="product-images"
DEST_BUCKET="invoice-images"
TEMP_DIR="/tmp/supabase_migration_$$"

AUTH_HEADER="Authorization: Bearer $SERVICE_ROLE_KEY"

# 创建临时目录
mkdir -p "$TEMP_DIR"

echo "=========================================="
echo "Supabase 批量文件迁移开始"
echo "源存储桶: $SOURCE_BUCKET"  
echo "目标存储桶: $DEST_BUCKET"
echo "临时目录: $TEMP_DIR"
echo "=========================================="

# 计数器
SUCCESS_COUNT=0
FAILED_COUNT=0
TOTAL_COUNT=0

# 清理函数
cleanup() {
    echo "清理临时文件..."
    rm -rf "$TEMP_DIR"
}

# 设置退出时清理
trap cleanup EXIT

# 获取所有子目录
echo "正在获取expense_invoices目录列表..."
DIRECTORIES=$(curl -s -X POST "$SUPABASE_URL/storage/v1/object/list/$SOURCE_BUCKET" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{"limit": 1000, "offset": 0, "prefix": "expense_invoices/"}' | \
    jq -r '.[] | select(.id == null) | .name')

echo "找到 $(echo "$DIRECTORIES" | wc -l) 个子目录"

# 遍历每个子目录
for dir in $DIRECTORIES; do
    echo ""
    echo "处理目录: expense_invoices/$dir/"
    
    # 获取该目录下的所有文件
    FILES=$(curl -s -X POST "$SUPABASE_URL/storage/v1/object/list/$SOURCE_BUCKET" \
        -H "$AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d "{\"limit\": 1000, \"offset\": 0, \"prefix\": \"expense_invoices/$dir/\"}" | \
        jq -r '.[] | select(.id != null) | .name')
    
    if [ -z "$FILES" ]; then
        echo "  目录为空，跳过"
        continue
    fi
    
    # 处理每个文件
    for file in $FILES; do
        ((TOTAL_COUNT++))
        
        SOURCE_PATH="expense_invoices/$dir/$file"
        TEMP_FILE="$TEMP_DIR/$(basename "$file")"
        
        echo "  [$TOTAL_COUNT] 正在迁移: $SOURCE_PATH"
        
        # 下载文件
        if curl -s -o "$TEMP_FILE" "$SUPABASE_URL/storage/v1/object/$SOURCE_BUCKET/$SOURCE_PATH" \
            -H "$AUTH_HEADER"; then
            
            # 检查文件是否下载成功（非空）
            if [ -s "$TEMP_FILE" ]; then
                # 确定文件类型
                MIME_TYPE="application/octet-stream"
                file_lower=$(echo "$file" | tr '[:upper:]' '[:lower:]')
                case "$file_lower" in
                    *.png) MIME_TYPE="image/png" ;;
                    *.jpg|*.jpeg) MIME_TYPE="image/jpeg" ;;
                    *.gif) MIME_TYPE="image/gif" ;;
                    *.pdf) MIME_TYPE="application/pdf" ;;
                esac
                
                # 上传到目标存储桶
                UPLOAD_RESPONSE=$(curl -s -w "%{http_code}" -X POST \
                    "$SUPABASE_URL/storage/v1/object/$DEST_BUCKET/$SOURCE_PATH" \
                    -H "$AUTH_HEADER" \
                    -H "Content-Type: $MIME_TYPE" \
                    --data-binary "@$TEMP_FILE")
                
                HTTP_CODE="${UPLOAD_RESPONSE: -3}"
                
                if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
                    echo "    ✓ 成功"
                    ((SUCCESS_COUNT++))
                else
                    echo "    ✗ 上传失败 (HTTP: $HTTP_CODE)"
                    echo "    响应: ${UPLOAD_RESPONSE%???}"
                    ((FAILED_COUNT++))
                fi
            else
                echo "    ✗ 下载的文件为空"
                ((FAILED_COUNT++))
            fi
            
            # 删除临时文件
            rm -f "$TEMP_FILE"
        else
            echo "    ✗ 下载失败"
            ((FAILED_COUNT++))
        fi
        
        # 添加小延迟避免API限制
        sleep 0.2
    done
done

echo ""
echo "=========================================="
echo "迁移完成!"
echo "总文件数: $TOTAL_COUNT"
echo "成功: $SUCCESS_COUNT"
echo "失败: $FAILED_COUNT"
echo "成功率: $(echo "scale=2; $SUCCESS_COUNT*100/$TOTAL_COUNT" | bc)%"
echo "=========================================="

# 验证迁移结果
if [ $FAILED_COUNT -eq 0 ]; then
    echo ""
    echo "正在验证迁移结果..."
    
    DEST_FILE_COUNT=$(curl -s -X POST "$SUPABASE_URL/storage/v1/object/list/$DEST_BUCKET" \
        -H "$AUTH_HEADER" \
        -H "Content-Type: application/json" \
        -d '{"limit": 10000, "offset": 0, "prefix": "expense_invoices/"}' | \
        jq '[.[] | select(.id != null)] | length')
    
    echo "目标存储桶中的文件数: $DEST_FILE_COUNT"
    echo "源文件数: $SUCCESS_COUNT"
    
    if [ "$DEST_FILE_COUNT" -eq "$SUCCESS_COUNT" ]; then
        echo "✓ 验证通过：所有文件迁移成功！"
    else
        echo "⚠ 验证警告：目标文件数与成功迁移数不匹配"
    fi
fi