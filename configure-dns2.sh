#!/bin/bash
#
# Ubuntu 虚拟机网络配置脚本
# 用于将 DNS1-Ubuntu-server (dns1, 10.0.1.1) 克隆机修改为 dns2 (10.0.2.1/24)
#
# 使用前请确认：
# 1. 已克隆虚拟机并启动
# 2. 已登录到新虚拟机（建议使用控制台或SSH）
# 3. 以 root 用户或 sudo 执行此脚本
#
# 修改以下变量以适应你的环境
#

# 新网络配置
NEW_IP="10.0.2.1"
NEW_PREFIX="24"
NEW_GATEWAY="10.0.2.254"
NEW_HOSTNAME="dns2"

# 原主机名（用于替换 /etc/hosts）
OLD_HOSTNAME="dns1"

# 网络接口名称（如果不知道，脚本可以尝试自动检测）
# 如果自动检测不正确，请手动设置 INTERFACE="你的网卡名"（如 ens160, eth0 等）
INTERFACE=""

# Netplan 配置文件路径（如果使用 netplan）
NETPLAN_FILE=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 root 权限
if [[ $EUID -ne 0 ]]; then
   log_error "此脚本需要 root 权限执行"
   log_error "请使用: sudo $0"
   exit 1
fi

# 备份函数
backup_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        cp "$file" "${file}.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "已备份 $file"
    fi
}

# 自动检测网络接口（如果未手动指定）
if [[ -z "$INTERFACE" ]]; then
    log_info "正在自动检测默认网络接口..."
    INTERFACE=$(ip route show default | awk '{print $5}' | head -n1)
    if [[ -z "$INTERFACE" ]]; then
        log_error "无法自动检测网络接口，请手动设置 INTERFACE 变量"
        exit 1
    fi
    log_info "检测到网络接口: $INTERFACE"
fi

# 自动检测 Netplan 配置文件（如果未手动指定）
if [[ -z "$NETPLAN_FILE" ]]; then
    log_info "正在查找 Netplan 配置文件..."
    NETPLAN_FILE=$(find /etc/netplan -name "*.yaml" -o -name "*.yml" | head -n1)
    if [[ -z "$NETPLAN_FILE" ]]; then
        log_warn "未找到 Netplan 配置文件，可能使用其他网络管理方式"
        log_warn "请手动设置 NETPLAN_FILE 变量或修改脚本"
    else
        log_info "找到 Netplan 配置文件: $NETPLAN_FILE"
    fi
fi

log_info "开始配置新虚拟机..."
log_info "新 IP: ${NEW_IP}/${NEW_PREFIX}"
log_info "新网关: ${NEW_GATEWAY}"
log_info "新主机名: ${NEW_HOSTNAME}"
log_info "网络接口: ${INTERFACE}"

echo
read -p "确认以上配置? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    log_error "用户取消操作"
    exit 1
fi

# 备份重要文件
log_info "备份系统配置文件..."
backup_file "/etc/hostname"
backup_file "/etc/hosts"
if [[ -n "$NETPLAN_FILE" ]]; then
    backup_file "$NETPLAN_FILE"
fi

# 1. 修改主机名
log_info "修改主机名..."
echo "$NEW_HOSTNAME" > /etc/hostname
hostnamectl set-hostname "$NEW_HOSTNAME"

# 2. 更新 /etc/hosts
log_info "更新 /etc/hosts..."
sed -i "s/\b${OLD_HOSTNAME}\b/${NEW_HOSTNAME}/g" /etc/hosts
# 确保 localhost 条目存在
if ! grep -q "127.0.0.1.*localhost" /etc/hosts; then
    echo "127.0.0.1 localhost" >> /etc/hosts
fi
if ! grep -q "::1.*localhost" /etc/hosts; then
    echo "::1 localhost" >> /etc/hosts
fi

# 3. 配置网络
if [[ -n "$NETPLAN_FILE" ]]; then
    log_info "配置 Netplan..."
    # 创建新的 netplan 配置
    cat > "$NETPLAN_FILE" << EOF
network:
  version: 2
  ethernets:
    $INTERFACE:
      addresses:
        - ${NEW_IP}/${NEW_PREFIX}
      routes:
        - to: default
          via: ${NEW_GATEWAY}
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
EOF
    
    log_info "应用 Netplan 配置..."
    netplan apply
    log_info "Netplan 配置已应用"
else
    log_warn "未使用 Netplan，请手动配置网络"
    log_warn "接口: $INTERFACE"
    log_warn "IP: $NEW_IP/$NEW_PREFIX"
    log_warn "网关: $NEW_GATEWAY"
fi

# 4. 重启网络服务（如果 netplan apply 已处理则不需要）
if [[ -z "$NETPLAN_FILE" ]]; then
    log_info "尝试重启网络服务..."
    if systemctl is-active --quiet NetworkManager; then
        systemctl restart NetworkManager
    elif systemctl is-active --quiet networking; then
        systemctl restart networking
    fi
fi

# 5. 验证配置
log_info "验证配置..."
echo
echo "=== 当前主机名 ==="
hostname
echo
echo "=== 网络接口配置 ==="
ip addr show "$INTERFACE" | grep inet
echo
echo "=== 路由表 ==="
ip route show default
echo
echo "=== 解析测试 ==="
ping -c 1 google.com >/dev/null 2>&1 && echo "互联网连接: OK" || echo "互联网连接: 失败"

log_info "配置完成！"
log_info "建议重启系统以确保所有更改生效: reboot"
log_info "备份文件位于:"
find /etc -name "*.backup.*" -type f 2>/dev/null

echo
log_warn "注意：如果 SSH 连接使用 IP 地址，可能需要重新连接"
log_warn "新 IP 地址: $NEW_IP"