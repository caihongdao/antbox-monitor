#!/bin/bash
# 批量 SSH / Ansible 封装技能：针对 150 个站点的配置下发、状态重置、服务重启实现“一键指令化”。

TARGETS=$1
CMD=$2

if [ -z "$TARGETS" ] || [ -z "$CMD" ]; then
    echo "用法: ./batch_ssh.sh <IP或网段/主机组, 如 192.168.12.0/24> '<需要执行的命令>'"
    echo "依赖: nmap 用于存活扫描 (针对网段), parallel 用于并发执行"
    exit 1
fi

echo "=== 正在获取存活主机列表: $TARGETS ==="
if [[ "$TARGETS" == *"/"* ]]; then
    # 扫描网段内的 22 端口存活主机
    LIVE_HOSTS=$(nmap -n -p 22 --open -T4 $TARGETS | grep "Nmap scan report for" | awk '{print $5}')
else
    # 直接指定的单个IP或逗号分隔的IP
    LIVE_HOSTS=$(echo $TARGETS | tr ',' '\n')
fi

if [ -z "$LIVE_HOSTS" ]; then
    echo "未发现任何开放 22 端口的主机。"
    exit 1
fi

echo "=== 发现存活节点: $(echo "$LIVE_HOSTS" | wc -l) 台 ==="
echo "=== 执行命令: $CMD ==="

# 准备并发脚本
cat << 'EOF' > /tmp/run_ssh.sh
#!/bin/bash
IP=$1
CMD=$2
echo "[+] $IP: 执行开始"
sshpass -p "ouyue2024" ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no root@$IP "$CMD" > /tmp/ssh_result_$IP.log 2>&1
if [ $? -eq 0 ]; then
    echo "✓ $IP: 成功"
else
    echo "✗ $IP: 失败/超时"
fi
cat /tmp/ssh_result_$IP.log | sed 's/^/    /'
rm /tmp/ssh_result_$IP.log
EOF
chmod +x /tmp/run_ssh.sh

# 如果机器没有 parallel，则用简单的 shell 并发
command -v parallel >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "$LIVE_HOSTS" | parallel -j 20 /tmp/run_ssh.sh {} "$CMD"
else
    for IP in $LIVE_HOSTS; do
        /tmp/run_ssh.sh $IP "$CMD" &
    done
    wait
fi

echo "=== 批量任务执行完毕 ==="