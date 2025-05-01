#!/bin/bash

# 邮件发送配置
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SENDER_EMAIL=your-email@gmail.com
# 如果使用Gmail，请使用应用专用密码，而非账户密码
export SENDER_PASSWORD=your-app-password

# 启动应用
python run.py 