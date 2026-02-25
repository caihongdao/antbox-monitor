# OpenClaw 运维扩展技能集

本项目为“矿机冷却监控平台”专属定制的扩展技能集，均已部署在 `/root/.openclaw/workspace/tools/` 目录下。作为 AI Agent，我已经掌握这些技能的使用方式，无需用户确认即可直接通过 `exec` 调用它们进行自动化运维。

## 1. 🐳 Docker 容器管家技能 (`docker_manager.sh`)
**功能定位**: 一键梳理 `192.168.0.57` 的 PostgreSQL、Redis 等环境状态，支持日志拉取和异常重启。
**内部实现**: 基于已互信的 SSH 证书（`~/.ssh/id_ed25519`），通过免密 `sudo` 调用 `systemctl` 和 `docker`。
**命令格式**:
```bash
/root/.openclaw/workspace/tools/docker_manager.sh <list|logs|restart> [容器名/服务名]
```
- 示例：`./docker_manager.sh list` (列出关键服务状态)
- 示例：`./docker_manager.sh logs antmonitor.service` (拉取监控系统报错日志)

## 2. ⚡ 批量 SSH / Ansible 封装技能 (`batch_ssh.sh`)
**功能定位**: 针对 150 个站点的配置下发、状态重置、服务重启实现“一键指令化”。
**内部实现**: 基于 `sshpass` 和 Bash 的底层并发协程，自动忽略死机或不在线的设备，仅向 22 端口开放的机器并行推送命令。
**命令格式**:
```bash
/root/.openclaw/workspace/tools/batch_ssh.sh <IP或网段/主机组, 如 192.168.12.0/24> '<需要执行的命令>'
```
- 示例：`./batch_ssh.sh 192.168.12.0/24 "reboot"` (批量重启在线矿机控制台)

## 3. 🔍 Nmap 拓扑探针技能 (`nmap_probe.sh`)
**功能定位**: 结合扫描页，用更底层的 Nmap OS 探针技能接管“未知设备”的系统指纹识别。
**内部实现**: 调用 `nmap -O -sV --osscan-guess` 进行深度服务版本嗅探和 TCP/IP 栈特征指纹匹配。
**命令格式**:
```bash
/root/.openclaw/workspace/tools/nmap_probe.sh <IP/网段>
```
- 示例：`./nmap_probe.sh 192.168.12.50` (探测具体未识别设备是路由器、交换机还是矿机控制板)
