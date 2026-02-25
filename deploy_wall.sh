#!/bin/bash
# 部署第三阶段：大屏监控墙与告警推送

SERVER="192.168.0.57"
USER="caihong"
PASS="ouyue2024"
REMOTE_DIR="/home/caihong/antmonitor"

echo "=== 开始部署大屏监控墙与告警引擎 ==="

# 1. 上传页面与JS
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/pages/monitor-wall.html $USER@$SERVER:$REMOTE_DIR/pages/
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/js/monitor-wall.js $USER@$SERVER:$REMOTE_DIR/js/

echo "✓ 上传监控墙前端文件 (HTML/JS)"

# 2. 上传告警推送模块
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/alert_notifier.py $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /root/.openclaw/workspace/inject_notifier.py $USER@$SERVER:$REMOTE_DIR/

# 创建配置文件目录
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$SERVER "mkdir -p $REMOTE_DIR/config"

echo "✓ 上传告警引擎后端文件"

# 3. 在服务器执行代码注入并重启
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$SERVER << EOF
    cd $REMOTE_DIR
    
    # 备份并注入告警推送逻辑
    cp api_server.py api_server.py.backup_alerts.$(date +%Y%m%d_%H%M%S)
    if python3 inject_notifier.py api_server.py; then
        echo "✓ 告警推送代码注入成功"
    else
        echo "✗ 代码注入失败，回滚..."
        cp api_server.py.backup_alerts.* api_server.py
    fi
    
    # 重启服务
    echo "$PASS" | sudo -S systemctl restart antmonitor.service
EOF

echo "✓ 重启后端服务"

# 4. 更新dashboard导航
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $USER@$SERVER \
    "if [ -f $REMOTE_DIR/dashboard.html ] && ! grep -q '监控墙' $REMOTE_DIR/dashboard.html; then \
        sed -i '/站点扫描/a\                <a href=\"pages/monitor-wall.html\"><i class=\"fas fa-tv\"></i> 监控墙</a>' $REMOTE_DIR/dashboard.html; \
    fi"

echo "=== 部署完成 ==="
echo ""
echo "🖥️  监控墙访问地址: https://$SERVER:8443/pages/monitor-wall.html"
echo "🚨  Telegram 告警模块已默认安装。如需开启，请编辑 $SERVER 上的 $REMOTE_DIR/config/alert_config.json"
