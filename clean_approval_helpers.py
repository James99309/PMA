#!/usr/bin/env python3
"""清理批价单V1审批系统的脚本"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
app = create_app()

def clean_v1_approval_references():
    """清理代码中的V1审批系统引用"""
    
    # 需要清理的文件列表
    files_to_clean = [
        'app/helpers/approval_helpers.py',
        'app/services/pricing_order_service.py',
        'app/routes/pricing_order_routes.py',
        'app/models/pricing_order.py'
    ]
    
    v1_patterns = [
        'PricingOrderApprovalRecord',
        'current_approval_step',
        'approval_flow_type'
    ]
    
    print("🧹 开始清理批价单V1审批系统引用")
    print("=" * 60)
    
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 统计V1引用
            v1_count = 0
            for pattern in v1_patterns:
                v1_count += content.count(pattern)
            
            if v1_count > 0:
                print(f"📄 {file_path}: 发现 {v1_count} 个V1引用")
            else:
                print(f"✅ {file_path}: 无V1引用")
    
    print("\n💡 建议:")
    print("1. 使用V2统一审批系统 (ApprovalInstance)")
    print("2. 移除 PricingOrderApprovalRecord 表")
    print("3. 清理批价单模型中的V1字段")
    print("4. 更新所有审批查询使用 get_step_actual_approver")

if __name__ == "__main__":
    clean_v1_approval_references()