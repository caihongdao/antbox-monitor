#!/bin/bash
# Docker 容器管家技能：一键梳理 PostgreSQL、Redis 等环境，支持日志拉取和异常重启。

SERVER="192.168.0.57"
USER="caihong"

ACTION=$1
TARGET=$2

if [ -z "$ACTION" ]; then
    echo "用法: ./docker_manager.sh <list|logs|restart> [容器名/服务名]"
    echo "注意: 默认管理 192.168.0.57 上的 Docker/Systemd 服务"
    exit 1
fi

case $ACTION in
    list)
        echo "=== 系统服务状态 (antmonitor / redis / postgresql) ==="
        ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "sudo systemctl status antmonitor.service | grep 'Active:'; sudo systemctl status redis-server | grep 'Active:'; sudo systemctl status postgresql | grep 'Active:'"
        echo "=== Docker 容器状态 ==="
        ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "sudo docker ps -a" 2>/dev/null || echo "Docker 未安装或无容器运行。"
        ;;
    logs)
        if [ -z "$TARGET" ]; then
            echo "错误: 请指定目标服务名 (例如: antmonitor.service 或 docker容器名)"
            exit 1
        fi
        echo "=== 拉取 $TARGET 最新 100 行日志 ==="
        if [[ "$TARGET" == *".service" ]]; then
            ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "sudo journalctl -u $TARGET -n 100 --no-pager"
        else
            ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "sudo docker logs --tail 100 $TARGET" 2>/dev/null || echo "无法获取 $TARGET 日志。"
        fi
        ;;
    restart)
        if [ -z "$TARGET" ]; then
            echo "错误: 请指定目标服务名 (例如: antmonitor.service 或 docker容器名)"
            exit 1
        fi
        echo "=== 正在重启 $TARGET ==="
        if [[ "$TARGET" == *".service" ]]; then
            ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "sudo systemctl restart $TARGET"
            echo "已重启 systemd 服务: $TARGET"
        else
            ssh -o StrictHostKeyChecking=no ${USER}@${SERVER} "sudo docker restart $TARGET" 2>/dev/null || echo "无法重启 Docker 容器 $TARGET。"
            echo "已重启容器: $TARGET"
        fi
        ;;
    *)
        echo "未知操作: $ACTION"
        ;;
esac