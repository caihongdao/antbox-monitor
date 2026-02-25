#!/bin/bash
# 部署站点扫描页面和设备详情页面到服务器

SERVER="192.168.0.57"
USER="caihong"
PASS="ouyue2024"
REMOTE_DIR="/home/caihong/antmonitor"

echo "=== 开始部署增强版扫描系统 ==="

# 创建远程目录结构
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$SERVER << EOF
    mkdir -p $REMOTE_DIR/pages
    mkdir -p $REMOTE_DIR/css
    mkdir -p $REMOTE_DIR/js
    mkdir -p $REMOTE_DIR/assets
EOF

echo "✓ 创建远程目录结构"

# 1. 上传页面与静态文件
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/pages/scan.html $USER@$SERVER:$REMOTE_DIR/pages/
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/pages/device_detail.html $USER@$SERVER:$REMOTE_DIR/pages/
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/js/scan_backend.js $USER@$SERVER:$REMOTE_DIR/js/
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/js/device_detail.js $USER@$SERVER:$REMOTE_DIR/js/

echo "✓ 上传静态资源"

# 2. 上传后端Python模块
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/ping_detection.py $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/scanner_module.py $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/update_api_server.py $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/inject_scan.py $USER@$SERVER:$REMOTE_DIR/

echo "✓ 上传后端脚本"

# 3. 更新CSS样式
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$SERVER \
    "if [ -f $REMOTE_DIR/css/styles.css ]; then \
        cp $REMOTE_DIR/css/styles.css $REMOTE_DIR/css/styles.css.backup; \
    fi; \
    cat > $REMOTE_DIR/css/styles.css << 'STYLES_END'
$(cat /root/.openclaw/workspace/css/styles.css)
STYLES_END"

echo "✓ 更新CSS样式"

# 4. 更新API服务器，添加Ping端点和Scan端点
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$SERVER << EOF
    cd $REMOTE_DIR
    cp api_server.py api_server.py.backup.$(date +%Y%m%d_%H%M%S)
    
    if python3 update_api_server.py api_server.py; then
        echo "Ping API端点更新成功"
    fi
    
    if python3 inject_scan.py api_server.py; then
        echo "Scan API端点更新成功"
    else
        echo "API服务器更新失败，使用备份恢复"
        cp api_server.py.backup.* api_server.py 2>/dev/null || true
    fi
EOF

echo "✓ 更新API服务器"

# 5. 更新dashboard导航
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$SERVER \
    "if [ -f $REMOTE_DIR/dashboard.html ] && ! grep -q '站点扫描' $REMOTE_DIR/dashboard.html; then \
        sed -i '/全部站点列表/a\                <a href=\"pages/scan.html\"><i class=\"fas fa-search\"></i> 站点扫描</a>' $REMOTE_DIR/dashboard.html; \
    fi"

echo "✓ 更新dashboard导航"

# 6. 重启服务
echo "重启监控服务..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$SERVER "echo '$PASS' | sudo -S systemctl restart antmonitor.service"
sleep 3

echo "=== 部署完成 ==="
echo ""
echo "🌐 访问地址:"
echo "1. 站点扫描页面: https://$SERVER:8443/pages/scan.html"
echo "2. 设备详情页面: https://$SERVER:8443/pages/device_detail.html?id=设备IP"
