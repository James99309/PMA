#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMA 系统搬迁通知邮件发送脚本
发送给所有激活用户
"""
import sys
import os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models.user import User
from app.utils.email import send_email
import time


def get_email_html(real_name):
    """生成个性化的邮件 HTML"""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PMA系统搬迁通知</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f5f5f5; color: #333; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);">

        <!-- 邮件正文 -->
        <div style="padding: 40px 50px;">
            <!-- 标题 -->
            <div style="text-align: center; margin-bottom: 10px;">
                <h1 style="font-size: 28px; font-weight: 500; color: #333; margin: 0 0 8px 0;">PMA系统搬迁通知</h1>
                <div style="font-size: 14px; color: #888; letter-spacing: 2px; text-transform: uppercase;">SYSTEM MIGRATION NOTICE</div>
            </div>

            <!-- 分隔线 -->
            <div style="height: 1px; background-color: #e0e0e0; margin: 30px 0;"></div>

            <!-- 欢迎语 -->
            <div style="text-align: center; font-size: 16px; color: #333; margin-bottom: 25px;">
                亲爱的 <strong>{real_name}</strong>，你好！<br><br>
                为了给大家提供更好的服务体验，<br>
                PMA系统将搬迁至新地址，新系统拥有<span style="color: #5a9; font-weight: 600;">更大的储存空间</span>和更稳定的服务。
            </div>

            <!-- 访问按钮 -->
            <div style="text-align: center; margin-bottom: 10px;">
                <a href="https://garbage-lottery-hanging-biological.trycloudflare.com" style="display: inline-block; padding: 12px 30px; border: 1px solid #5a9; color: #5a9; text-decoration: none; font-size: 14px;">
                    →  访问新系统
                </a>
            </div>

            <!-- 分隔线 -->
            <div style="height: 1px; background-color: #e0e0e0; margin: 30px 0;"></div>

            <!-- I. 搬迁信息 -->
            <div style="margin-bottom: 30px;">
                <div style="font-size: 16px; font-weight: 500; color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0;">
                    <span style="color: #888; margin-right: 10px;">I.</span>搬迁信息
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px 0; width: 50%; vertical-align: top;">
                            <div style="font-size: 12px; color: #888; margin-bottom: 4px;">搬迁周期</div>
                            <div style="font-size: 14px; color: #e74c3c; font-weight: 600;">一周（7天）</div>
                        </td>
                        <td style="padding: 8px 0; vertical-align: top;">
                            <div style="font-size: 12px; color: #888; margin-bottom: 4px;">数据迁移状态</div>
                            <div style="font-size: 14px; color: #27ae60; font-weight: 600;">✓ 已完成迁移</div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; vertical-align: top;">
                            <div style="font-size: 12px; color: #888; margin-bottom: 4px;">新系统优势</div>
                            <div style="font-size: 14px; color: #333;">更大储存空间 · 更稳定的服务</div>
                        </td>
                        <td style="padding: 8px 0; vertical-align: top;">
                            <div style="font-size: 12px; color: #888; margin-bottom: 4px;">问题联系人</div>
                            <div style="font-size: 14px; color: #333;">童蕾</div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- II. 搬迁时间线 -->
            <div style="margin-bottom: 30px;">
                <div style="font-size: 16px; font-weight: 500; color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0;">
                    <span style="color: #888; margin-right: 10px;">II.</span>搬迁时间线
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px 15px; vertical-align: top; width: 20px;">
                            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #5a9;"></div>
                        </td>
                        <td style="padding: 10px 0;">
                            <div style="font-size: 12px; color: #888; margin-bottom: 3px;">即日起</div>
                            <div style="font-size: 14px; color: #333;">新系统正式上线，新老系统同时可用</div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 15px; vertical-align: top;">
                            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #f0ad4e;"></div>
                        </td>
                        <td style="padding: 10px 0;">
                            <div style="font-size: 12px; color: #888; margin-bottom: 3px;">搬迁周期内（一周）</div>
                            <div style="font-size: 14px; color: #333;">新老系统均可访问，如出现问题可从两个系统找回数据</div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 15px; vertical-align: top;">
                            <div style="width: 12px; height: 12px; border-radius: 50%; background-color: #e74c3c;"></div>
                        </td>
                        <td style="padding: 10px 0;">
                            <div style="font-size: 12px; color: #888; margin-bottom: 3px;">一周后</div>
                            <div style="font-size: 14px; color: #333;">老系统将正式关闭，请确保切换至新系统</div>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- III. 重要说明 -->
            <div style="margin-bottom: 30px;">
                <div style="font-size: 16px; font-weight: 500; color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0;">
                    <span style="color: #888; margin-right: 10px;">III.</span>重要说明
                </div>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th style="padding: 15px 10px; text-align: left; border-bottom: 1px solid #e0e0e0; font-size: 13px; color: #888; font-weight: 500;">事项</th>
                            <th style="padding: 15px 10px; text-align: left; border-bottom: 1px solid #e0e0e0; font-size: 13px; color: #888; font-weight: 500;">说明</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding: 15px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px; font-weight: 500; width: 120px;">1. 数据安全</td>
                            <td style="padding: 15px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px;">所有数据已完整迁移至新系统，无需手动操作</td>
                        </tr>
                        <tr>
                            <td style="padding: 15px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px; font-weight: 500;">2. 过渡期间</td>
                            <td style="padding: 15px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px;">一周内新老系统均可正常访问和使用</td>
                        </tr>
                        <tr>
                            <td style="padding: 15px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px; font-weight: 500;">3. 数据恢复</td>
                            <td style="padding: 15px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px;">过渡期内如遇问题，可从两个系统找回数据</td>
                        </tr>
                        <tr>
                            <td style="padding: 15px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px; font-weight: 500;">4. 系统关闭</td>
                            <td style="padding: 15px 10px; border-bottom: 1px solid #e0e0e0; font-size: 14px;">一周后老系统将永久关闭，请及时切换</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- 重要提示 -->
            <div style="background-color: #fff8e6; border-left: 4px solid #f0ad4e; padding: 15px 20px; margin: 25px 0; font-size: 14px; color: #8a6d3b;">
                <strong style="display: block; margin-bottom: 5px;">⚠️ 重要提示</strong>
                请在一周内完成向新系统的切换。一周后老系统将正式关闭，届时只能通过新系统访问。
            </div>

            <!-- IV. 新系统访问方式 -->
            <div style="margin-bottom: 30px;">
                <div style="font-size: 16px; font-weight: 500; color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #e0e0e0;">
                    <span style="color: #888; margin-right: 10px;">IV.</span>新系统访问方式
                </div>

                <!-- 二维码 -->
                <div style="text-align: center; margin: 30px 0;">
                    <div style="display: inline-block; padding: 15px; background-color: #fff; border: 1px solid #e0e0e0; margin-bottom: 10px;">
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://garbage-lottery-hanging-biological.trycloudflare.com" alt="新系统二维码" style="display: block; width: 150px; height: 150px;">
                    </div>
                    <div style="font-size: 13px; color: #888;">扫描二维码访问新系统（手机端）</div>
                </div>

                <p style="font-size: 13px; color: #888; margin-bottom: 10px;">如需复制链接，请使用以下地址：</p>
                <div style="background-color: #f8f8f8; padding: 15px; margin: 20px 0; word-break: break-all; font-size: 13px; color: #5a9; border: 1px solid #e0e0e0;">
                    https://garbage-lottery-hanging-biological.trycloudflare.com
                </div>
            </div>

            <!-- 联系人 -->
            <div style="background-color: #f8f9fa; padding: 20px; margin-top: 30px; text-align: center;">
                <p style="font-size: 14px; color: #666; margin: 0 0 5px 0;">使用过程中如有任何问题，请联系：</p>
                <div style="font-size: 16px; color: #333; font-weight: 600;">👤 童蕾</div>
            </div>
        </div>

        <!-- 页脚 -->
        <div style="text-align: center; padding: 25px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #999;">
            <p style="margin: 5px 0;">© 2025 PMA系统管理团队. All rights reserved.</p>
            <p style="margin: 5px 0;">此邮件由系统自动发送，请勿直接回复</p>
        </div>
    </div>
</body>
</html>'''


def send_test_email(email, real_name):
    """发送测试邮件给指定用户"""
    subject = "PMA系统搬迁通知 | System Migration Notice"
    html_content = get_email_html(real_name)
    text_content = f"""
亲爱的 {real_name}，你好！

为了给大家提供更好的服务体验，PMA系统将搬迁至新地址。

新系统地址：https://garbage-lottery-hanging-biological.trycloudflare.com

搬迁周期：一周（7天）
数据迁移状态：已完成迁移

重要提示：请在一周内完成向新系统的切换。一周后老系统将正式关闭。

如有问题请联系：童蕾

© 2025 PMA系统管理团队
"""

    print(f"正在发送测试邮件给 {real_name} ({email})...")
    result = send_email(
        subject=subject,
        recipient=email,
        content=text_content,
        html=html_content,
        async_send=False  # 同步发送，等待结果
    )

    if result:
        print(f"✅ 测试邮件发送成功！")
    else:
        print(f"❌ 测试邮件发送失败")

    return result


def send_to_all_active_users():
    """发送给所有激活用户"""
    active_users = User.query.filter(User.is_active == True).all()

    print(f"\n准备发送给 {len(active_users)} 个激活用户...")

    success_count = 0
    fail_count = 0

    for user in active_users:
        if not user.email:
            print(f"⚠️ 跳过 {user.username}：没有邮箱")
            continue

        subject = "PMA系统搬迁通知 | System Migration Notice"
        html_content = get_email_html(user.real_name or user.username)
        text_content = f"亲爱的 {user.real_name or user.username}，PMA系统将搬迁至新地址..."

        print(f"发送给 {user.real_name} ({user.email})...", end=" ")

        try:
            send_email(
                subject=subject,
                recipient=user.email,
                content=text_content,
                html=html_content,
                async_send=True  # 异步发送
            )
            print("✅")
            success_count += 1
        except Exception as e:
            print(f"❌ {e}")
            fail_count += 1

        # 避免发送过快被限流
        time.sleep(0.5)

    print(f"\n发送完成！成功: {success_count}, 失败: {fail_count}")


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        import argparse
        parser = argparse.ArgumentParser(description='发送PMA系统搬迁通知邮件')
        parser.add_argument('--test', action='store_true', help='只发送测试邮件给倪靖豪')
        parser.add_argument('--all', action='store_true', help='发送给所有激活用户')
        args = parser.parse_args()

        if args.test:
            # 发送测试邮件
            send_test_email("james98980566@gmail.com", "倪靖豪")
        elif args.all:
            # 发送给所有人
            send_to_all_active_users()
        else:
            print("用法:")
            print("  python send_migration_notice.py --test  # 发送测试邮件给倪靖豪")
            print("  python send_migration_notice.py --all   # 发送给所有激活用户")
