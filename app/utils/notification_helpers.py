from app.models.notification import EventRegistry, UserEventSubscription
from app.models.user import User
from flask import render_template, current_app
import logging
from app.utils.email import send_email
from app.utils.email_async import send_async_email
import threading

logger = logging.getLogger(__name__)

def trigger_event_notification(event_key, target_user_id, context=None):
    """
    触发一个事件通知，发送给所有订阅了该用户该事件的用户
    
    Args:
        event_key (str): 事件唯一标识
        target_user_id (int): 被订阅的用户ID
        context (dict, optional): 渲染通知所需的上下文数据
    
    Returns:
        bool: 是否成功触发通知
    """
    try:
        # 获取事件ID
        event = EventRegistry.query.filter_by(event_key=event_key, enabled=True).first()
        if not event:
            logger.warning(f"未找到事件: {event_key}")
            return False
        
        # 获取所有订阅了此事件的用户
        subscriptions = UserEventSubscription.query.filter_by(
            target_user_id=target_user_id,
            event_id=event.id,
            enabled=True
        ).all()
        
        if not subscriptions:
            logger.info(f"事件 {event_key} 没有被任何用户订阅")
            return True
        
        # 获取触发事件的用户
        target_user = User.query.get(target_user_id)
        if not target_user:
            logger.warning(f"未找到用户: {target_user_id}")
            return False
        
        # 准备上下文数据
        ctx = context or {}
        ctx.update({
            'event': event,
            'target_user': target_user,
        })
        
        # 发送通知给所有订阅者
        for sub in subscriptions:
            subscriber = User.query.get(sub.user_id)
            if not subscriber or not subscriber.email:
                continue
            
            try:
                # 根据事件类型选择不同的邮件模板
                template = f'emails/{event_key}.html'
                
                # 确保上下文中有recipient_name，如果传入的context中有占位符则替换，否则使用订阅者的姓名
                if 'recipient_name' in ctx and ctx['recipient_name'] == '{{recipient_name}}':
                    ctx['recipient_name'] = subscriber.real_name or subscriber.username
                elif 'recipient_name' not in ctx:
                    ctx['recipient_name'] = subscriber.real_name or subscriber.username
                
                try:
                    # 渲染模板生成HTML内容
                    html_content = render_template(template, **ctx)
                except Exception as render_error:
                    logger.error(f"渲染模板 {template} 失败: {str(render_error)}", exc_info=True)
                    # 如果渲染失败，使用简单的HTML内容
                    html_content = f"""
                    <html>
                    <body>
                        <h1>通知: {event.label_zh}</h1>
                        <p>尊敬的 {subscriber.real_name or subscriber.username}：</p>
                        <p>由于技术原因，无法显示完整通知。</p>
                        <p>请登录系统查看详情。</p>
                    </body>
                    </html>
                    """
                
                # 异步发送邮件通知
                threading.Thread(
                    target=send_async_email,
                    args=(
                        current_app._get_current_object(),
                        subscriber.email,
                        f"通知: {event.label_zh}",
                        "",  # 空文本内容
                        html_content,
                        send_email
                    )
                ).start()
                
                logger.info(f"已启动异步线程发送 {event_key} 事件通知给用户 {subscriber.id}")
            except Exception as e:
                logger.error(f"处理通知给用户 {subscriber.id} 失败: {str(e)}", exc_info=True)
        
        return True
    
    except Exception as e:
        logger.error(f"触发事件通知失败: {str(e)}", exc_info=True)
        return False 