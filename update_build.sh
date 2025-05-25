#!/bin/bash
# 添加到build.sh以应用数据库结构
echo "应用本地数据库结构..."
python apply_schema_on_render.py
