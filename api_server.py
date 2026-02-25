#!/usr/bin/env python3
"""
AntBox 矿机冷却系统监控平台 - FastAPI 后端服务
提供数据采集、查询 API 和报警检测功能
"""

import asyncio
import asyncpg
import aiohttp
import json
import logging
from alert_notifier import notify_all
import ssl
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============= 配置 =============
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "antmonitor",
    "password": "antmonitor2024",
    "database": "antmonitor_db"
}

# 站点配置
SITES_CONFIG_PATH = "config/all_sites.json"

# 数据采集配置
COLLECTION_INTERVAL = 60  # 秒
API_TIMEOUT = 5  # 秒
MAX_CONCURRENT_REQUESTS = 50

# ============= 数据模型 =============
class SiteStatus(BaseModel):
    site_id: int
    ip_address: str
    location: Optional[str]
    is_online: bool
    last_update: Optional[datetime]
    supply_temp: Optional[float]
    return_temp: Optional[float]
    total_power: Optional[float]
    total_hashrate: Optional[float]
    miner_count: Optional[int]

class AlertRecord(BaseModel):
    record_id: int
    site_id: Optional[int]
    metric_name: Optional[str]
    metric_value: Optional[float]
    threshold_value: Optional[float]
    status: str
    triggered_at: datetime
    acknowledged_at: Optional[datetime]

class DashboardOverview(BaseModel):
    total_sites: int
    online_sites: int
    offline_sites: int
    active_alerts: int
    total_power: Optional[float]
    total_hashrate: Optional[float]
    avg_supply_temp: Optional[float]

# ============= 全局变量 =============
db_pool: Optional[asyncpg.Pool] = None
data_collector: Optional["DataCollector"] = None
collection_task: Optional[asyncio.Task] = None

# ============= 生命周期管理 =============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global db_pool, data_collector, collection_task
    
    try:
        # 启动时初始化
        logger.info("正在初始化数据库连接池...")
        db_pool = await asyncpg.create_pool(**DB_CONFIG, min_size=2, max_size=10)
        
        # 测试连接
        async with db_pool.acquire() as conn:
            await conn.fetchval('SELECT 1')
        logger.info("数据库连接池初始化完成，连接测试成功")
        
        # 初始化数据采集器
        logger.info("正在初始化数据采集器...")
        data_collector = DataCollector()
        logger.info(f"数据采集器初始化完成，加载了 {len(data_collector.sites)} 个站点")
        
        # 启动后台数据采集任务
        logger.info("正在启动后台数据采集任务...")
        collection_task = asyncio.create_task(background_data_collection())
        logger.info("后台数据采集任务已启动")
        
    except Exception as e:
        logger.error(f"初始化失败：{e}")
        raise
    
    yield
    
    # 关闭时清理
    logger.info("正在关闭数据库连接池...")
    if db_pool:
        await db_pool.close()
    
    if collection_task:
        collection_task.cancel()
        try:
            await collection_task
        except asyncio.CancelledError:
            pass
    
    logger.info("应用已正常关闭")

# ============= FastAPI 应用 =============
app = FastAPI(
    title="AntBox 监控系统 API",
    description="矿机冷却系统监控平台后端 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（前端页面）
@app.get("/")
async def root_page():
    """根路径返回仪表盘页面"""
    return FileResponse("dashboard.html")

@app.get("/dashboard")
async def dashboard_page():
    """仪表盘页面"""
    return FileResponse("dashboard.html")

# ============= 数据采集器 =============
class DataCollector:
    """异步数据采集器"""
    
    def __init__(self):
        self.sites: List[Dict[str, Any]] = []
        self.api_endpoints: Dict[str, str] = {}
        self.load_config()
    
    def load_config(self):
        """加载站点配置"""
        try:
            with open(SITES_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.sites = config.get("sites", [])
            self.api_endpoints = config.get("api_endpoints", {})
            logger.info(f"加载了 {len(self.sites)} 个站点配置")
        except Exception as e:
            logger.error(f"加载站点配置失败：{e}")
    
    async def fetch_site_data(self, session: aiohttp.ClientSession, site: Dict[str, Any]) -> Dict[str, Any]:
        """采集单个站点数据"""
        ip = site["ip"]
        result = {
            "ip": ip,
            "location": site.get("location", ""),
            "timestamp": datetime.utcnow(),
            "data": {},
            "errors": []
        }
        
        # 并发获取所有 API 端点
        tasks = []
        for endpoint_name, endpoint_path in self.api_endpoints.items():
            url = f"http://{ip}{endpoint_path}"
            tasks.append(self.fetch_endpoint(session, url, endpoint_name, ip))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for endpoint_name, res in zip(self.api_endpoints.keys(), results):
            if isinstance(res, Exception):
                result["errors"].append(f"{endpoint_name}: {str(res)}")
            else:
                result["data"][endpoint_name] = res
        
        return result
    
    async def fetch_endpoint(self, session: aiohttp.ClientSession, url: str, 
                            endpoint_name: str, ip: str) -> Dict[str, Any]:
        """获取单个 API 端点数据"""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok") is not None:
                        return {"status": "success", "data": data}
                    else:
                        return {"status": "invalid_format", "data": data}
                else:
                    return {"status": "http_error", "code": response.status}
        except asyncio.TimeoutError:
            raise TimeoutError(f"请求 {ip} 超时")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"连接 {ip} 失败：{str(e)}")
    
    async def collect_all_sites(self) -> List[Dict[str, Any]]:
        """采集所有站点数据"""
        connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.fetch_site_data(session, site) for site in self.sites]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        collected = []
        for site, result in zip(self.sites, results):
            if isinstance(result, Exception):
                collected.append({
                    "ip": site["ip"],
                    "errors": [str(result)],
                    "status": "failed"
                })
            else:
                collected.append(result)
        
        return collected

# ============= 后台数据采集任务 =============
async def background_data_collection():
    """后台数据采集循环任务"""
    logger.info("后台数据采集任务已启动")
    
    while True:
        try:
            start_time = datetime.utcnow()
            logger.info(f"开始数据采集周期 (预计采集 {len(data_collector.sites)} 个站点)")
            
            # 采集数据
            collected_data = await data_collector.collect_all_sites()
            
            # 保存到数据库
            await save_to_database(collected_data)
            
            # 检查报警
            await check_alerts()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"数据采集完成，耗时 {duration:.2f} 秒")
            
            # 等待下一个采集周期
            sleep_time = max(0, COLLECTION_INTERVAL - duration)
            await asyncio.sleep(sleep_time)
            
        except asyncio.CancelledError:
            logger.info("数据采集任务被取消")
            break
        except Exception as e:
            logger.error(f"数据采集周期出错：{e}")
            await asyncio.sleep(10)  # 出错后等待 10 秒

async def save_to_database(collected_data: List[Dict[str, Any]]):
    """将采集数据保存到数据库"""
    if not db_pool:
        return
    
    async with db_pool.acquire() as conn:
        for site_data in collected_data:
            try:
                ip = site_data.get("ip")
                if not ip:
                    continue
                
                # 获取或创建站点记录
                site = await conn.fetchrow(
                    "SELECT site_id FROM sites WHERE ip_address = $1", ip
                )
                
                if not site:
                    site_id = await conn.fetchval(
                        "INSERT INTO sites (ip_address, location, is_online) VALUES ($1, $2, $3) RETURNING site_id",
                        ip, site_data.get("location", ""), True
                    )
                else:
                    site_id = site["site_id"]
                    # 更新在线状态
                    await conn.execute(
                        "UPDATE sites SET is_online = $1, last_seen = NOW() WHERE site_id = $2",
                        len(site_data.get("errors", [])) == 0, site_id
                    )
                
                # 保存状态快照
                data = site_data.get("data", {})
                if "coolerState" in data and data["coolerState"].get("status") == "success":
                    params = data["coolerState"]["data"].get("params", {})
                    await conn.execute(
                        """INSERT INTO status_snapshots 
                           (site_id, supply_temp, return_temp, flow_rate, pressure, 
                            compressor_speed, fan_speed, operation_mode)
                           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                        site_id,
                        params.get("supply_temp"),
                        params.get("return_temp"),
                        params.get("flow_rate"),
                        params.get("pressure"),
                        params.get("compressor_speed"),
                        params.get("fan_speed"),
                        params.get("operation_mode")
                    )
                
                logger.debug(f"站点 {ip} 数据已保存")
                
            except Exception as e:
                logger.error(f"保存站点 {ip} 数据失败：{e}")

async def check_alerts():
    """检查报警规则"""
    if not db_pool:
        return
    
    async with db_pool.acquire() as conn:
        # 获取启用的报警规则
        rules = await conn.fetch("SELECT * FROM alert_rules WHERE is_enabled = TRUE")
        
        for rule in rules:
            try:
                # 获取最新数据检查是否触发报警
                latest = await conn.fetchrow(
                    f"""SELECT site_id, {rule['metric_name']} as value 
                        FROM latest_site_status 
                        WHERE {rule['metric_name']} IS NOT NULL"""
                )
                
                if latest and should_trigger_alarm(latest["value"], rule):
                    # 创建报警记录
                    await conn.execute(
                        """INSERT INTO alert_records 
                           (rule_id, site_id, metric_name, metric_value, threshold_value, status)
                           VALUES ($1, $2, $3, $4, $5, 'active')""",
                        rule["rule_id"], latest["site_id"], 
                        rule["metric_name"], latest["value"], rule["threshold_value"]
                    )
                    logger.info(f"触发报警：{rule['name']} - 站点 {latest['site_id']}")
                    import asyncio
                    asyncio.create_task(notify_all(
                        latest['site_id'], 
                        rule['name'], 
                        f"检测到异常值 {latest['value']} (阈值 {rule['threshold_value']})", 
                        float(latest['value'])
                    ))
                    
            except Exception as e:
                logger.error(f"检查报警规则 {rule['name']} 失败：{e}")

def should_trigger_alarm(value: float, rule: dict) -> bool:
    """判断是否应该触发报警"""
    condition = rule["condition_type"]
    threshold = rule["threshold_value"]
    
    if condition == "gt":  # 大于
        return value > threshold
    elif condition == "lt":  # 小于
        return value < threshold
    elif condition == "eq":  # 等于
        return value == threshold
    elif condition == "change":  # 变化
        return abs(value - threshold) > threshold * 0.1  # 10% 变化
    
    return False

# ============= API 端点 =============
@app.get("/api")
async def root():
    return {"message": "AntBox 监控系统 API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """健康检查"""
    db_status = "disconnected"
    if db_pool:
        try:
            async with db_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status
    }

@app.get("/api/dashboard/overview", response_model=DashboardOverview)
async def get_dashboard_overview():
    """获取仪表盘总览数据"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    async with db_pool.acquire() as conn:
        # 获取站点统计
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_online) as online,
                COUNT(*) FILTER (WHERE NOT is_online) as offline
            FROM sites
        """)
        
        # 获取最新状态统计
        latest_stats = await conn.fetchrow("""
            SELECT 
                SUM(total_power) as total_power,
                SUM(total_hashrate) as total_hashrate,
                AVG(supply_temp) as avg_supply_temp
            FROM latest_site_status
        """)
        
        # 获取活动报警数
        alert_count = await conn.fetchval(
            "SELECT COUNT(*) FROM alert_records WHERE status = 'active'"
        )
        
        return DashboardOverview(
            total_sites=stats["total"] or 0,
            online_sites=stats["online"] or 0,
            offline_sites=stats["offline"] or 0,
            active_alerts=alert_count or 0,
            total_power=float(latest_stats["total_power"]) if latest_stats["total_power"] else None,
            total_hashrate=float(latest_stats["total_hashrate"]) if latest_stats["total_hashrate"] else None,
            avg_supply_temp=float(latest_stats["avg_supply_temp"]) if latest_stats["avg_supply_temp"] else None
        )

@app.get("/api/sites", response_model=List[SiteStatus])
async def get_all_sites(
    status: Optional[str] = Query(None, description="过滤状态：online/offline"),
    limit: int = Query(100, ge=1, le=1000)
):
    """获取所有站点列表"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="数据库未连接")

    async with db_pool.acquire() as conn:
        if status == "online":
            rows = await conn.fetch(
                "SELECT * FROM latest_site_status WHERE is_online = TRUE LIMIT $1", limit
            )
        elif status == "offline":
            rows = await conn.fetch(
                "SELECT * FROM latest_site_status WHERE is_online = FALSE LIMIT $1", limit
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM latest_site_status LIMIT $1", limit
            )

        # 转换 IP 地址为字符串 (PostgreSQL INET 类型返回 IPv4Address 对象)
        result = []
        for row in rows:
            site_dict = dict(row)
            if site_dict.get('ip_address'):
                site_dict['ip_address'] = str(site_dict['ip_address'])
            result.append(site_dict)
        return result

@app.get("/api/sites/{site_id}")
async def get_site_detail(site_id: int):
    """获取站点详细信息"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    async with db_pool.acquire() as conn:
        site = await conn.fetchrow(
            "SELECT * FROM latest_site_status WHERE site_id = $1", site_id
        )
        
        if not site:
            raise HTTPException(status_code=404, detail="站点不存在")
        
        # 获取最近 24 小时趋势数据
        trends = await conn.fetch(
            """SELECT timestamp, supply_temp, return_temp, total_power, total_hashrate
               FROM status_snapshots
               WHERE site_id = $1 AND timestamp > NOW() - INTERVAL '24 hours'
               ORDER BY timestamp DESC""",
            site_id
        )
        
        return {
            "site": dict(site),
            "trends": [dict(row) for row in trends]
        }

@app.get("/api/alerts", response_model=List[AlertRecord])
async def get_alerts(
    status: str = Query("active", description="报警状态：active/acknowledged/resolved"),
    limit: int = Query(50, ge=1, le=500)
):
    """获取报警列表"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM alert_records WHERE status = $1 ORDER BY triggered_at DESC LIMIT $2",
            status, limit
        )
        return [dict(row) for row in rows]

@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int):
    """确认报警"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            """UPDATE alert_records 
               SET status = 'acknowledged', acknowledged_at = NOW()
               WHERE record_id = $1 AND status = 'active'""",
            alert_id
        )
        
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="报警不存在或已处理")
        
        return {"message": "报警已确认", "alert_id": alert_id}

@app.get("/api/trend/{metric}")
async def get_trend(
    metric: str,
    hours: int = Query(24, ge=1, le=168),
    site_id: Optional[int] = Query(None, description="站点 ID，不传则为所有站点平均值")
):
    """获取趋势数据"""
    if not db_pool:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    valid_metrics = ["supply_temp", "return_temp", "total_power", "total_hashrate", "efficiency"]
    if metric not in valid_metrics:
        raise HTTPException(status_code=400, detail=f"无效的指标，可选：{valid_metrics}")
    
    async with db_pool.acquire() as conn:
        if site_id:
            rows = await conn.fetch(
                f"""SELECT timestamp, {metric} as value
                    FROM status_snapshots
                    WHERE site_id = $1 AND timestamp > NOW() - INTERVAL '{hours} hours'
                    ORDER BY timestamp""",
                site_id
            )
        else:
            rows = await conn.fetch(
                f"""SELECT DATE_TRUNC('hour', timestamp) as timestamp, AVG({metric}) as value
                    FROM status_snapshots
                    WHERE timestamp > NOW() - INTERVAL '{hours} hours'
                    GROUP BY DATE_TRUNC('hour', timestamp)
                    ORDER BY timestamp"""
            )
        
        return {
            "metric": metric,
            "hours": hours,
            "site_id": site_id,
            "data": [{"timestamp": row["timestamp"].isoformat(), "value": round(float(row["value"]), 2) if row["value"] is not None else 0} for row in rows]
        }

# ============= 主程序 =============

# Ping检测API
@app.post("/api/ping")
async def ping_device(ip: str, count: int = 2, timeout: int = 2):
    """Ping检测单个设备"""
    return await ping_endpoint(ip, count, timeout)

@app.post("/api/ping/batch")
async def ping_devices_batch(ips: List[str], max_concurrent: int = 10, count: int = 2, timeout: int = 2):
    """批量Ping检测"""
    return await ping_batch_endpoint(ips, max_concurrent, count, timeout)



# Scan API from scanner_module
from pydantic import BaseModel
class ScanRequest(BaseModel):
    start_ip: str
    end_ip: str
    scan_type: str = 'all'
    port: int = 80
    concurrent_limit: int = 50

from scanner_module import scanner

@app.post("/api/scan/start")
async def start_scan(req: ScanRequest):
    return scanner.start_scan(req.start_ip, req.end_ip, req.scan_type, req.port, req.concurrent_limit)

@app.post("/api/scan/stop")
async def stop_scan():
    return scanner.stop_scan()

@app.get("/api/scan/status")
async def get_scan_status():
    return scanner.get_status()


if __name__ == "__main__":
    # 创建 SSL 证书（如果不存在）
    cert_dir = "/etc/ssl/antmonitor"
    cert_file = os.path.join(cert_dir, "cert.pem")
    key_file = os.path.join(cert_dir, "key.pem")
    
    if not os.path.exists(cert_file):
        logger.info("正在生成自签名 SSL 证书...")
        os.makedirs(cert_dir, exist_ok=True)
        os.system(f"openssl req -x509 -newkey rsa:4096 -keyout {key_file} -out {cert_file} -days 365 -nodes -subj '/CN=antmonitor'")
        logger.info("SSL 证书生成完成")
    
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8443,
        ssl_certfile=cert_file,
        ssl_keyfile=key_file,
        log_config=None,  # 禁用 uvicorn 日志配置，使用我们的配置
        log_level="info"
    )
