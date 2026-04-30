"""邮件发送工具模块"""

import smtplib
import logging
import threading
import io
import zipfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
from flask import current_app, request
from itsdangerous import URLSafeTimedSerializer

logger = logging.getLogger(__name__)


def _send_email_sync(smtp_server, smtp_port, sender_email, sender_password, use_tls, use_ssl, recipient, subject, msg_string):
    """同步发送邮件的内部函数（在后台线程中执行）

    Args:
        smtp_server: SMTP服务器地址
        smtp_port: SMTP端口
        sender_email: 发件人邮箱
        sender_password: 发件人密码/授权码
        use_tls: 是否使用STARTTLS（端口587常用）
        use_ssl: 是否使用SSL（端口465常用，国内邮件服务常用此模式）
        recipient: 收件人邮箱
        subject: 邮件主题
        msg_string: 邮件内容字符串
    """
    try:
        if use_ssl:
            # SSL模式：直接建立加密连接（端口465，国内邮件服务常用）
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        elif use_tls:
            # TLS模式：先明文连接再升级加密（端口587，Gmail常用）
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        else:
            # 无加密模式（不推荐）
            server = smtplib.SMTP(smtp_server, smtp_port)

        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [recipient], msg_string)
        server.quit()
        logger.info(f"邮件发送成功: {recipient}")
        return True
    except Exception as e:
        logger.error(f"后台邮件发送失败: {str(e)}")
        return False

def generate_dxt_bytes(token: str, display_name: str = 'PMA', host: str = 'pma-mcp.jamesgpone.win') -> bytes:
    """生成用户专属的 .dxt 扩展包（内存中，返回 bytes）
    使用 Node.js bridge，依赖 Claude Desktop 内置 Node.js，无需用户安装任何环境。
    host: MCP 服务器域名，CN NAS 用 pma-mcp.jamesgpone.win，SG NAS 用 sg-pma-mcp.jamesgpone.win
    """
    manifest = f'''{{
  "dxt_version": "0.1",
  "name": "pma",
  "display_name": "{display_name}",
  "version": "1.1.0",
  "description": "连接 PMA 业务系统，查询报价单、项目、客户、审批等数据",
  "author": {{"name": "Evertac"}},
  "server": {{
    "type": "node",
    "entry_point": "server/bridge.js",
    "mcp_config": {{
      "command": "node",
      "args": ["${{__dirname}}/server/bridge.js"]
    }}
  }}
}}'''

    bridge = f"""'use strict';
// PMA MCP stdio bridge (Node.js)
const https = require('https');
const readline = require('readline');

const TOKEN = process.env.PMA_TOKEN || '{token}';
const HOST  = '{host}';
const PATH  = '/mcp?token=' + TOKEN;

let sessionId = null;

function httpPost(payload) {{
  return new Promise((resolve, reject) => {{
    const body = JSON.stringify(payload);
    const headers = {{
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream',
      'mcp-protocol-version': '2024-11-05',
      'Content-Length': Buffer.byteLength(body),
    }};
    if (sessionId) headers['mcp-session-id'] = sessionId;

    const req = https.request({{ hostname: HOST, path: PATH, method: 'POST', headers }}, (res) => {{
      const sid = res.headers['mcp-session-id'];
      if (sid) sessionId = sid;
      const ct = res.headers['content-type'] || '';
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {{
        if (ct.includes('text/event-stream')) {{
          for (const line of data.split('\\n')) {{
            if (line.startsWith('data: ')) {{
              try {{ resolve(JSON.parse(line.slice(6))); return; }} catch (_) {{}}
            }}
          }}
          resolve(null);
        }} else {{
          try {{ resolve(JSON.parse(data)); }} catch (e) {{ reject(e); }}
        }}
      }});
    }});
    req.on('error', reject);
    req.write(body);
    req.end();
  }});
}}

const rl = readline.createInterface({{ input: process.stdin }});
rl.on('line', async (line) => {{
  line = line.trim();
  if (!line) return;
  try {{
    const msg  = JSON.parse(line);
    const resp = await httpPost(msg);
    if (resp) process.stdout.write(JSON.stringify(resp) + '\\n');
  }} catch (e) {{
    let mid = null;
    try {{ mid = JSON.parse(line).id; }} catch (_) {{}}
    if (mid !== null && mid !== undefined) {{
      process.stdout.write(JSON.stringify({{
        jsonrpc: '2.0', id: mid,
        error: {{ code: -32603, message: String(e) }}
      }}) + '\\n');
    }}
  }}
}});
"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', manifest)
        zf.writestr('server/bridge.js', bridge)
    return buf.getvalue()


def send_email(subject, recipient, content, html=None, async_send=True, attachments=None):
    """发送邮件的通用函数

    Args:
        subject: 邮件主题
        recipient: 收件人邮箱
        content: 纯文本内容
        html: HTML内容（可选）
        async_send: 是否异步发送（默认True，在后台线程中发送，不阻塞主请求）

    Returns:
        bool: 同步模式返回发送结果；异步模式返回True表示已加入发送队列
    """
    # 从配置中获取邮件设置
    smtp_server = current_app.config.get('MAIL_SERVER')
    smtp_port = current_app.config.get('MAIL_PORT')
    sender_email = current_app.config.get('MAIL_USERNAME')
    sender_password = current_app.config.get('MAIL_PASSWORD')
    use_tls = current_app.config.get('MAIL_USE_TLS', True)
    use_ssl = current_app.config.get('MAIL_USE_SSL', False)

    # 输出详细的配置信息
    logger.info(f"SMTP配置: 服务器={smtp_server}, 端口={smtp_port}, 发件人={sender_email}, TLS={use_tls}, SSL={use_ssl}")
    logger.info(f"开始向 {recipient} 发送邮件, 主题: {subject}, 异步模式: {async_send}")

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
        if attachments:
            msg = MIMEMultipart()
            body = MIMEText(html or content or '', 'html' if html else 'plain', 'utf-8')
            msg.attach(body)
            for filename, data in attachments:
                part = MIMEApplication(data, Name=filename)
                part['Content-Disposition'] = f'attachment; filename="{filename}"'
                msg.attach(part)
        elif html:
            msg = MIMEText(html, 'html', 'utf-8')
            logger.debug("使用HTML格式邮件")
        else:
            msg = MIMEText(content, 'plain', 'utf-8')
            logger.debug("使用纯文本格式邮件")

        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = sender_email
        msg['To'] = recipient

        msg_string = msg.as_string()

        if async_send:
            # 异步模式：在后台线程中发送邮件，立即返回
            thread = threading.Thread(
                target=_send_email_sync,
                args=(smtp_server, smtp_port, sender_email, sender_password, use_tls, use_ssl, recipient, subject, msg_string)
            )
            thread.daemon = True  # 设为守护线程，主程序退出时自动结束
            thread.start()
            logger.info(f"邮件已加入后台发送队列: {recipient}")
            return True
        else:
            # 同步模式：等待发送完成
            return _send_email_sync(smtp_server, smtp_port, sender_email, sender_password, use_tls, use_ssl, recipient, subject, msg_string)

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
            'sales_director': '营销总监',
            'agent': '代理商',
            'dealer': '代理商',
            'user': '普通用户'
        }
        role_name = role_names.get(role, '用户')
        
        # 创建极简风格邀请邮件内容
        subject = f"PMA系统账户邀请 - {real_name}"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8"/>
            <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
        </head>
        <body style="margin: 0; padding: 0; background-color: #ffffff; font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased;">
            <div style="max-width: 600px; margin: 0 auto; padding: 48px 24px;">
                <!-- 头部 -->
                <div style="text-align: center; padding-bottom: 32px; margin-bottom: 32px; border-bottom: 1px solid #a0a0a0;">
                    <h1 style="font-size: 28px; font-weight: 300; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.05em; color: #1a1a1a;">PMA系统账户邀请</h1>
                    <p style="font-size: 16px; color: #545454; margin: 0; font-family: 'Roboto Mono', monospace; letter-spacing: -0.025em;">ACCOUNT INVITATION</p>
                </div>

                <!-- 欢迎信息 -->
                <div style="text-align: center; padding-bottom: 32px; margin-bottom: 32px; border-bottom: 1px solid #a0a0a0;">
                    <p style="font-size: 18px; color: #404040; margin: 0 0 24px 0; font-weight: 300;">
                        尊敬的 <strong style="font-weight: 500;">{real_name}</strong>，欢迎加入我们的团队
                    </p>
                    <a href="{activation_url}" style="display: inline-block; padding: 14px 32px; border: 1px solid #607d8b; color: #607d8b; text-decoration: none; font-weight: 500; font-size: 14px; letter-spacing: 0.025em; transition: all 0.2s;">
                        &#8594;&nbsp;&nbsp;激活您的账户
                    </a>
                </div>

                <!-- 账户信息 -->
                <div style="margin-bottom: 32px;">
                    <div style="display: flex; align-items: center; margin-bottom: 24px;">
                        <span style="font-size: 24px; font-weight: 300; color: #1a1a1a; margin-right: 12px;">I.</span>
                        <h2 style="font-size: 18px; font-weight: 400; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; color: #1a1a1a;">账户信息</h2>
                    </div>

                    <div style="border-bottom: 1px solid #e8e8e8; padding-bottom: 24px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; width: 50%;">
                                    <span style="display: block; font-size: 12px; font-weight: 500; color: #545454; margin-bottom: 4px;">用户名</span>
                                    <span style="font-size: 14px; color: #2c2c2c;">{username}</span>
                                </td>
                                <td style="padding: 8px 0; width: 50%;">
                                    <span style="display: block; font-size: 12px; font-weight: 500; color: #545454; margin-bottom: 4px;">用户角色</span>
                                    <span style="font-size: 14px; color: #2c2c2c;">{role_name}</span>
                                </td>
                            </tr>
                            <tr>
                                <td colspan="2" style="padding: 8px 0;">
                                    <span style="display: block; font-size: 12px; font-weight: 500; color: #545454; margin-bottom: 4px;">所属公司</span>
                                    <span style="font-size: 14px; color: #2c2c2c;">{company_name}</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>

                <!-- 操作说明 -->
                <div style="margin-bottom: 32px;">
                    <div style="display: flex; align-items: center; margin-bottom: 24px;">
                        <span style="font-size: 24px; font-weight: 300; color: #1a1a1a; margin-right: 12px;">II.</span>
                        <h2 style="font-size: 18px; font-weight: 400; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; color: #1a1a1a;">激活步骤</h2>
                    </div>

                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #e8e8e8;">
                            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #404040; letter-spacing: 0.025em;">步骤</td>
                            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #404040; letter-spacing: 0.025em;">操作说明</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e8e8e8;">
                            <td style="padding: 12px 16px; font-size: 14px; font-weight: 500; color: #1a1a1a;">1. 点击激活链接</td>
                            <td style="padding: 12px 16px; font-size: 14px; color: #545454;">点击上方按钮或复制下方链接到浏览器</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e8e8e8;">
                            <td style="padding: 12px 16px; font-size: 14px; font-weight: 500; color: #1a1a1a;">2. 设置密码</td>
                            <td style="padding: 12px 16px; font-size: 14px; color: #545454;">创建您的登录密码（至少8位字符）</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e8e8e8;">
                            <td style="padding: 12px 16px; font-size: 14px; font-weight: 500; color: #1a1a1a;">3. 完成激活</td>
                            <td style="padding: 12px 16px; font-size: 14px; color: #545454;">使用用户名和新密码登录系统</td>
                        </tr>
                    </table>
                </div>

                <!-- 重要提示 -->
                <div style="border: 1px solid #a0a0a0; padding: 24px; margin-bottom: 32px;">
                    <div style="display: flex; align-items: flex-start;">
                        <div>
                            <h3 style="font-size: 16px; font-weight: 500; color: #2c2c2c; margin: 0 0 12px 0;">重要提示</h3>
                            <p style="font-size: 14px; color: #545454; margin: 0; line-height: 1.6;">
                                此激活链接将在 <strong style="color: #607d8b;">24小时</strong> 内有效。如链接过期，请联系系统管理员重新发送邀请。
                            </p>
                        </div>
                    </div>
                </div>

                <!-- 激活链接备用 -->
                <div style="margin-bottom: 32px;">
                    <p style="font-size: 12px; color: #686868; margin: 0 0 8px 0;">如按钮无法点击，请复制以下链接到浏览器：</p>
                    <p style="font-size: 12px; color: #607d8b; margin: 0; word-break: break-all; font-family: 'Roboto Mono', monospace;">
                        {activation_url}
                    </p>
                </div>

                <!-- 页脚 -->
                <div style="text-align: center; padding-top: 32px; border-top: 1px solid #a0a0a0;">
                    <p style="font-size: 12px; color: #686868; margin: 0; font-family: 'Roboto Mono', monospace;">
                        &copy; 2025 PMA系统管理团队. All rights reserved.
                    </p>
                    <p style="font-size: 11px; color: #a0a0a0; margin: 8px 0 0 0;">
                        此邮件由系统自动发送，请勿直接回复
                    </p>
                </div>
            </div>
        </body>
        </html>
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
def send_claude_ai_token_email(user, token, is_reset=False, attach_dxt=True):
    """发送 Claude AI 代理 token 邮件给用户。

    参数:
        user: User 对象
        token: 该用户的 cliproxy token
        is_reset: 是否为重置操作（True 时邮件主题和正文略有不同）

    返回值:
        bool 发送成功返回 True
    """
    try:
        import os
        from flask import current_app

        if not user or not user.email:
            logger.warning(f'send_claude_ai_token_email: 用户邮箱缺失')
            return False

        public_url = (
            os.environ.get('CLAUDE_AI_PROXY_PUBLIC_URL')
            or current_app.config.get('CLAUDE_AI_PROXY_PUBLIC_URL', 'https://mac-proxy.jamesgpone.win')
        )
        default_quota_val = (
            os.environ.get('CLAUDE_AI_DEFAULT_QUOTA')
            or current_app.config.get('CLAUDE_AI_DEFAULT_QUOTA', 50_000_000)
        )
        quota = user.claude_ai_quota_tokens or int(default_quota_val)
        quota_display = f'{int(quota):,}'

        real_name = user.real_name or user.username
        action_en = 'TOKEN RESET' if is_reset else 'CLAUDE AI ENABLED'

        # 根据数据库类型判断语言（sp8d=CN中文，ovs=SG英文）
        db_type = os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE', 'sp8d')
        is_cn = (db_type == 'sp8d')

        if is_cn:
            subject = f'PMA Claude AI 代理已{"重置" if is_reset else "开通"} - {real_name}'
            notice_text = (
                '你之前的 Token 已立即失效，请使用以下新 Token 替换原有配置。'
                if is_reset else
                '你的 PMA 账号已获得 Claude AI 工作助手的使用权限，请按下方说明完成配置。'
            )
            sec_title = '使用规范'
            sec_body = (
                'Claude AI 是公司提供的工作效率工具，请仅用于工作相关事务，并遵守公司 AI 工具保密规定，'
                '勿将客户资料、商业机密等内部信息输入用于非工作目的。'
                'Token 为个人专属凭证，请勿转让或共享。如怀疑泄漏，请登录 PMA 个人中心自助重置。'
                '月度配额超限后请求将暂停至下月 1 日自动恢复。'
            )
            cred_title = '你的凭证'
            cfg_title = 'Claude Desktop 配置'
            field_col = '字段'
            value_col = '值'
            quota_label = '月度配额'
            footer_copy = '&copy; 2026 PMA系统管理团队. All rights reserved.'
            footer_note = '此邮件由系统自动发送，请勿直接回复'
            lang = 'zh-CN'
        else:
            subject = f'PMA Claude AI Gateway {"Reset" if is_reset else "Enabled"} - {real_name}'
            notice_text = (
                f'Your previous token has been invalidated. Please update your configuration with the new token below.'
                if is_reset else
                f'Your PMA account has been granted access to the Claude AI Gateway. Please follow the instructions below to configure your client.'
            )
            sec_title = 'Usage Policy'
            sec_body = (
                'Claude AI is a company-provided productivity tool. Please use it exclusively for work-related purposes '
                'and comply with the company\'s AI tool confidentiality policy. Do not input confidential client data, '
                'trade secrets, or internal information for non-work purposes. '
                'Your token is personal and non-transferable. If you suspect it has been compromised, '
                'reset it immediately via your PMA profile. '
                'Monthly quota will be automatically reset on the 1st of each month.'
            )
            cred_title = 'Your Credentials'
            cfg_title = 'Claude Desktop Setup'
            field_col = 'Field'
            value_col = 'Value'
            quota_label = 'Monthly Quota'
            footer_copy = '&copy; 2026 PMA Team. All rights reserved.'
            footer_note = 'This email was sent automatically. Please do not reply directly.'
            lang = 'en'

        html_content = f"""
        <!DOCTYPE html>
        <html lang="{lang}">
        <head>
            <meta charset="utf-8"/>
            <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
        </head>
        <body style="margin: 0; padding: 0; background-color: #ffffff; font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; -webkit-font-smoothing: antialiased;">
            <div style="max-width: 600px; margin: 0 auto; padding: 48px 24px;">
                <div style="text-align: center; padding-bottom: 32px; margin-bottom: 32px; border-bottom: 1px solid #a0a0a0;">
                    <h1 style="font-size: 28px; font-weight: 300; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.05em; color: #1a1a1a;">PMA Claude AI</h1>
                    <p style="font-size: 16px; color: #545454; margin: 0; font-family: 'Roboto Mono', monospace; letter-spacing: -0.025em;">{action_en}</p>
                </div>

                <div style="text-align: center; padding-bottom: 32px; margin-bottom: 32px; border-bottom: 1px solid #a0a0a0;">
                    <p style="font-size: 18px; color: #404040; margin: 0; font-weight: 300;">
                        <strong style="font-weight: 500;">{real_name}</strong>，{notice_text}
                    </p>
                </div>

                <div style="margin-bottom: 32px;">
                    <div style="display: flex; align-items: center; margin-bottom: 24px;">
                        <span style="font-size: 24px; font-weight: 300; color: #1a1a1a; margin-right: 12px;">I.</span>
                        <h2 style="font-size: 18px; font-weight: 400; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; color: #1a1a1a;">{cred_title}</h2>
                    </div>
                    <div style="border-bottom: 1px solid #e8e8e8; padding-bottom: 24px;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0;">
                                    <span style="display: block; font-size: 12px; font-weight: 500; color: #545454; margin-bottom: 4px;">Gateway URL</span>
                                    <span style="font-size: 14px; color: #2c2c2c; font-family: 'Roboto Mono', monospace;">{public_url}</span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0;">
                                    <span style="display: block; font-size: 12px; font-weight: 500; color: #545454; margin-bottom: 4px;">API Key (Token)</span>
                                    <span style="font-size: 14px; color: #2c2c2c; font-family: 'Roboto Mono', monospace; word-break: break-all;">{token}</span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0;">
                                    <span style="display: block; font-size: 12px; font-weight: 500; color: #545454; margin-bottom: 4px;">{quota_label}</span>
                                    <span style="font-size: 14px; color: #2c2c2c;">{quota_display} tokens</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>

                <div style="margin-bottom: 32px;">
                    <div style="display: flex; align-items: center; margin-bottom: 24px;">
                        <span style="font-size: 24px; font-weight: 300; color: #1a1a1a; margin-right: 12px;">II.</span>
                        <h2 style="font-size: 18px; font-weight: 400; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; color: #1a1a1a;">{cfg_title}</h2>
                    </div>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background-color: #e8e8e8;">
                            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #404040;">{field_col}</td>
                            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #404040;">{value_col}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e8e8e8;">
                            <td style="padding: 12px 16px; font-size: 14px; font-weight: 500; color: #1a1a1a;">Connection</td>
                            <td style="padding: 12px 16px; font-size: 14px; color: #545454;">Gateway (Anthropic-compatible)</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e8e8e8;">
                            <td style="padding: 12px 16px; font-size: 14px; font-weight: 500; color: #1a1a1a;">Gateway base URL</td>
                            <td style="padding: 12px 16px; font-size: 13px; color: #545454; font-family: 'Roboto Mono', monospace;">{public_url}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e8e8e8;">
                            <td style="padding: 12px 16px; font-size: 14px; font-weight: 500; color: #1a1a1a;">Gateway API key</td>
                            <td style="padding: 12px 16px; font-size: 13px; color: #545454; font-family: 'Roboto Mono', monospace; word-break: break-all;">{token}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e8e8e8;">
                            <td style="padding: 12px 16px; font-size: 14px; font-weight: 500; color: #1a1a1a;">Gateway auth scheme</td>
                            <td style="padding: 12px 16px; font-size: 14px; color: #545454;">bearer</td>
                        </tr>
                    </table>
                </div>

                <div style="border: 1px solid #a0a0a0; padding: 24px; margin-bottom: 32px;">
                    <h3 style="font-size: 16px; font-weight: 500; color: #2c2c2c; margin: 0 0 12px 0;">{sec_title}</h3>
                    <p style="font-size: 14px; color: #545454; margin: 0; line-height: 1.6;">
                        {sec_body}
                    </p>
                </div>

                <div style="text-align: center; padding-top: 32px; border-top: 1px solid #a0a0a0;">
                    <p style="font-size: 12px; color: #686868; margin: 0; font-family: 'Roboto Mono', monospace;">
                        {footer_copy}
                    </p>
                    <p style="font-size: 11px; color: #a0a0a0; margin: 8px 0 0 0;">
                        {footer_note}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        logger.info(f'正在向 {user.username} 发送 Claude AI {"重置" if is_reset else "开通"} 邮件')
        attachments = None
        if attach_dxt and not is_reset:
            try:
                mcp_host = 'sg-pma-mcp.jamesgpone.win' if not is_cn else 'pma-mcp.jamesgpone.win'
                dxt_bytes = generate_dxt_bytes(token, display_name='PMA', host=mcp_host)
                safe_name = (user.username or 'user').lower()
                attachments = [(f'pma-{safe_name}.dxt', dxt_bytes)]
            except Exception as e:
                logger.warning(f'生成 DXT 附件失败，继续发送邮件: {e}')
        return send_email(subject, user.email, None, html=html_content, async_send=False, attachments=attachments)

    except Exception as e:
        logger.error(f'发送 Claude AI 邮件失败: {e}', exc_info=True)
        return False


def send_dxt_install_email(user) -> bool:
    """发送 Claude Desktop 扩展安装说明邮件（含 .dxt 附件）"""
    try:
        import os
        if not user or not user.email:
            logger.warning('send_dxt_install_email: 用户邮箱缺失')
            return False
        if not user.claude_ai_token:
            logger.warning('send_dxt_install_email: 用户未开通 Claude AI')
            return False

        real_name = user.real_name or user.username
        safe_name = (user.username or 'user').lower()
        db_type = os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE', 'sp8d')
        is_cn = (db_type == 'sp8d')

        if is_cn:
            subject = f'PMA Claude Desktop 扩展安装指南 - {real_name}'
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background:#fff;font-family:'Inter','Helvetica Neue',Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:48px 24px;">
  <div style="text-align:center;padding-bottom:32px;margin-bottom:32px;border-bottom:1px solid #a0a0a0;">
    <h1 style="font-size:28px;font-weight:300;margin:0 0 8px 0;text-transform:uppercase;letter-spacing:.05em;color:#1a1a1a;">PMA Claude AI</h1>
    <p style="font-size:16px;color:#545454;margin:0;font-family:'Roboto Mono',monospace;">DESKTOP EXTENSION</p>
  </div>
  <div style="text-align:center;padding-bottom:32px;margin-bottom:32px;border-bottom:1px solid #a0a0a0;">
    <p style="font-size:18px;color:#404040;margin:0;font-weight:300;">
      <strong style="font-weight:500;">{real_name}</strong>，你的 PMA Claude Desktop 扩展已准备好，请按以下步骤完成安装。
    </p>
  </div>
  <div style="margin-bottom:32px;">
    <h3 style="font-size:16px;font-weight:500;color:#2c2c2c;margin:0 0 16px 0;">安装步骤</h3>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="border-bottom:1px solid #e8e8e8;">
        <td style="padding:12px 16px;width:32px;font-size:20px;">1</td>
        <td style="padding:12px 16px;font-size:14px;color:#1a1a1a;">
          <strong>下载附件</strong><br>
          <span style="color:#545454;">保存邮件附件 <code style="font-family:monospace;background:#f5f5f5;padding:2px 6px;border-radius:3px;">pma-{safe_name}.dxt</code> 到电脑</span>
        </td>
      </tr>
      <tr style="border-bottom:1px solid #e8e8e8;">
        <td style="padding:12px 16px;font-size:20px;">2</td>
        <td style="padding:12px 16px;font-size:14px;color:#1a1a1a;">
          <strong>打开 Claude Desktop</strong><br>
          <span style="color:#545454;">点击左下角头像 → Settings → 左侧 Extensions</span>
        </td>
      </tr>
      <tr style="border-bottom:1px solid #e8e8e8;">
        <td style="padding:12px 16px;font-size:20px;">3</td>
        <td style="padding:12px 16px;font-size:14px;color:#1a1a1a;">
          <strong>拖入安装</strong><br>
          <span style="color:#545454;">将 .dxt 文件拖入 Extensions 页面中的 "Drag .MCPB or .DXT files here to install" 区域</span>
        </td>
      </tr>
      <tr>
        <td style="padding:12px 16px;font-size:20px;">4</td>
        <td style="padding:12px 16px;font-size:14px;color:#1a1a1a;">
          <strong>启用扩展</strong><br>
          <span style="color:#545454;">安装后点击 PMA 扩展的开关将其启用，即可在对话中使用 PMA 数据查询</span>
        </td>
      </tr>
    </table>
  </div>
  <div style="border:1px solid #e8e8e8;border-radius:6px;padding:16px;margin-bottom:32px;background:#f9f9f9;">
    <p style="font-size:13px;color:#545454;margin:0;">
      安装完成后，你可以在 Claude Desktop 对话框中直接提问，例如：<br>
      <em>"帮我查一下本月的报价单"</em>&nbsp;&nbsp;
      <em>"最近有哪些待审批项目？"</em>
    </p>
  </div>
  <div style="text-align:center;padding-top:32px;border-top:1px solid #a0a0a0;">
    <p style="font-size:12px;color:#686868;margin:0;font-family:'Roboto Mono',monospace;">&copy; 2026 PMA系统管理团队. All rights reserved.</p>
    <p style="font-size:11px;color:#a0a0a0;margin:8px 0 0 0;">此邮件由系统自动发送，请勿直接回复</p>
  </div>
</div>
</body>
</html>"""
        else:
            subject = f'PMA Claude Desktop Extension - Installation Guide - {real_name}'
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;background:#fff;font-family:'Inter','Helvetica Neue',Arial,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:48px 24px;">
  <div style="text-align:center;padding-bottom:32px;margin-bottom:32px;border-bottom:1px solid #a0a0a0;">
    <h1 style="font-size:28px;font-weight:300;margin:0 0 8px 0;text-transform:uppercase;letter-spacing:.05em;color:#1a1a1a;">PMA Claude AI</h1>
    <p style="font-size:16px;color:#545454;margin:0;font-family:'Roboto Mono',monospace;">DESKTOP EXTENSION</p>
  </div>
  <div style="text-align:center;padding-bottom:32px;margin-bottom:32px;border-bottom:1px solid #a0a0a0;">
    <p style="font-size:18px;color:#404040;margin:0;font-weight:300;">
      Hi <strong style="font-weight:500;">{real_name}</strong>, your PMA Claude Desktop extension is ready to install.
    </p>
  </div>
  <div style="margin-bottom:32px;">
    <h3 style="font-size:16px;font-weight:500;color:#2c2c2c;margin:0 0 16px 0;">Installation Steps</h3>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="border-bottom:1px solid #e8e8e8;">
        <td style="padding:12px 16px;width:32px;font-size:20px;">1</td>
        <td style="padding:12px 16px;font-size:14px;color:#1a1a1a;">
          <strong>Download the attachment</strong><br>
          <span style="color:#545454;">Save the email attachment <code style="font-family:monospace;background:#f5f5f5;padding:2px 6px;border-radius:3px;">pma-{safe_name}.dxt</code> to your computer</span>
        </td>
      </tr>
      <tr style="border-bottom:1px solid #e8e8e8;">
        <td style="padding:12px 16px;font-size:20px;">2</td>
        <td style="padding:12px 16px;font-size:14px;color:#1a1a1a;">
          <strong>Open Claude Desktop</strong><br>
          <span style="color:#545454;">Click the avatar icon (bottom-left) → Settings → Extensions</span>
        </td>
      </tr>
      <tr style="border-bottom:1px solid #e8e8e8;">
        <td style="padding:12px 16px;font-size:20px;">3</td>
        <td style="padding:12px 16px;font-size:14px;color:#1a1a1a;">
          <strong>Drag to install</strong><br>
          <span style="color:#545454;">Drag the .dxt file into the "Drag .MCPB or .DXT files here to install" area on the Extensions page</span>
        </td>
      </tr>
      <tr>
        <td style="padding:12px 16px;font-size:20px;">4</td>
        <td style="padding:12px 16px;font-size:14px;color:#1a1a1a;">
          <strong>Enable the extension</strong><br>
          <span style="color:#545454;">Toggle the PMA extension on — you can now query PMA data directly in Claude conversations</span>
        </td>
      </tr>
    </table>
  </div>
  <div style="text-align:center;padding-top:32px;border-top:1px solid #a0a0a0;">
    <p style="font-size:12px;color:#686868;margin:0;font-family:'Roboto Mono',monospace;">&copy; 2026 PMA Team. All rights reserved.</p>
    <p style="font-size:11px;color:#a0a0a0;margin:8px 0 0 0;">This email was sent automatically. Please do not reply.</p>
  </div>
</div>
</body>
</html>"""

        mcp_host = 'sg-pma-mcp.jamesgpone.win' if not is_cn else 'pma-mcp.jamesgpone.win'
        dxt_bytes = generate_dxt_bytes(user.claude_ai_token, display_name='PMA', host=mcp_host)
        attachments = [(f'pma-{safe_name}.dxt', dxt_bytes)]
        logger.info(f'发送 DXT 安装邮件给 {user.username} ({user.email})')
        return send_email(subject, user.email, None, html=html_content, async_send=False, attachments=attachments)

    except Exception as e:
        logger.error(f'发送 DXT 安装邮件失败: {e}', exc_info=True)
        return False

