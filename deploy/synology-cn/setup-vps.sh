#!/bin/bash
# VPS 端一键部署脚本
# 部署 FRP 服务器 + Nginx 反向代理 + Let's Encrypt HTTPS
# 适用于 Ubuntu 22.04 / Debian 12 / CentOS 8+
# 用法: curl -sL https://your-domain/setup-vps.sh | bash
#   或: bash setup-vps.sh

set -e

# ============ 配置区域（部署前请修改） ============

# 你的域名（已解析到 VPS IP）
DOMAIN="${DOMAIN:-pma.yourdomain.com}"

# FRP 认证 token（与 NAS 端 frpc.toml 一致）
FRP_TOKEN="${FRP_TOKEN:-YOUR_FRP_AUTH_TOKEN}"

# FRP Dashboard 密码
FRP_DASHBOARD_PASSWORD="${FRP_DASHBOARD_PASSWORD:-admin123}"

# FRP 版本
FRP_VERSION="${FRP_VERSION:-0.61.1}"

# Let's Encrypt 邮箱
CERT_EMAIL="${CERT_EMAIL:-your-email@example.com}"

# PMA 端口（FRP 映射到 VPS 的端口）
PMA_PORT=5001

# ============ 颜色输出 ============

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ============ 检查 root 权限 ============

if [ "$EUID" -ne 0 ]; then
    error "请使用 root 用户运行: sudo bash setup-vps.sh"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA VPS 部署脚本${NC}"
echo -e "${GREEN}  FRP + Nginx + HTTPS${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "域名: $DOMAIN"
echo "FRP 版本: $FRP_VERSION"
echo "PMA 端口: $PMA_PORT"
echo ""

# ============ Step 1: 安装依赖 ============

info "[1/6] 安装系统依赖..."

if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq nginx certbot python3-certbot-nginx wget tar ufw
elif command -v yum &> /dev/null; then
    yum install -y -q nginx certbot python3-certbot-nginx wget tar firewalld
else
    error "不支持的操作系统，需要 apt-get 或 yum"
fi

# ============ Step 2: 安装 FRP 服务端 ============

info "[2/6] 安装 FRP 服务端 v${FRP_VERSION}..."

FRP_DIR="/opt/frp"
mkdir -p "$FRP_DIR"

ARCH=$(uname -m)
case "$ARCH" in
    x86_64) FRP_ARCH="amd64" ;;
    aarch64) FRP_ARCH="arm64" ;;
    *) error "不支持的架构: $ARCH" ;;
esac

FRP_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_${FRP_ARCH}.tar.gz"

info "下载 FRP: $FRP_URL"
wget -q -O /tmp/frp.tar.gz "$FRP_URL"
tar -xzf /tmp/frp.tar.gz -C /tmp/
cp /tmp/frp_${FRP_VERSION}_linux_${FRP_ARCH}/frps "$FRP_DIR/"
chmod +x "$FRP_DIR/frps"
rm -rf /tmp/frp*

# 写入 FRP 服务端配置
cat > "$FRP_DIR/frps.toml" << EOF
# FRP v0.50+ TOML 格式
bindPort = 7000

auth.token = "$FRP_TOKEN"

log.to = "/var/log/frps.log"
log.level = "info"
log.maxDays = 7

webServer.addr = "127.0.0.1"
webServer.port = 7500
webServer.user = "admin"
webServer.password = "$FRP_DASHBOARD_PASSWORD"

allowPorts = [
    { start = 5001, end = 5010 },
    { start = 8080, end = 8090 }
]
EOF

# 创建 systemd 服务
cat > /etc/systemd/system/frps.service << EOF
[Unit]
Description=FRP Server
After=network.target

[Service]
Type=simple
ExecStart=$FRP_DIR/frps -c $FRP_DIR/frps.toml
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable frps
systemctl start frps

info "FRP 服务端已启动"

# ============ Step 3: 配置 Nginx 反向代理 ============

info "[3/6] 配置 Nginx 反向代理..."

cat > /etc/nginx/sites-available/pma << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Let's Encrypt 验证
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # 临时 HTTP 反向代理（HTTPS 配置后会被 certbot 修改）
    location / {
        proxy_pass http://127.0.0.1:$PMA_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;

        # 文件上传大小限制
        client_max_body_size 50M;
    }
}
EOF

# 启用站点
ln -sf /etc/nginx/sites-available/pma /etc/nginx/sites-enabled/pma

# 删除默认站点（如果存在）
rm -f /etc/nginx/sites-enabled/default

# 测试并重载 Nginx
nginx -t && systemctl reload nginx

info "Nginx 反向代理已配置"

# ============ Step 4: 配置防火墙 ============

info "[4/6] 配置防火墙..."

if command -v ufw &> /dev/null; then
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw allow 7000/tcp  # FRP
    ufw allow 22/tcp    # SSH
    ufw --force enable
    info "UFW 防火墙已配置"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=80/tcp
    firewall-cmd --permanent --add-port=443/tcp
    firewall-cmd --permanent --add-port=7000/tcp
    firewall-cmd --reload
    info "Firewalld 防火墙已配置"
fi

# ============ Step 5: 申请 HTTPS 证书 ============

info "[5/6] 申请 Let's Encrypt HTTPS 证书..."

if [ "$DOMAIN" = "pma.yourdomain.com" ]; then
    warn "域名未修改，跳过 HTTPS 证书申请"
    warn "请修改 DOMAIN 变量后手动执行:"
    warn "  certbot --nginx -d $DOMAIN --email $CERT_EMAIL --agree-tos --no-eff-email"
else
    certbot --nginx -d "$DOMAIN" --email "$CERT_EMAIL" --agree-tos --no-eff-email --non-interactive || {
        warn "HTTPS 证书申请失败，可能是域名未解析到此 VPS"
        warn "请确认 DNS 解析后手动执行:"
        warn "  certbot --nginx -d $DOMAIN --email $CERT_EMAIL --agree-tos --no-eff-email"
    }
fi

# 设置证书自动续期
systemctl enable certbot.timer 2>/dev/null || true

# ============ Step 6: 验证 ============

info "[6/6] 验证部署..."

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  VPS 部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "FRP 服务端状态:"
systemctl status frps --no-pager -l 2>/dev/null | head -5
echo ""
echo "Nginx 状态:"
systemctl status nginx --no-pager -l 2>/dev/null | head -5
echo ""
echo -e "${GREEN}配置信息:${NC}"
echo "  FRP 监听端口: 7000"
echo "  FRP Dashboard: http://127.0.0.1:7500 (admin / $FRP_DASHBOARD_PASSWORD)"
echo "  FRP Token: $FRP_TOKEN"
echo "  PMA 外网地址: https://$DOMAIN"
echo "  PMA FRP 端口: $PMA_PORT"
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo "  1. 确认域名 $DOMAIN 已解析到本 VPS IP"
echo "  2. 在 DS925+ 的 frpc.toml 中填写本 VPS 地址和 Token"
echo "  3. 启动 DS925+ 的 FRP 客户端"
echo "  4. 访问 https://$DOMAIN 验证"
echo ""
echo -e "${YELLOW}常用命令:${NC}"
echo "  查看 FRP 日志: tail -f /var/log/frps.log"
echo "  重启 FRP: systemctl restart frps"
echo "  重启 Nginx: systemctl restart nginx"
echo "  续期证书: certbot renew"
echo "  查看证书到期: certbot certificates"
