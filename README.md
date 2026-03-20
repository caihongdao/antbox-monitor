# AntBox Monitor - 矿机冷却系统监控平台

一个基于 FastAPI + PostgreSQL + Redis 的矿机冷却系统监控平台，用于监控 AntBox 设备的运行状态、温度、功耗等关键指标。

## 项目特点

- **实时监控**: 监控 150+ 矿机站点，60秒采集周期
- **前端面板**: 响应式 Web 界面，支持实时监控和历史趋势
- **设备扫描**: 自动扫描和识别 AntBox/矿机设备
- **Ping 检测**: 集成网络连通性检测
- **数据存储**: PostgreSQL + TimescaleDB + Redis 多层存储
- **告警系统**: 根据温度、功耗、算力等指标触发告警

## 系统架构

```
数据源层 (150个 AntBox 站点)
    ↓
采集与控制层 (FastAPI + aiohttp + asyncio)
    ↓
数据处理层 (解析、验证、告警、聚合)
    ↓
数据存储层 (PostgreSQL + TimescaleDB + Redis)
    ↓
应用服务层 (RESTful API + WebSocket)
    ↓
前端展示层 (Web 仪表盘 + 监控大屏)
```

## 技术栈

- **后端**: Python 3.10+, FastAPI, PostgreSQL, Redis
- **前端**: HTML5, CSS3, JavaScript (原生)
- **部署**: systemd, Docker (可选)
- **协议**: RESTful API, WebSocket

## 主要功能

### 1. 站点扫描
- IP 范围扫描
- AntBox/矿机自动识别
- 批量导入站点
- Ping 检测集成

访问地址: `/pages/scan.html`

### 2. 设备详情
- 设备信息展示
- Ping 历史图表
- 端口扫描
- 实时状态更新

访问地址: `/pages/device_detail.html?id={设备IP}`

### 3. 监控大屏
- 实时数据总览
- 关键指标监控
- 告警状态展示

访问地址: `/pages/monitor-wall.html`

### 4. 视频监控
- 多路视频流监控
- HLS/RTSP 支持
- 自动重连

访问地址: `/pages/jiankongqiang.html`

## API 端点

```
GET  /api/health              - 健康检查
GET  /api/dashboard/overview  - 仪表盘总览
GET  /api/sites               - 站点列表
POST /api/ping                - 单个设备 Ping 检测
POST /api/ping/batch          - 批量设备 Ping 检测
GET  /api/trend/{metric}      - 趋势数据
POST /api/scan/start          - 开始扫描
GET  /api/scan/status         - 扫描状态
POST /api/scan/stop           - 停止扫描
```

## 快速开始

### 环境要求

- Python 3.10+
- PostgreSQL 16+
- Redis 7.0+
- Node.js 16+ (前端构建)

### 安装步骤

1. 克隆项目
```bash
git clone https://github.com/caihongdao/antbox-monitor.git
cd antbox-monitor
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置数据库
```bash
# 创建 PostgreSQL 数据库
createdb antmonitor_db

# 执行数据库迁移
# (根据实际配置文件)
```

4. 配置 Redis
```bash
# 确保 Redis 服务已启动
redis-server
```

5. 配置应用
```bash
cp config.example.json config.json
# 编辑 config.json 填写数据库和 Redis 配置
```

6. 启动应用
```bash
python main.py
# 或使用 systemd 服务
systemctl start antmonitor.service
```

7. 访问 Web 界面
```
http://localhost:8443/pages/monitor-wall.html
```

### 使用 Docker 部署

```bash
# 构建镜像
docker build -t antbox-monitor .

# 启动容器
docker-compose up -d
```

## 配置文件

### 站点配置

站点配置文件位于 `config/sites.json`:

```json
{
  "sites": [
    {
      "zone": "A",
      "ip": "10.1.101.1",
      "name": "AntBox-A-01",
      "type": "antbox"
    }
  ]
}
```

### 告警规则

告警规则配置示例:

```json
{
  "alerts": [
    {
      "name": "高温告警",
      "metric": "temperature",
      "threshold": 80,
      "comparison": ">",
      "channels": ["telegram", "wechat"]
    }
  ]
}
```

## 系统服务

### 使用 systemd 管理

```bash
# 启动服务
sudo systemctl start antmonitor

# 开机自启
sudo systemctl enable antmonitor

# 查看状态
sudo systemctl status antmonitor

# 查看日志
journalctl -u antmonitor -f
```

服务文件: `antmonitor.service`

## 开发

### 项目结构

```
antbox-monitor/
├── main.py                 # 主应用入口
├── antbox_collector.py     # 数据采集器
├── config/                 # 配置文件
├── pages/                  # Web 页面
├── js/                     # JavaScript 文件
├── css/                    # 样式文件
├── api/                    # API 模块
├── database/               # 数据库模块
├── utils/                  # 工具函数
├── tests/                  # 测试文件
├── requirements.txt        # Python 依赖
└── README.md              # 项目说明
```

### 添加新功能

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 性能指标

- 数据采集延迟: < 5秒 (150个站点一轮采集)
- API响应时间: < 200ms (P95延迟)
- 并发用户数: 50+
- 系统可用性: 99.9%

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- 感谢所有贡献者的支持
- 基于 FastAPI 和 Vue.js 构建

## 联系方式

项目地址: https://github.com/caihongdao/antbox-monitor

---

**注意**: 本项目仅供学习和研究使用，请遵守当地法律法规。
