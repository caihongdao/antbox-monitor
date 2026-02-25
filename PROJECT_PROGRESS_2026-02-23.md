# 矿机冷却系统监控平台项目 - 进度与架构重构表 (2026-02-23)

## 📌 项目里程碑

### 第一阶段：基础数据采集与接口层 (已完成)
- [x] 服务器选型与系统部署 (Ubuntu, 192.168.0.57)
- [x] PostgreSQL + Redis 数据存储引擎配置
- [x] FastAPI 后端架构搭建 (8443 端口, HTTPS)
- [x] `antmonitor.service` systemd 后台自动保活
- [x] 150 个基础站点的配置下发与脚本导入
- [x] API 接口定义与调试 (`/api/sites`, `/api/trend`)
- [x] Python 异步 HTTP 并发扫描器 (BTCTools 式嗅探重构)

### 第二阶段：高级运维自动化与探针扩展 (当前进行中)
- [x] 撤销无用的本地重量级 AI 模型 (`qwen2.5-coder:32b`) 释放 P4 显卡资源，专项提供纯代码推理和小模型过滤脱敏功能。
- [x] **自动化免密互信**：为 OpenClaw 的 Workspace 环境下发 192.168.0.57 的 `ssh-copy-id` 密钥认证，以及自动 `sudo NOPASSWD` 提权。
- [x] **Docker 容器管家技能**：一键梳理环境、拉取日志、异常重启 (`docker_manager`)
- [x] **Ansible 批量主机技能**：针对全网段或 150 个站点的配置分发与平滑重启 (`batch_ssh`)
- [x] **Nmap 深度拓扑技能**：利用 Nmap OS 指纹探针，通过 MAC 地址和内核特征自动纠偏离线和异常设备 (`nmap_probe`)

### 第三阶段：前端监控墙与自动预警 (已完成)
- [x] 大屏监控墙页面 (`monitor-wall.html`)
- [x] 报警规则引擎（根据温度、丢包率、算力下限触发）
- [x] 微信/Telegram 的实时报错推送整合

---

## 💻 核心资产资源清单

### 1. 服务资源矩阵
| 角色名称 | IP 地址 | 系统/型号 | 核心服务 | 账号 | 凭证与权限 |
|----------|---------|-----------|----------|------|------------|
| **本地主控节点 (AI大脑)** | `caihong-MS-A1` | Linux (Ubuntu) | OpenClaw, Ollama (`phi3:mini`) | `root` | 已拥有最高控制权 |
| **监控平台服务器 (核心)** | `192.168.0.57` | Linux (Ubuntu) | FastAPI (8443), PostgreSQL (5432), Redis (6379) | `caihong` | 密码：`ouyue2024`<br>免密：**已完成 SSH-Key 互信**<br>提权：**已配置 NOPASSWD sudo** |
| **矿机及冷却站设备** | `192.168.12.0/24`<br>`10.1.x.x` | ASIC, AntBox 控制器 | HTTP WebUI (80), CGMiner API (4028) | `-` | 使用 API 和并发探针获取 |

### 2. 自动化扩展命令 (内建)
我已经为你编写并安装了三个强力探针脚本，可以直接调用：
- **容器管理**: `/root/.openclaw/workspace/tools/docker_manager.sh <list|logs|restart> [容器名]`
- **批量部署**: `/root/.openclaw/workspace/tools/batch_ssh.sh <网段/主机组> <命令>`
- **Nmap 拓扑**: `/root/.openclaw/workspace/tools/nmap_probe.sh <IP/网段>`
