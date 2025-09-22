"""
审批邮件通知服务
提供通用的审批邮件发送功能，支持所有审批流程
"""

from flask import current_app, url_for
from app.utils.email import send_email
from app.models.user import User
from app.models.approval import ApprovalInstance, ApprovalStep
import logging

logger = logging.getLogger(__name__)


class ApprovalEmailService:
    """审批邮件服务类"""

    @staticmethod
    def send_approval_notification(instance, step, action=None, comment=None, custom_context=None):
        """
        发送审批通知邮件

        Args:
            instance: 审批实例
            step: 当前审批步骤
            action: 审批动作 ('approve', 'reject', None表示待审批)
            comment: 审批意见
            custom_context: 自定义上下文数据，用于不同业务模块的特殊信息

        Returns:
            bool: 是否发送成功
        """
        try:
            # 检查是否需要发送邮件
            if not step or not step.send_email:
                logger.info(f"步骤 {step.step_name if step else 'None'} 不需要发送邮件通知")
                return True

            # 获取审批人信息
            approver = User.query.get(step.approver_user_id) if step.approver_user_id else None
            if not approver or not approver.email:
                logger.warning(f"审批人未设置或没有邮箱地址: step_id={step.id}")
                return False

            # 发送主通知邮件
            success = ApprovalEmailService._send_single_notification(
                instance, step, approver, action, comment, custom_context
            )

            if not success:
                return False

            # 处理抄送
            if step.cc_enabled and step.cc_users:
                ApprovalEmailService._handle_cc_notifications(
                    instance, step, action, comment, custom_context
                )

            return True

        except Exception as e:
            logger.error(f"发送审批通知邮件失败: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _send_single_notification(instance, step, recipient, action, comment, custom_context):
        """
        发送单个通知邮件

        Args:
            instance: 审批实例
            step: 审批步骤
            recipient: 收件人用户对象
            action: 审批动作
            comment: 审批意见
            custom_context: 自定义上下文

        Returns:
            bool: 是否发送成功
        """
        try:
            # 获取提交人信息
            submitter = User.query.get(instance.created_by) if instance.created_by else None
            submitter_name = submitter.real_name or submitter.username if submitter else "系统"

            # 构建邮件主题
            action_text = ApprovalEmailService._get_action_text(action)
            object_name = ApprovalEmailService._get_object_name(instance.object_type)
            subject = f"[PMA系统] 审批通知 - {object_name} #{instance.object_id} {action_text}"

            # 构建邮件内容
            html_content = ApprovalEmailService._build_email_content(
                instance, step, recipient, action, comment, submitter_name, custom_context
            )

            # 发送邮件
            result = send_email(subject, recipient.email, "", html=html_content)

            if result:
                logger.info(f"审批通知邮件已发送至: {recipient.email}")
            else:
                logger.error(f"审批通知邮件发送失败: {recipient.email}")

            return result

        except Exception as e:
            logger.error(f"发送单个通知邮件失败: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _handle_cc_notifications(instance, step, action, comment, custom_context):
        """
        处理抄送通知

        Args:
            instance: 审批实例
            step: 审批步骤
            action: 审批动作
            comment: 审批意见
            custom_context: 自定义上下文
        """
        try:
            cc_user_ids = step.cc_users if isinstance(step.cc_users, list) else []

            for user_id in cc_user_ids:
                cc_user = User.query.get(user_id)
                if cc_user and cc_user.email:
                    # 发送抄送邮件
                    ApprovalEmailService._send_cc_notification(
                        instance, step, cc_user, action, comment, custom_context
                    )

        except Exception as e:
            logger.error(f"处理抄送通知失败: {str(e)}", exc_info=True)

    @staticmethod
    def _send_cc_notification(instance, step, cc_user, action, comment, custom_context):
        """
        发送抄送邮件

        Args:
            instance: 审批实例
            step: 审批步骤
            cc_user: 抄送用户
            action: 审批动作
            comment: 审批意见
            custom_context: 自定义上下文
        """
        try:
            # 获取提交人信息
            submitter = User.query.get(instance.created_by) if instance.created_by else None
            submitter_name = submitter.real_name or submitter.username if submitter else "系统"

            # 构建邮件主题
            action_text = ApprovalEmailService._get_action_text(action)
            object_name = ApprovalEmailService._get_object_name(instance.object_type)
            subject = f"[PMA系统] 审批通知(抄送) - {object_name} #{instance.object_id}"

            # 构建邮件内容（标记为抄送）
            html_content = ApprovalEmailService._build_email_content(
                instance, step, cc_user, action, comment, submitter_name, custom_context, is_cc=True
            )

            # 发送邮件
            result = send_email(subject, cc_user.email, "", html=html_content)

            if result:
                logger.info(f"审批抄送邮件已发送至: {cc_user.email}")
            else:
                logger.error(f"审批抄送邮件发送失败: {cc_user.email}")

        except Exception as e:
            logger.error(f"发送抄送邮件失败: {str(e)}", exc_info=True)

    @staticmethod
    def _build_email_content(instance, step, recipient, action, comment, submitter_name, custom_context, is_cc=False):
        """
        构建邮件HTML内容

        Args:
            instance: 审批实例
            step: 审批步骤
            recipient: 收件人
            action: 审批动作
            comment: 审批意见
            submitter_name: 提交人名称
            custom_context: 自定义上下文
            is_cc: 是否为抄送邮件

        Returns:
            str: HTML格式的邮件内容
        """
        # 获取审批详情URL
        try:
            approval_url = url_for('approval_config.approval_detail',
                                  instance_id=instance.id,
                                  _external=True,
                                  _scheme='https' if current_app.config.get('ENVIRONMENT') != 'local' else 'http')
        except:
            approval_url = "#"

        action_text = ApprovalEmailService._get_action_text(action)
        action_color = ApprovalEmailService._get_action_color(action)
        object_name = ApprovalEmailService._get_object_name(instance.object_type)

        # 构建自定义信息部分
        custom_info = ""
        if custom_context:
            custom_info = ApprovalEmailService._build_custom_info(custom_context)

        # 构建HTML内容
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
                .content {{ background: white; padding: 30px; border: 1px solid #e0e0e0; border-top: none; }}
                .info-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .info-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #666; display: inline-block; width: 100px; }}
                .value {{ color: #333; }}
                .status {{ display: inline-block; padding: 5px 15px; border-radius: 20px; color: white; font-weight: bold; }}
                .comment-box {{ background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107; }}
                .custom-info {{ background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .button:hover {{ background: #0056b3; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #666; font-size: 12px; }}
                .cc-badge {{ display: inline-block; background: #6c757d; color: white; padding: 3px 10px; border-radius: 12px; font-size: 12px; margin-left: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">审批通知 {'<span class="cc-badge">抄送</span>' if is_cc else ''}</h2>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">PMA项目管理系统</p>
                </div>

                <div class="content">
                    <p>尊敬的 {recipient.real_name or recipient.username}：</p>

                    <div class="info-box">
                        <div class="info-row">
                            <span class="label">审批类型：</span>
                            <span class="value">{object_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">审批编号：</span>
                            <span class="value">#{instance.object_id}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">当前步骤：</span>
                            <span class="value">{step.step_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">审批状态：</span>
                            <span class="status" style="background: {action_color};">{action_text}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">提交人：</span>
                            <span class="value">{submitter_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="label">提交时间：</span>
                            <span class="value">{instance.created_at.strftime('%Y-%m-%d %H:%M:%S') if instance.created_at else '未知'}</span>
                        </div>
                    </div>

                    {custom_info}

                    {f'<div class="comment-box"><strong>审批意见：</strong><br>{comment}</div>' if comment else ''}

                    {'<p style="color: #28a745; font-weight: bold;">请您尽快处理此审批事项。</p>' if action is None and not is_cc else ''}

                    <div style="text-align: center;">
                        <a href="{approval_url}" class="button">查看详情</a>
                    </div>

                    <div class="footer">
                        <p>此邮件由PMA系统自动发送，请勿直接回复。</p>
                        <p>如有疑问，请联系系统管理员。</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content

    @staticmethod
    def _build_custom_info(custom_context):
        """
        构建自定义信息HTML

        Args:
            custom_context: 自定义上下文字典

        Returns:
            str: HTML格式的自定义信息
        """
        if not custom_context:
            return ""

        info_html = '<div class="custom-info"><h4 style="margin-top: 0;">详细信息</h4>'

        for key, value in custom_context.items():
            # 跳过内部使用的键
            if key.startswith('_'):
                continue

            # 转换键名为中文（可以扩展映射）
            label = ApprovalEmailService._translate_field_name(key)
            info_html += f'<div class="info-row"><span class="label">{label}：</span><span class="value">{value}</span></div>'

        info_html += '</div>'
        return info_html

    @staticmethod
    def _get_action_text(action):
        """获取动作文本"""
        action_map = {
            'approve': '已批准',
            'reject': '已拒绝',
            'recall': '已召回',
            None: '待审批'
        }
        return action_map.get(action, '处理中')

    @staticmethod
    def _get_action_color(action):
        """获取动作对应的颜色"""
        color_map = {
            'approve': '#28a745',
            'reject': '#dc3545',
            'recall': '#6c757d',
            None: '#ffc107'
        }
        return color_map.get(action, '#17a2b8')

    @staticmethod
    def _get_object_name(object_type):
        """获取对象类型的中文名称"""
        object_map = {
            'quotation': '报价单',
            'order': '订单',
            'project': '项目',
            'expense': '报销单',
            'pricing_order': '批价单',
            'settlement_order': '结算单',
            'customer': '客户',
            'product': '产品'
        }
        return object_map.get(object_type, object_type)

    @staticmethod
    def _translate_field_name(field_name):
        """翻译字段名为中文"""
        field_map = {
            'total_amount': '总金额',
            'project_name': '项目名称',
            'customer_name': '客户名称',
            'product_name': '产品名称',
            'quantity': '数量',
            'unit_price': '单价',
            'discount': '折扣',
            'remark': '备注',
            'description': '描述'
        }
        return field_map.get(field_name, field_name)