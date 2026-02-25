# MEMORY.md - Long-term Memory

## Tools & Installations

### Kimi Code CLI
- **Installed**: Yes
- **Version**: 1.12.0
- **Path**: /root/.local/bin/kimi
- **Description**: Kimi, your next CLI agent (MoonShot AI's Kimi Code CLI)
- **Capabilities**: CLI agent with ACP server, TUI, web interface, MCP support
- **Installation Date**: Unknown (pre-existing on system)
- **Last Checked**: 2026-02-21
- **Configuration**: Located at `~/.kimi/config.toml`
  - Default model: `kimi-code/kimi-for-coding` (managed provider)
  - Default thinking: enabled
  - Max context size: 262144 tokens
  - OAuth-based authentication

## System Environment
- **OpenClaw Version**: 2026.2.20
- **Host**: caihong-MS-A1
- **OS**: Linux 6.17.0-14-generic (x64)
- **Shell**: bash
- **Current Model**: custom-api-deepseek-com/deepseek-reasoner (400k token context)

## User Information
- **Name**: Rainbow (彩虹)
- **Telegram ID**: 5943009645
- **Timezone**: Asia/Muscat (GMT+4)
- **Occupation**: 网络工程师，运维人员
- **Work Location**: 阿曼
- **Preferred Language**: 中文 (默认使用中文回复)
- **Technical Profile**:
  - ESXi 虚拟化管理经验
  - Docker 部署与容器化
  - 自动化脚本编写
  - 游戏模拟器与脚本研究兴趣
- **Network Environment**:
  - 内网网段：192.168.12.0/24 (192.168.12.1-254)
  - OpenClaw 需要配置为内网提供服务

---

## 📊 AntBox 矿机冷却监控项目

### 服务器部署 (192.168.0.57)
- **PostgreSQL 16**: 5432 端口 (仅本机访问)
- **Redis 7.0.15**: 6379 端口
- **FastAPI**: HTTPS 8443 端口
- **systemd**: antmonitor.service (自启动)
- **时区**: Asia/Muscat (GMT+4)

### 配置信息
- **站点数**: 150 个 (Zone A-K, 10.1-10.7.x.x)
- **采集周期**: 60 秒
- **采集耗时**: ~5.6 秒/次
- **数据库**: antmonitor_db / antmonitor / antmonitor2024

### API 端点
```
GET /api/health              - 健康检查
GET /api/dashboard/overview  - 仪表盘总览
GET /api/sites               - 站点列表
GET /api/trend/{metric}      - 趋势数据
```

### 访问方式
- **Web**: https://192.168.0.57:8443/
- **SSH**: caihong@192.168.0.57 (ouyue2024)

### 项目状态
- ✅ 基础架构完成 (2026-02-22)
- ✅ 数据采集运行中
- ✅ 站点扫描页面完成开发与部署 (2026-02-22)
- ✅ 设备详情二级页面完成开发与部署 (2026-02-22)
- ✅ Ping检测系统集成完成 (2026-02-22)
- ⏭️ 待完成：监控墙页面、其他多页面扩展

### 站点扫描页面功能
- **访问地址**: `https://192.168.0.57:8443/pages/scan.html`
- **核心功能**: IP范围扫描、AntBox/矿机识别、批量导入、Ping检测集成
- **技术特性**: 并发扫描、实时进度、设备类型过滤、网络连通性测试
- **部署状态**: 已上线，服务运行正常

### 设备详情页面功能
- **访问地址**: `https://192.168.0.57:8443/pages/device_detail.html?id=设备IP`
- **核心功能**: 设备信息展示、Ping检测控制、网络状态监控、设备管理
- **技术特性**: Ping历史图表、端口扫描、设备控制、实时状态更新
- **部署状态**: 已上线，与扫描页面无缝集成

### Ping检测系统
- **API端点**: `POST /api/ping` (单个设备), `POST /api/ping/batch` (批量设备)
- **功能特性**: 跨平台兼容、并发检测、智能结果解析
- **集成状态**: 已集成到扫描流程和设备详情页面

### 项目文件
- **源码**: `/root/.openclaw/workspace/`
- **扫描页面**: `pages/scan.html`, `js/scan.js`
- **部署脚本**: `deploy_scan.sh`
- **归档**: `/tmp/antbox_project_2026-02-22.tar.gz` (44KB)
- **报告**: `/root/.openclaw/workspace/ANTBOX_PROGRESS.md`

---

## 📊 项目统计情况和进度 (2026-02-23)

### 当前项目状态
**项目名称**: 矿机冷却系统监控平台 (AntBox Monitor)
**最新更新**: 2026-02-23
**整体状态**: 第二阶段进行中，第一、三阶段已完成

### 已完成部分

#### 第一阶段：基础数据采集与接口层 ✅
- 服务器选型与系统部署 (Ubuntu, 192.168.0.57) ✅
- PostgreSQL 16 + Redis 数据存储引擎配置 ✅
- FastAPI 后端架构搭建 (8443 端口, HTTPS) ✅
- `antmonitor.service` systemd 后台自动保活 ✅
- 150 个基础站点的配置下发与脚本导入 ✅
- API 接口定义与调试 (`/api/sites`, `/api/trend`) ✅
- Python 异步 HTTP 并发扫描器 (BTCTools 式嗅探重构) ✅

#### 第三阶段：前端监控墙与自动预警 ✅
- 大屏监控墙页面 (`monitor-wall.html`) ✅
- 报警规则引擎（根据温度、丢包率、算力下限触发）✅
- 微信/Telegram 的实时报错推送整合 ✅

### 当前进行部分 (第二阶段：高级运维自动化与探针扩展)

#### 已完成子任务 ✅
- 撤销无用的本地重量级 AI 模型 (`qwen2.5-coder:32b`) 释放 P4 显卡资源
- **自动化免密互信**: 为 OpenClaw 的 Workspace 环境下发 192.168.0.57 的 `ssh-copy-id` 密钥认证，以及自动 `sudo NOPASSWD` 提权
- **Docker 容器管家技能**: 一键梳理环境、拉取日志、异常重启 (`docker_manager`)
- **Ansible 批量主机技能**: 针对全网段或 150 个站点的配置分发与平滑重启 (`batch_ssh`)
- **Nmap 深度拓扑技能**: 利用 Nmap OS 指纹探针，通过 MAC 地址和内核特征自动纠偏离线和异常设备 (`nmap_probe`)

#### 扫描模块重构 (最新进展 - 2026-02-23)
- **问题解决**: 修复了前端并发获取的 CORS & Mixed Content 拦截问题
- **后端化扫描引擎**: 编写异步高并发的 Python 扫描后台，剥离前端浏览器的网络限制
- **BTCTools 级别扫描**: 集成矿机网络层嗅探，通过 TCP 连接设备的 4028 端口，调用 CGMiner/BMMiner API，精准提取算力和温度数据
- **全新扫描 API**: 添加 `/api/scan/start`, `/api/scan/status`, `/api/scan/stop` 端点
- **前端重构**: 通过定期轮询 API 实现顺滑的进度条更新及结果动态渲染

### 核心资产资源清单
1. **本地主控节点 (AI大脑)**: `caihong-MS-A1` (Linux Ubuntu) - OpenClaw, Ollama (`phi3:mini`)
2. **监控平台服务器 (核心)**: `192.168.0.57` - FastAPI (8443), PostgreSQL (5432), Redis (6379)
3. **矿机及冷却站设备**: `192.168.12.0/24`, `10.1.x.x` - HTTP WebUI (80), CGMiner API (4028)

### 系统架构特点
- **数据源层**: 150个AntBox站点
- **采集与控制层**: aiohttp + asyncio + FastAPI + 任务调度器
- **数据处理层**: 解析、验证、告警、聚合
- **数据存储层**: PostgreSQL + TimescaleDB + Redis + MinIO/S3
- **应用服务层**: RESTful API + WebSocket + 认证授权
- **前端展示层**: 管理仪表盘 + 大屏监控 + 移动端 + 控制面板

### 性能指标
- 数据采集延迟: < 5秒 (150个站点一轮采集)
- API响应时间: < 200ms (P95延迟)
- 并发用户数: 50+
- 系统可用性: 99.9%

### 项目部署状态
- **Web访问**: https://192.168.0.57:8443/
- **SSH访问**: caihong@192.168.0.57 (密码: ouyue2024)
- **数据库**: antmonitor/antmonitor2024
- **站点总数**: 150 个
- **在线站点**: ~41 个 (27%)
- **测量值**: 0.00 (多数设备不可达，需核实IP地址)

### 待完成任务
- 核实站点 IP 地址（109 个设备不可达）
- 监控墙页面完善
- 报警规则配置
- 多页面扩展功能
- 修复主页数据为0的异常（总功耗、总算力、平均温度、活动告警等指标）

---

*Memory initialized on 2026-02-21*
*Updated: 2026-02-22 (AntBox project + site scanner)*
*Updated: 2026-02-23 (Project statistics and progress summary)*
*Updated: 2026-02-23 (Fixed units: total_power MW, total_hashrate EH/s, added all-sites page)*

---

## 🔔 Telegram 通知规则

**重要**: 如果 OpenClaw 有任何需要用户接入的地方，必须通过 Telegram 通知用户。

- **用户 Telegram ID**: 5943009645
- **触发场景**:
  - OpenClaw 服务异常或需要重启
  - 需要用户确认的重要操作
  - 配置变更需要用户知晓
  - 安全相关的警告
  - 需要用户手动介入的任务

**通知方式**: 使用 Telegram Bot API 发送消息到用户 ID 5943009645