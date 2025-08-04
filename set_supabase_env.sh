#!/bin/bash
# 设置 Supabase 环境变量用于本地测试

echo "🔧 设置 Supabase 环境变量..."

export SUPABASE_URL="https://pqzviljbpfoqvyfulakl.supabase.co"
export SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxenZpbGpicGZvcXZ5ZnVsYWtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU5NzMsImV4cCI6MjA0MTU0OTczM30.kSqVh-mTkERrDWrnZx6kJgG3RzmwUW6oV6QN83ehNUM"
export SUPABASE_BUCKET="product-images"
export FORCE_CLOUD_UPLOAD="true"

echo "✅ 环境变量设置完成！"
echo "   SUPABASE_URL: $SUPABASE_URL"
echo "   SUPABASE_BUCKET: $SUPABASE_BUCKET"
echo "   FORCE_CLOUD_UPLOAD: $FORCE_CLOUD_UPLOAD"
echo ""
echo "现在可以运行: python run.py"