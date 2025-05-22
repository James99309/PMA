#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
客户活跃度状态更新脚本

使用方法:
python scripts/update_customer_activity.py [--days=1] [--company-id=123]

参数说明:
--days: 不活跃天数阈值，默认为1天
--company-id: 指定检查特定客户ID，默认为全部客户
"""

import sys
import os
import argparse
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 确保可以导入app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, 'customer_activity.log')
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)

# 添加控制台输出
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 配置根日志记录器
logger = logging.getLogger('')
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.addHandler(console)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='更新客户活跃度状态')
    parser.add_argument('--days', type=int, default=1,
                        help='不活跃天数阈值，默认为1天')
    parser.add_argument('--company-id', type=int,
                        help='指定检查特定客户ID，默认为全部客户')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 创建应用上下文
    from app import create_app
    app = create_app()
    
    with app.app_context():
        from app.utils.activity_tracker import check_company_activity
        from app.models.settings import SystemSettings
        
        start_time = datetime.now()
        
        # 如果命令行没有指定阈值，则使用系统设置中的值
        days_threshold = args.days
        if days_threshold is None:
            days_threshold = SystemSettings.get('customer_activity_threshold', 1)
            
        logger.info(f"开始更新客户活跃度状态，参数: days={days_threshold}, company_id={args.company_id}")
        
        try:
            updated_count, active_count, inactive_count = check_company_activity(
                company_id=args.company_id,
                days_threshold=days_threshold
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"客户活跃度更新完成 - 总时间: {duration:.2f}秒, "
                       f"活跃客户: {active_count}, 不活跃客户: {inactive_count}, 更新数量: {updated_count}")
        except Exception as e:
            logger.exception(f"更新客户活跃度时发生错误: {str(e)}")
            sys.exit(1)
    
    sys.exit(0)

if __name__ == '__main__':
    main() 