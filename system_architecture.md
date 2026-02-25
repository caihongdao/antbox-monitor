# 矿机冷却系统监控平台 - 系统架构设计

## 总体架构图

```mermaid
graph TB
    subgraph "数据源层 (150个AntBox站点)"
        A1[站点1: 10.1.101.1]
        A2[站点2: 10.1.102.1]
        A3[...]
        A150[站点150: 10.2.150.1]
        
        V1[视频流1: HLS]
        V2[视频流2: HLS]
        V150[视频流150: HLS]
    end

    subgraph "采集与控制层"
        B1[数据采集服务<br/>aiohttp + asyncio]
        B2[控制命令服务<br/>FastAPI端点]
        B3[视频代理服务<br/>FFmpeg + nginx-rtmp]
        B4[任务调度器<br/>Celery + Redis]
        
        B1 --> C[(Redis<br/>消息队列)]
        B2 --> C
        B4 --> C
    end

    subgraph "数据处理层"
        D1[数据解析器<br/>JSON → 结构化]
        D2[数据验证器<br/>范围检查]
        D3[告警引擎<br/>规则匹配]
        D4[数据聚合器<br/>统计计算]
    end

    subgraph "数据存储层"
        E1[(PostgreSQL + TimescaleDB<br/>时序数据)]
        E2[(Redis<br/>缓存与会话)]
        E3[(MinIO/S3<br/>视频存储可选)]
        
        D1 --> E1
        D2 --> E1
        D3 --> E1
        D4 --> E1
    end

    subgraph "应用服务层"
        F1[RESTful API<br/>FastAPI]
        F2[WebSocket服务<br/>实时更新]
        F3[认证授权<br/>JWT + OAuth2]
        F4[报表服务<br/>PDF/Excel导出]
    end

    subgraph "前端展示层"
        G1[管理仪表盘<br/>Vue.js/React]
        G2[大屏监控<br/>全屏可视化]
        G3[移动端适配<br/>响应式设计]
        G4[控制面板<br/>实时控制]
    end

    subgraph "外部集成"
        H1[短信网关<br/>告警通知]
        H2[邮件服务<br/>SMTP]
        H3[微信/钉钉<br/>企业通知]
        H4[第三方API<br/>对接]
    end

    %% 数据流向
    A1 --> B1
    A2 --> B1
    A150 --> B1
    
    V1 --> B3
    V150 --> B3
    
    B1 --> D1
    C --> B4
    
    F1 --> G1
    F2 --> G1
    F3 --> G1
    
    D3 --> H1
    D3 --> H2
    D3 --> H3
    
    G4 --> B2
```

## 组件详细说明

### 1. 数据采集服务 (Data Collector)
- **技术栈**: Python aiohttp + asyncio
- **并发能力**: 150个站点并发采集，约5秒完成一轮
- **采集频率**: 可配置，默认60秒/次
- **容错机制**:
  - 连接超时处理（3秒超时）
  - 重试机制（最大3次）
  - 断点续传
  - 数据完整性验证

### 2. 控制命令服务 (Control Service)
- **协议**: RESTful API over HTTPS
- **命令队列**: Redis队列保证顺序执行
- **状态跟踪**: 每个命令有唯一ID，可查询执行状态
- **权限控制**: 基于角色的访问控制（RBAC）
- **审计日志**: 所有控制操作入库

### 3. 视频代理服务 (Video Proxy)
- **功能**: 代理HLS流，避免前端直接访问内网IP
- **技术**: nginx-rtmp-module + FFmpeg转码
- **特性**:
  - 实时转码（支持多种分辨率）
  - 访问控制（Token验证）
  - 带宽限制
  - 录制功能（可选）

### 4. 任务调度器 (Task Scheduler)
- **框架**: Celery + Redis作为Broker
- **任务类型**:
  - 定期数据采集
  - 告警检查
  - 数据清理
  - 报表生成
- **监控**: Flower监控任务状态

### 5. 数据存储设计
#### 5.1 PostgreSQL + TimescaleDB
- **主数据库**: 存储配置、用户、控制日志
- **时序数据库**: 状态快照（高性能时间序列查询）
- **分区策略**: 按时间分片（1天/片）
- **压缩策略**: 7天后压缩，节省存储空间

#### 5.2 Redis
- **用途**: 缓存、会话存储、消息队列
- **数据结构**:
  - Hash: 站点最新状态缓存
  - List: 命令队列
  - Set: 在线用户会话
  - Sorted Set: 告警优先级队列

### 6. 告警引擎 (Alert Engine)
- **规则引擎**: 支持复杂条件组合
- **告警级别**: 紧急、严重、警告、信息
- **通知渠道**: 邮件、短信、微信、钉钉
- **告警抑制**: 避免重复告警
- **自动恢复**: 条件恢复后自动清除告警

### 7. 前端架构
#### 7.1 技术栈
- **框架**: Vue 3 + TypeScript 或 React + TypeScript
- **状态管理**: Pinia 或 Redux Toolkit
- **UI组件库**: Element Plus 或 Ant Design
- **图表库**: ECharts 或 Apache ECharts
- **地图**: 可选，用于站点地理位置展示

#### 7.2 页面结构
1. **总览仪表盘** - 关键指标KPI、告警摘要、地图视图
2. **站点详情** - 单个站点的详细数据、历史趋势、控制面板
3. **实时监控** - 视频流网格展示（4×4、9×9布局）
4. **告警中心** - 告警列表、处理、统计
5. **报表中心** - 能效分析、运行报告、导出功能
6. **系统管理** - 用户管理、权限配置、系统设置

### 8. 安全设计
- **认证**: JWT Token + Refresh Token
- **授权**: RBAC（管理员、操作员、查看员）
- **网络隔离**: 前端通过API网关访问，不直连内网
- **数据加密**: HTTPS传输，敏感数据加密存储
- **审计日志**: 所有操作记录，不可篡改

## 部署架构

### 开发环境
```yaml
version: '3.8'
services:
  postgres:
    image: timescale/timescaledb:latest-pg14
  redis:
    image: redis:7-alpine
  api:
    build: ./backend
    depends_on: [postgres, redis]
  collector:
    build: ./collector
    depends_on: [redis]
  frontend:
    build: ./frontend
```

### 生产环境
- **高可用部署**: Kubernetes集群
- **负载均衡**: Nginx/Traefik
- **数据库**: PostgreSQL主从复制 + TimescaleDB集群
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack（Elasticsearch, Logstash, Kibana）

## 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 数据采集延迟 | < 5秒 | 150个站点一轮采集时间 |
| API响应时间 | < 200ms | P95延迟 |
| 并发用户数 | 50+ | 同时在线操作 |
| 数据存储 | 90天 | 原始数据保留时间 |
| 系统可用性 | 99.9% | SLA目标 |

## 扩展性考虑

1. **水平扩展**: 采集服务可部署多个实例，通过Redis队列分配任务
2. **分片存储**: 站点数据可按区域分片存储
3. **插件架构**: 支持自定义数据处理器、告警规则
4. **API开放**: 提供OpenAPI文档，支持第三方集成

## 下一步实施计划

1. **第一阶段（2周）**: 基础架构搭建
   - 数据库部署与初始化
   - 数据采集服务原型
   - 基础API开发

2. **第二阶段（3周）**: 核心功能开发
   - 完整数据采集与存储
   - 基础前端仪表盘
   - 告警引擎

3. **第三阶段（2周）**: 控制与视频功能
   - 控制命令服务
   - 视频代理服务
   - 控制面板

4. **第四阶段（1周）**: 测试与优化
   - 性能测试
   - 安全测试
   - 用户体验优化

## 参考设计
- **类似系统**: 工业SCADA系统、IDC监控系统
- **设计原则**: 实时性、可靠性、可扩展性
- **用户体验**: 大屏友好、操作直观、响应迅速