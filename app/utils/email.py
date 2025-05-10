"""邮件发送工具模块"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.header import Header
from flask import current_app, request
from itsdangerous import URLSafeTimedSerializer

logger = logging.getLogger(__name__)

def send_email(subject, recipient, content, html=None):
    """发送邮件的通用函数"""
    # 从配置中获取邮件设置
    smtp_server = current_app.config.get('MAIL_SERVER')
    smtp_port = current_app.config.get('MAIL_PORT')
    sender_email = current_app.config.get('MAIL_USERNAME')
    sender_password = current_app.config.get('MAIL_PASSWORD')
    use_tls = current_app.config.get('MAIL_USE_TLS', True)
    
    # 输出详细的配置信息
    logger.info(f"SMTP配置: 服务器={smtp_server}, 端口={smtp_port}, 发件人={sender_email}")
    logger.info(f"开始向 {recipient} 发送邮件, 主题: {subject}")
    
    # 移除密码中的空格(如果有)
    if sender_password:
        sender_password = sender_password.replace(" ", "")
    else:
        logger.error("邮箱密码未配置")
    
    # 检查是否配置了邮件发送参数
    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        missing_items = []
        if not smtp_server: missing_items.append("MAIL_SERVER")
        if not smtp_port: missing_items.append("MAIL_PORT")
        if not sender_email: missing_items.append("MAIL_USERNAME")
        if not sender_password: missing_items.append("MAIL_PASSWORD")
        
        logger.warning(f"邮件发送配置不完整，缺少: {', '.join(missing_items)}")
        return False
    
    try:
        # 记录邮件信息
        logger.info(f"准备发送邮件 - 发送到: {recipient}")
        logger.info(f"邮件主题: {subject}")
        
        # 创建邮件
        if html:
            msg = MIMEText(html, 'html', 'utf-8')
            logger.debug("使用HTML格式邮件")
        else:
            msg = MIMEText(content, 'plain', 'utf-8')
            logger.debug("使用纯文本格式邮件")
            
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender_email
        msg['To'] = recipient
        
        # 连接SMTP服务器
        logger.info(f"连接SMTP服务器: {smtp_server}:{smtp_port}")
        try:
            if use_tls:
                logger.info("使用TLS加密连接")
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()  # 启用TLS加密
            else:
                logger.info("使用非加密连接")
                server = smtplib.SMTP(smtp_server, smtp_port)
                
            # 登录并发送
            logger.info(f"尝试登录邮箱: {sender_email}")
            server.login(sender_email, sender_password)
            
            logger.info(f"开始发送邮件到: {recipient}")
            server.sendmail(sender_email, [recipient], msg.as_string())
            server.quit()
            
            logger.info("邮件发送成功")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP认证失败: {str(e)}")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP连接失败: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {str(e)}")
            return False
        except TimeoutError as e:
            logger.error(f"连接SMTP服务器超时: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"发送邮件失败: {str(e)}", exc_info=True)
        return False

def send_admin_notification(subject, content):
    """
    发送通知邮件给管理员
    
    参数:
        subject: 邮件主题
        content: 邮件内容
        
    返回值:
        成功时返回True，失败时返回False
    """
    admin_email = current_app.config.get('ADMIN_EMAIL', "James.ni@evertacsolutions.com")
    if not admin_email:
        logger.warning("未配置管理员邮箱，无法发送通知")
        return False
    
    # 先记录到日志
    logger.info(f"准备发送通知邮件 - 收件人: {admin_email}")
    logger.info(f"通知邮件 - 主题: {subject}")
    logger.info(f"通知邮件 - 内容: {content}")
    
    # 从配置中获取邮件设置
    smtp_server = current_app.config.get('MAIL_SERVER')
    smtp_port = current_app.config.get('MAIL_PORT')
    sender_email = current_app.config.get('MAIL_USERNAME')
    sender_password = current_app.config.get('MAIL_PASSWORD')
    use_tls = current_app.config.get('MAIL_USE_TLS', True)
    
    # 输出邮件配置信息（不包含密码）
    logger.info(f"邮件服务器: {smtp_server}:{smtp_port}")
    logger.info(f"发件人: {sender_email}")
    logger.info(f"TLS加密: {'启用' if use_tls else '禁用'}")
    
    return send_email(subject, admin_email, content)

def send_user_invitation_email(user_data):
    """
    发送邀请邮件给新创建的用户
    
    参数:
    - user_data: 字典，包含用户信息（username, real_name, company_name, role, email等）
    
    返回值:
    - 成功发送返回True，否则返回False
    """
    try:
        from app.models.user import User
        username = user_data.get('username')
        real_name = user_data.get('real_name')
        email = user_data.get('email')
        company_name = user_data.get('company_name')
        role = user_data.get('role')
        user_id = user_data.get('id')
        
        # 获取应用域名
        app_domain = current_app.config.get('APP_DOMAIN', request.host_url.rstrip('/'))
        
        # 生成邀请令牌
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        invitation_token = s.dumps({'user_id': user_id, 'action': 'activate'}, salt='user-activation')
        
        # 构建激活链接
        activation_url = f"{app_domain}/auth/activate/{invitation_token}"
        
        # 角色的中文名称
        role_names = {
            'admin': '系统管理员',
            'sales': '销售人员',
            'product': '产品经理',
            'product_manager': '产品经理',
            'solution': '解决方案经理',
            'solution_manager': '解决方案经理',
            'service': '服务',
            'service_manager': '服务经理',
            'channel': '渠道经理',
            'channel_manager': '渠道经理',
            'marketing_director': '营销总监',
            'agent': '代理商',
            'dealer': '代理商',
            'user': '普通用户'
        }
        role_name = role_names.get(role, '用户')
        
        # 创建热情的邀请邮件内容
        subject = f"🎉 热烈欢迎加入项目管理系统！"
        
        html_content = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
            <h2 style="color: #3f51b5; text-align: center; margin-bottom: 20px;">🎉 热烈欢迎加入我们！</h2>
            
            <p style="font-size: 16px; line-height: 1.6;">亲爱的 <strong>{real_name}</strong>：</p>
            
            <p style="font-size: 16px; line-height: 1.6;">太棒了！您已成功被添加到我们的项目管理系统！我们非常高兴您能够加入我们的团队，相信您的加入将为我们带来新的活力和创新！</p>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #3f51b5;">您的账户信息</h3>
                <p><strong>用户名：</strong> {username}</p>
                <p><strong>公司名称：</strong> {company_name}</p>
                <p><strong>用户角色：</strong> {role_name}</p>
            </div>
            
            <p style="font-size: 16px; line-height: 1.6;">请点击下方按钮设置您的密码并激活账户：</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{activation_url}" style="background-color: #3f51b5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                    设置密码并激活账户
                </a>
            </div>
            
            <p style="font-size: 16px; line-height: 1.6;"><strong>请注意：</strong>此激活链接将在24小时内有效，请尽快完成账户设置。</p>
            
            <p style="font-size: 16px; line-height: 1.6;">如有任何问题或需要帮助，请随时与管理员联系。</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center; color: #757575; font-size: 14px;">
                <p>此邮件由系统自动发送，请勿直接回复</p>
                <p>©️ 项目管理系统团队</p>
            </div>
        </div>
        """
        
        # 发送邮件
        logger.info(f"正在向新用户 {username} 发送邀请邮件")
        return send_email(subject, email, None, html=html_content)
    
    except Exception as e:
        logger.error(f"发送用户邀请邮件失败: {str(e)}")
        return False

def send_password_reset_email(user, reset_token, reset_url):
    """
    发送密码重置邮件给用户
    
    参数:
        user: User对象，包含用户信息
        reset_token: 重置密码的令牌
        reset_url: 重置密码的完整URL
        
    返回值:
        成功时返回True，失败时返回False
    """
    try:
        subject = "密码重置请求"
        
        # 记录重置URL
        logger.info(f"准备发送密码重置邮件给用户: {user.username} <{user.email}>")
        logger.info(f"生成的密码重置链接: {reset_url}")
        
        # 检查邮件配置
        smtp_server = current_app.config.get('MAIL_SERVER')
        smtp_port = current_app.config.get('MAIL_PORT')
        sender_email = current_app.config.get('MAIL_USERNAME')
        
        logger.info(f"邮件服务器配置: {smtp_server}:{smtp_port}, 发件人: {sender_email}")
        
        # 创建HTML邮件内容
        html_content = f"""
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
            <h2 style="color: #3f51b5; text-align: center; margin-bottom: 20px;">项目管理系统 - 密码重置</h2>
            
            <p style="font-size: 16px; line-height: 1.6;">亲爱的 <strong>{user.real_name}</strong>：</p>
            
            <p style="font-size: 16px; line-height: 1.6;">我们收到了重置您账户密码的请求。如果这不是您本人的操作，请忽略此邮件。</p>
            
            <p style="font-size: 16px; line-height: 1.6;">如需重置密码，请点击下方按钮：</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}" style="background-color: #3f51b5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                    重置我的密码
                </a>
            </div>
            
            <p style="font-size: 16px; line-height: 1.6;">或者，您可以复制以下链接到浏览器地址栏：</p>
            
            <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; word-break: break-all;">
                {reset_url}
            </p>
            
            <p style="font-size: 16px; line-height: 1.6;"><strong>注意：</strong>此链接将在30分钟后失效。</p>
            
            <p style="font-size: 16px; line-height: 1.6;">如果您没有请求重置密码，请忽略此邮件，您的账户将保持安全。</p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center; color: #757575; font-size: 14px;">
                <p>此邮件由系统自动发送，请勿直接回复</p>
                <p>©️ 项目管理系统团队</p>
            </div>
        </div>
        """
        
        # 发送邮件并获取结果
        logger.info(f"调用send_email函数发送密码重置邮件至 {user.email}")
        result = send_email(subject, user.email, None, html=html_content)
        
        if result:
            logger.info(f"密码重置邮件发送成功")
        else:
            logger.error(f"密码重置邮件发送失败")
            
        return result
        
    except Exception as e:
        logger.error(f"发送密码重置邮件异常: {str(e)}", exc_info=True)
        return False