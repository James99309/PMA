from flask import Flask
import logging
import sys
import json
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger('industry_debug')

def create_debug_app():
    app = Flask(__name__)
    app.config.from_object('config')
    
    from app import db
    db.init_app(app)
    
    return app

def debug_industry_stats():
    """调试行业统计数据生成过程"""
    app = create_debug_app()
    
    with app.app_context():
        from app.models.customerpm_statistics import CustomerStatistics, INDUSTRY_COLORS
        from app.utils.dictionary_helpers import INDUSTRY_LABELS
        from flask_login import current_user
        from app.models.user import User
        
        # 获取一个管理员用户作为测试
        admin_user = User.query.filter_by(role='admin').first()
        
        if not admin_user:
            logger.error("找不到管理员用户，无法继续测试")
            return
        
        logger.info(f"使用管理员用户 {admin_user.username} 进行测试")
        
        # 检查INDUSTRY_LABELS
        logger.info(f"行业标签定义: {json.dumps(INDUSTRY_LABELS, ensure_ascii=False)}")
        logger.info(f"行业颜色定义: {json.dumps(INDUSTRY_COLORS, ensure_ascii=False)}")
        
        # 获取统计数据
        logger.info("正在获取客户统计数据...")
        stats = CustomerStatistics.get_customer_statistics(user=admin_user)
        
        if not stats:
            logger.error("无法获取客户统计数据，返回为None")
            return
        
        logger.info(f"获取到统计数据: {json.dumps(stats, ensure_ascii=False, default=str)}")
        
        # 检查行业统计数据
        industry_stats = stats.get('industry_stats', [])
        logger.info(f"行业统计数据数量: {len(industry_stats)}")
        
        for i, stat in enumerate(industry_stats):
            logger.info(f"行业 {i+1}: {stat.get('industry')} - {stat.get('industry_name')} - 客户数: {stat.get('count')}")
        
        # 保存结果到文件
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"app/debug/industry_stats_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"结果已保存到 {filename}")

if __name__ == "__main__":
    logger.info("开始调试行业统计数据")
    debug_industry_stats()
    logger.info("调试结束") 