#!/bin/bash
# Nmap 拓扑探针技能：接管“未知设备”的系统指纹识别，进行深度扫描。

TARGET=$1

if [ -z "$TARGET" ]; then
    echo "用法: ./nmap_probe.sh <IP/网段>"
    echo "示例: ./nmap_probe.sh 192.168.0.50"
    exit 1
fi

echo "=== 启动 Nmap 深度拓扑探针探测: $TARGET ==="
echo "执行参数: -sV (服务/版本探测) -O (操作系统指纹) --osscan-guess (强制猜测)"
echo "警告: 此扫描可能会花费 30 秒至几分钟时间。"

sudo nmap -sV -O --osscan-guess -T4 -p 22,80,443,4028,8443 $TARGET | grep -E "^Nmap scan report|^PORT|^STATE|^SERVICE|^VERSION|^MAC Address|^Device type|^Running|^OS details|^Network Distance"

echo "=== 探针任务完成 ==="