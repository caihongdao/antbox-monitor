# MEMORY.md - Long-term Memory

## 🛠️ 软件编程与项目

### 📊 AntBox 矿机监控平台 (192.168.0.57)
- **环境**: Ubuntu, PostgreSQL 16, Redis, FastAPI (HTTPS 8443)
- **范围**: 10.1.x.x - 10.4.x.x (约 150 站点, 2026-03扫描确认10.1最稳定全在线)
- **状态**: 监控墙、站点扫描(并发Ping/4028提取)、视频监控模块已完成。
- **架构**: Python 异步采集，前后端分离，Telegram预警集成。

### 🦌 DeerFlow 2.0 (192.168.12.120)
- **环境**: Docker Compose (`/root/.openclaw/workspace/deer-flow`)
- **地址**: 0.0.0.0:2026 (网关 8001, 引擎 2024, Web 3000)
- **API集**: 聚合了 DeepSeek, Moonshot (Kimi), Dashscope (Qwen), Gemini。

### 🤖 OpenClaw 与 AI 配置
- **版本**: v2026.3.23-2 (升级于 2026-03-24)
- **模型**: 主力 `deepseek-reasoner` / `gemini-3.1-pro-preview` / `qwen3.5-plus`。
- **ACP Agents**: 已接入并默认分配 `kimi code` 和 `qwen code`。
- One API (192.168.12.120:3000) 统一管理 AI 通道。

## 🌐 网络工程与资产

- **内网网段**: 192.168.12.0/24 (阿曼, GMT+4时区)
- **核心路由**: 爱快 (192.168.12.254, **仅监控，修改必须经 TG 确认**)
- **核心计算节点**:
  - `192.168.12.120` (主节点/桌面, OpenClaw 1)
  - `192.168.12.100` (OpenClaw 2 - DeepSeek)
- **监控与虚拟化**:
  - PVE (192.168.0.220) / ESXi 8.0.3 (10.0.1.136)
  - Zabbix (192.168.0.100) / AntSentry (192.168.0.221-222)
- **DNS解析群**: 10.0.1.1, 10.0.2.1, 10.0.3.1, 10.0.4.1

## 👤 用户画像 (彩虹)
- **身份**: 网络工程师/运维 (TG ID: 5943009645)
- **偏好**: 偏好内网自动化、容器化及脚本治理，倾向于高效直接的中文反馈。操作敏感设备（如爱快路由）或OpenClaw服务必须预先发送 Telegram 通知。

## 🔐 设备凭据

### 网络设备 (华为交换机与Zabbix)
- **Zabbix (192.168.0.100)**:
  - 网页UI: `Admin` / `zabbix` (端口8080/API可用)
- **生产网络交换机 (Zone 1-4)**:
  - **登录方式**: Telnet (端口23)
  - **默认账号**: `admin`
  - **默认密码**: `admin@123`
  - **资产列表**:
    - **一区**: 172.16.1.1~8, 172.16.1.100
    - **二区**: 172.16.2.1~8, 172.16.2.100
    - **三区**: 172.16.3.1~4, 172.16.3.100
    - **四区**: 172.16.4.1~4, 172.16.4.100

### 矿机默认登录信息
- **设备类型**: Antminer 矿机 (Antminer S21e Hyd. 等)
- **默认账号**: `root`
- **默认密码**: `root`
- **登录页面**: `http://<miner_ip>/` 或 `http://<miner_ip>/#blog`
- **SN 获取方式**: 登录后访问日志页面，搜索 `sn :` 或 `Miner sn:` 提取
- **SN 格式**: 16 位大写字母 + 数字 (例：`JYZZGBUBEJDBB02FG`)
- **型号提取**: 日志中搜索 `type: Antminer` 或 `型号 Antminer`
## 📋 标准操作流程 (SOP)

### 矿机批量掉线与零算力排查恢复流程
**适用场景**: 矿机在监控平台大面积离线，或网络在线但持续零算力。

#### 1. 网络层排查 (华为 S5735S 三层交换机)
- **现象特征**: 交换机 `display arp` 存在大量 `Incomplete`；`display logbuffer` 频繁提示内部网关 IP 触发 `ARP Attack` (如 `The specified source IP address attack occurred`)。
- **根因分析**: AntBox 等监控中心的高频轮询扫描 (约 75 pps) 误触了交换机的防攻击保护机制 (auto-defend / anti-attack)，导致正常网关的 ARP 报文被底层丢弃，无法与矿机建立映射。
- **恢复命令**:
  ```text
  <Switch> system-view
  [Switch] acl 2000
  [Switch-acl-basic-2000] rule 10 permit source 10.4.0.0 0.0.255.255
  [Switch-acl-basic-2000] quit
  # 提升全局源 IP ARP 限制阈值
  [Switch] arp speed-limit source-ip maximum 150
  [Switch] arp-miss speed-limit source-ip maximum 150
  [Switch] quit
  # 清理僵死缓存让网关重新学习矿机 MAC (必做)
  <Switch> reset arp dynamic
  <Switch> save
  ```

#### 2. 矿机硬件层排查 (在线但零算力)
- **现象特征**: 网络可达，管理后台或监控端在线，但算力长时间为 0.0 GH/s。
- **诊断手段**: 绕过前端 UI，直接请求矿机 `4028` 端口的 API (发送 `{"command":"stats"}` 和 `{"command":"pools"}`)，避免盲目重启和无效抓包。
- **指标定性**:
  - **矿池状态**: 若 `POOLS` 返回 `Status: Alive` 且 `Stratum Active: True`，说明网络和矿池侧业务通讯**完全正常，无需抓包诊断网络**。
  - **芯片识别**: 若 `STATS` 中 `total_acn` 数值完整 (如 S19 XP Hyd 为 612)，说明算力板物理芯片通信正常。
  - **自保状态**: 若 `TempMax=0` (或空白)、风扇状态为 `None`、持续重启 (`Elapsed` 运行时间极短)，说明触发了**矿机环境自保停机**。
- **处理结论**: 此类零算力极大概率为现场物理环境异常（如水冷 CDU 水流量不足、入水温度超阈值等），应立即指派运维人员赴现场检查物理水冷和散热系统。
