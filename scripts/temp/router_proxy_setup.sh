#!/bin/sh
# 路由器透明代理配置脚本
# 用法: 在路由器上执行此脚本
# SSH 到路由器后: sh router_proxy_setup.sh

echo "=========================================="
echo "路由器透明代理配置脚本"
echo "=========================================="

# 检查依赖
echo "[1/5] 检查已安装的软件包..."
if ! opkg list-installed | grep -q stunnel; then
    echo "错误: stunnel 未安装"
    exit 1
fi

if ! opkg list-installed | grep -q redsocks; then
    echo "错误: redsocks 未安装"
    exit 1
fi

echo "stunnel 和 redsocks 已安装"

# 配置 stunnel
echo "[2/5] 配置 stunnel..."
mkdir -p /etc/stunnel

cat > /etc/stunnel/stunnel.conf << 'EOF'
; stunnel 配置 - 连接 Cloudflare Tunnel
; 将 TLS 连接转换为本地明文 TCP

pid = /var/run/stunnel.pid
setuid = nobody
setgid = nogroup

[socks-proxy]
client = yes
accept = 127.0.0.1:1080
connect = proxy.jamesgpone.win:443
EOF

echo "stunnel 配置完成"

# 配置 redsocks
echo "[3/5] 配置 redsocks..."
cat > /etc/redsocks.conf << 'EOF'
base {
    log_debug = off;
    log_info = on;
    log = "syslog:daemon";
    daemon = on;
    redirector = iptables;
}

redsocks {
    local_ip = 0.0.0.0;
    local_port = 12345;
    ip = 127.0.0.1;
    port = 1080;
    type = socks5;
}
EOF

echo "redsocks 配置完成"

# 配置 iptables
echo "[4/5] 配置 iptables 透明代理规则..."

# 清理旧规则（如果存在）
iptables -t nat -D PREROUTING -i br-lan -p tcp -j REDSOCKS 2>/dev/null
iptables -t nat -F REDSOCKS 2>/dev/null
iptables -t nat -X REDSOCKS 2>/dev/null

# 创建 REDSOCKS 链
iptables -t nat -N REDSOCKS

# 排除本地和内网地址
iptables -t nat -A REDSOCKS -d 0.0.0.0/8 -j RETURN
iptables -t nat -A REDSOCKS -d 10.0.0.0/8 -j RETURN
iptables -t nat -A REDSOCKS -d 127.0.0.0/8 -j RETURN
iptables -t nat -A REDSOCKS -d 169.254.0.0/16 -j RETURN
iptables -t nat -A REDSOCKS -d 172.16.0.0/12 -j RETURN
iptables -t nat -A REDSOCKS -d 192.168.0.0/16 -j RETURN
iptables -t nat -A REDSOCKS -d 224.0.0.0/4 -j RETURN
iptables -t nat -A REDSOCKS -d 240.0.0.0/4 -j RETURN

# 重定向 TCP 到 redsocks
iptables -t nat -A REDSOCKS -p tcp -j REDIRECT --to-ports 12345

# 应用到局域网流量
iptables -t nat -A PREROUTING -i br-lan -p tcp -j REDSOCKS

echo "iptables 规则配置完成"

# 启动服务
echo "[5/5] 启动服务..."

# 停止现有服务
/etc/init.d/stunnel stop 2>/dev/null
/etc/init.d/redsocks stop 2>/dev/null

# 启动 stunnel
/etc/init.d/stunnel start
if [ $? -eq 0 ]; then
    echo "stunnel 启动成功"
    /etc/init.d/stunnel enable
else
    echo "stunnel 启动失败"
    exit 1
fi

# 启动 redsocks
/etc/init.d/redsocks start
if [ $? -eq 0 ]; then
    echo "redsocks 启动成功"
    /etc/init.d/redsocks enable
else
    echo "redsocks 启动失败"
    exit 1
fi

echo ""
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "验证步骤："
echo "1. 检查服务状态: ps | grep -E 'stunnel|redsocks'"
echo "2. 检查端口监听: netstat -tlnp | grep -E '1080|12345'"
echo "3. 从局域网设备测试: curl -v https://www.google.com"
echo ""
echo "如需禁用透明代理："
echo "  iptables -t nat -D PREROUTING -i br-lan -p tcp -j REDSOCKS"
echo ""
