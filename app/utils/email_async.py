import threading
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def send_async_email(app, recipient, subject, content, html, email_function):
    """
    异步发送邮件的函数，运行在独立线程中
    
    Args:
        app: Flask应用实例（必须使用current_app._get_current_object()获取）
        recipient: 收件人邮箱
        subject: 邮件主题
        content: 纯文本内容
        html: HTML格式内容
        email_function: 邮件发送函数引用
    """
    with app.app_context():
        try:
            email_function(
                recipient=recipient,
                subject=subject,
                content=content,
                html=html
            )
            logger.info(f"异步邮件发送成功: {subject} 发送至 {recipient}")
        except Exception as e:
            logger.error(f"异步邮件发送失败: {str(e)}", exc_info=True) 