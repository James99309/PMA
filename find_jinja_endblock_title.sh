#!/bin/bash
# 查找所有包含 `{% endblock title %}` 的模板文件，并打印到日志

SEARCH_DIR="./app/templates"
LOG_FILE="./endblock_title_found.log"

# 清空日志文件
> "$LOG_FILE"

# 查找并输出
find "$SEARCH_DIR" -type f -name "*.html" | while read -r file; do
    if grep -q '{% endblock title %}' "$file"; then
        echo "[发现] $file 包含 {% endblock title %}" | tee -a "$LOG_FILE"
    fi
done

echo "\n查找完毕，所有结果已写入 $LOG_FILE" 