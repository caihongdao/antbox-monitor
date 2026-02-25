-- 矿机冷却系统监控平台数据库Schema
-- 使用PostgreSQL 14+ 或 TimescaleDB（时序数据优化）
-- 字符集：UTF8，时区：UTC

-- 1. 站点信息表（存储150个AntBox容器的基本信息）
CREATE TABLE sites (
    site_id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL UNIQUE,          -- 站点IP地址，如 10.1.102.1
    hostname VARCHAR(128),                    -- 可选的设备主机名
    location VARCHAR(256),                    -- 物理位置描述
    model VARCHAR(64) DEFAULT 'AntBox',       -- 设备型号
    firmware_version VARCHAR(32),             -- 固件版本
    last_seen TIMESTAMPTZ,                    -- 最后通信时间
    is_online BOOLEAN DEFAULT FALSE,          -- 当前在线状态
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 索引
    INDEX idx_sites_ip (ip_address),
    INDEX idx_sites_online (is_online)
);

-- 2. 状态快照表（时序数据，使用TimescaleDB超表）
CREATE TABLE status_snapshots (
    snapshot_id BIGSERIAL,
    site_id INTEGER NOT NULL REFERENCES sites(site_id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- 冷却系统参数
    supply_temp NUMERIC(5,2),                 -- 供液温度 (°C)
    return_temp NUMERIC(5,2),                 -- 回液温度 (°C)
    target_temp NUMERIC(5,2),                 -- 设定温度 (°C)
    flow_rate NUMERIC(8,2),                   -- 流量 (L/min)
    pressure NUMERIC(8,2),                    -- 压力 (kPa)
    compressor_speed NUMERIC(6,2),            -- 压缩机转速 (%)
    fan_speed NUMERIC(6,2),                   -- 风机转速 (%)
    
    -- 电力参数
    total_power NUMERIC(10,2),                -- 总功耗 (KW)
    power_factor NUMERIC(4,3),                -- 功率因数
    voltage NUMERIC(8,2),                     -- 电压 (V)
    current NUMERIC(8,2),                     -- 电流 (A)
    energy_consumption NUMERIC(12,2),         -- 累计能耗 (KWh)
    
    -- 矿机集群参数
    miner_count INTEGER,                      -- 矿机数量
    total_hashrate NUMERIC(12,2),             -- 总算力 (PH/s)
    efficiency NUMERIC(8,2),                  -- 能效比 (J/T)
    avg_miner_temp NUMERIC(5,2),              -- 平均矿机温度 (°C)
    
    -- 环境参数
    ambient_temp NUMERIC(5,2),                -- 环境温度 (°C)
    ambient_humidity NUMERIC(5,2),            -- 环境湿度 (%)
    cabinet_temp NUMERIC(5,2),                -- 机柜温度 (°C)
    
    -- 状态标志
    fault_flags INTEGER DEFAULT 0,            -- 故障标志位图
    warning_flags INTEGER DEFAULT 0,          -- 警告标志位图
    operation_mode VARCHAR(32),               -- 运行模式：cooling/heating/idle
    
    -- 元数据
    data_source VARCHAR(16) DEFAULT 'api',    -- 数据来源：api/manual/estimated
    collection_duration INTEGER,              -- 采集耗时 (ms)
    
    PRIMARY KEY (snapshot_id, timestamp)
);

-- 转换为TimescaleDB超表（如果使用TimescaleDB）
-- SELECT create_hypertable('status_snapshots', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- 索引
CREATE INDEX idx_snapshots_site_time ON status_snapshots(site_id, timestamp DESC);
CREATE INDEX idx_snapshots_timestamp ON status_snapshots(timestamp DESC);

-- 3. 矿机详情表（每台矿机的详细信息）
CREATE TABLE miner_details (
    miner_id BIGSERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(site_id) ON DELETE CASCADE,
    miner_index INTEGER NOT NULL,             -- 矿机在集群中的索引 (0-188)
    mac_address MACADDR,                      -- 矿机MAC地址
    ip_address INET,                          -- 矿机IP地址
    
    -- 硬件信息
    model VARCHAR(64) DEFAULT 'Antminer S19 XP Hyd.', -- 型号
    firmware_version VARCHAR(32),             -- 矿机固件版本
    pcb_version VARCHAR(32),                  -- PCB版本
    hashboard_count INTEGER DEFAULT 3,        -- 算力板数量
    
    -- 运行状态
    hashrate NUMERIC(10,2),                   -- 算力 (GH/s)
    temperature NUMERIC(5,2),                 -- 温度 (°C)
    fan_speed INTEGER,                        -- 风扇转速 (RPM)
    power NUMERIC(8,2),                       -- 功耗 (W)
    voltage NUMERIC(6,2),                     -- 电压 (V)
    current NUMERIC(6,2),                     -- 电流 (A)
    
    -- 状态标志
    is_online BOOLEAN DEFAULT FALSE,
    has_error BOOLEAN DEFAULT FALSE,
    error_code VARCHAR(32),
    
    -- 时间戳
    last_update TIMESTAMPTZ DEFAULT NOW(),
    
    -- 唯一约束
    UNIQUE(site_id, miner_index),
    
    -- 索引
    INDEX idx_miners_site (site_id),
    INDEX idx_miners_online (is_online),
    INDEX idx_miners_error (has_error)
);

-- 4. 控制日志表（记录所有控制操作）
CREATE TABLE control_logs (
    log_id BIGSERIAL PRIMARY KEY,
    site_id INTEGER NOT NULL REFERENCES sites(site_id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- 操作信息
    operation VARCHAR(32) NOT NULL,           -- 操作类型：power_on/power_off/reset/set_temperature/...
    target_param VARCHAR(64),                 -- 目标参数（如temperature）
    old_value TEXT,                           -- 操作前值
    new_value TEXT,                           -- 操作后值
    
    -- 执行状态
    status VARCHAR(16) DEFAULT 'pending',     -- pending/success/failed/timeout
    response_code INTEGER,                    -- HTTP响应码
    response_message TEXT,                    -- 响应消息
    
    -- 执行者信息
    initiated_by VARCHAR(64) DEFAULT 'system',-- system/user:<username>/api
    user_agent TEXT,                          -- 用户代理（如果是Web请求）
    session_id VARCHAR(128),                  -- 会话ID
    
    -- 索引
    INDEX idx_control_logs_site (site_id),
    INDEX idx_control_logs_time (timestamp DESC),
    INDEX idx_control_logs_operation (operation),
    INDEX idx_control_logs_status (status)
);

-- 5. 视频会话表（管理视频流访问）
CREATE TABLE video_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id INTEGER NOT NULL REFERENCES sites(site_id) ON DELETE CASCADE,
    user_id VARCHAR(64),                      -- 用户标识（可为空）
    
    -- 流信息
    stream_url TEXT NOT NULL,                 -- 视频流URL
    proxy_url TEXT,                           -- 代理后的URL（后端代理）
    resolution VARCHAR(16) DEFAULT '720p',    -- 分辨率
    frame_rate INTEGER DEFAULT 30,            -- 帧率
    
    -- 会话状态
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 使用统计
    total_duration INTEGER DEFAULT 0,         -- 总时长（秒）
    bandwidth_usage BIGINT DEFAULT 0,         -- 带宽使用（字节）
    
    -- 索引
    INDEX idx_video_sessions_site (site_id),
    INDEX idx_video_sessions_active (is_active),
    INDEX idx_video_sessions_started (started_at DESC)
);

-- 6. 报警规则表（配置报警条件）
CREATE TABLE alert_rules (
    rule_id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    
    -- 报警条件
    metric_name VARCHAR(64) NOT NULL,         -- 指标名称：supply_temp/total_power/...
    condition_type VARCHAR(16) NOT NULL,      -- 条件类型：gt/lt/eq/change
    threshold_value NUMERIC(10,2),            -- 阈值
    duration_seconds INTEGER DEFAULT 300,     -- 持续时长（秒）
    
    -- 报警动作
    severity VARCHAR(16) DEFAULT 'warning',   -- critical/warning/info
    action_type VARCHAR(32),                  -- 动作类型：email/webhook/control
    action_params JSONB,                      -- 动作参数
    
    -- 状态
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 索引
    INDEX idx_alert_rules_enabled (is_enabled)
);

-- 7. 报警记录表
CREATE TABLE alert_records (
    record_id BIGSERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alert_rules(rule_id) ON DELETE SET NULL,
    site_id INTEGER REFERENCES sites(site_id) ON DELETE CASCADE,
    
    -- 报警详情
    metric_name VARCHAR(64),
    metric_value NUMERIC(10,2),
    threshold_value NUMERIC(10,2),
    condition_description TEXT,
    
    -- 状态
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    status VARCHAR(16) DEFAULT 'active',      -- active/acknowledged/resolved
    
    -- 处理信息
    acknowledged_by VARCHAR(64),
    resolution_notes TEXT,
    
    -- 索引
    INDEX idx_alert_records_site (site_id),
    INDEX idx_alert_records_status (status),
    INDEX idx_alert_records_triggered (triggered_at DESC)
);

-- 8. 用户与权限表（简单版本）
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(128),
    email VARCHAR(256),
    
    -- 认证
    password_hash VARCHAR(256),               -- bcrypt哈希
    api_token VARCHAR(64) UNIQUE,             -- API访问令牌
    last_login TIMESTAMPTZ,
    
    -- 权限
    role VARCHAR(16) DEFAULT 'viewer',        -- admin/operator/viewer
    permissions JSONB DEFAULT '{}',           -- 额外权限
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 索引
    INDEX idx_users_username (username),
    INDEX idx_users_role (role)
);

-- 视图：最新状态视图
CREATE OR REPLACE VIEW latest_site_status AS
SELECT DISTINCT ON (s.site_id)
    s.site_id,
    s.ip_address,
    s.location,
    s.is_online,
    ss.timestamp as last_update,
    ss.supply_temp,
    ss.return_temp,
    ss.total_power,
    ss.miner_count,
    ss.total_hashrate,
    ss.efficiency,
    ss.fault_flags,
    ss.warning_flags
FROM sites s
LEFT JOIN status_snapshots ss ON s.site_id = ss.site_id
ORDER BY s.site_id, ss.timestamp DESC;

-- 函数：更新站点最后在线时间
CREATE OR REPLACE FUNCTION update_site_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sites 
    SET last_seen = NOW(), 
        is_online = TRUE,
        updated_at = NOW()
    WHERE site_id = NEW.site_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 触发器：当插入状态快照时更新站点在线状态
CREATE TRIGGER trigger_update_site_status
AFTER INSERT ON status_snapshots
FOR EACH ROW
EXECUTE FUNCTION update_site_last_seen();

-- 初始化数据：插入示例站点（实际需要导入150个IP）
-- INSERT INTO sites (ip_address, location) VALUES 
-- ('10.1.101.1', 'Zone A, Rack 1'),
-- ('10.1.102.1', 'Zone A, Rack 2'),
-- ...;

-- 创建TimescaleDB压缩策略（如果使用TimescaleDB）
-- SELECT add_compression_policy('status_snapshots', INTERVAL '7 days');

-- 创建数据保留策略
-- SELECT add_retention_policy('status_snapshots', INTERVAL '90 days');

COMMENT ON TABLE sites IS 'AntBox容器站点信息';
COMMENT ON TABLE status_snapshots IS '冷却系统状态时序数据';
COMMENT ON TABLE miner_details IS '单个矿机详细信息';
COMMENT ON TABLE control_logs IS '控制操作日志';
COMMENT ON TABLE video_sessions IS '视频流会话管理';
COMMENT ON TABLE alert_rules IS '报警规则配置';
COMMENT ON TABLE alert_records IS '报警历史记录';