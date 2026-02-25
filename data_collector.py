#!/usr/bin/env python3
"""
矿机冷却系统数据采集原型
支持异步并发从多个AntBox站点采集数据
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SiteConfig:
    """站点配置"""
    def __init__(self, ip: str, location: str = ""):
        self.ip = ip
        self.location = location
        self.base_url = f"http://{ip}"
        
    def get_api_url(self, endpoint: str) -> str:
        """构建完整的API URL"""
        return f"{self.base_url}{endpoint}"

class DataCollector:
    """数据采集器"""
    
    def __init__(self, config_path: str = "config/sites.json"):
        self.config_path = config_path
        self.sites: List[SiteConfig] = []
        self.api_endpoints: Dict[str, str] = {}
        self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 加载站点配置
            for site_info in config.get("sites", []):
                site = SiteConfig(
                    ip=site_info["ip"],
                    location=site_info.get("location", "")
                )
                self.sites.append(site)
                
            # 加载API端点
            self.api_endpoints = config.get("api_endpoints", {})
            
            # 加载其他配置
            self.collection_interval = config.get("collection_interval", 60)
            self.timeout = config.get("timeout", 5)
            self.retry_count = config.get("retry_count", 3)
            
            logger.info(f"配置加载成功，共 {len(self.sites)} 个站点")
            logger.info(f"API端点: {list(self.api_endpoints.keys())}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)
    
    async def fetch_site_data(self, session: aiohttp.ClientSession, site: SiteConfig) -> Dict[str, Any]:
        """采集单个站点的所有数据"""
        site_data = {
            "ip": site.ip,
            "location": site.location,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {},
            "errors": []
        }
        
        # 并发获取所有API端点数据
        tasks = []
        for endpoint_name, endpoint_path in self.api_endpoints.items():
            task = self.fetch_api_endpoint(session, site, endpoint_name, endpoint_path)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for endpoint_name, result in zip(self.api_endpoints.keys(), results):
            if isinstance(result, Exception):
                error_msg = f"{endpoint_name} 采集失败: {str(result)}"
                logger.error(f"站点 {site.ip} - {error_msg}")
                site_data["errors"].append(error_msg)
            else:
                site_data["data"][endpoint_name] = result
        
        return site_data
    
    async def fetch_api_endpoint(self, session: aiohttp.ClientSession, 
                                 site: SiteConfig, endpoint_name: str, 
                                 endpoint_path: str) -> Dict[str, Any]:
        """获取单个API端点数据"""
        url = site.get_api_url(endpoint_path)
        
        for attempt in range(self.retry_count):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    if response.status == 200:
                        data = await response.json()
                        # 验证API响应格式
                        if data.get("ok") is not None:
                            return {
                                "status": "success",
                                "http_status": response.status,
                                "response": data
                            }
                        else:
                            return {
                                "status": "invalid_format",
                                "http_status": response.status,
                                "response": data
                            }
                    else:
                        return {
                            "status": "http_error",
                            "http_status": response.status,
                            "response": await response.text()
                        }
                        
            except asyncio.TimeoutError:
                if attempt == self.retry_count - 1:
                    raise TimeoutError(f"请求超时 (尝试 {self.retry_count} 次)")
                logger.warning(f"站点 {site.ip} - {endpoint_name} 第 {attempt+1} 次超时，重试...")
                await asyncio.sleep(1)  # 等待后重试
                
            except aiohttp.ClientError as e:
                if attempt == self.retry_count - 1:
                    raise ConnectionError(f"连接错误: {str(e)}")
                logger.warning(f"站点 {site.ip} - {endpoint_name} 连接错误，重试...")
                await asyncio.sleep(1)
                
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON解析错误: {str(e)}")
    
    async def collect_all_sites(self) -> List[Dict[str, Any]]:
        """采集所有站点数据"""
        logger.info(f"开始采集 {len(self.sites)} 个站点数据")
        
        connector = aiohttp.TCPConnector(limit=50)  # 限制并发连接数
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for site in self.sites:
                task = self.fetch_site_data(session, site)
                tasks.append(task)
            
            # 并发执行所有站点采集
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理采集结果
        collected_data = []
        for site, result in zip(self.sites, results):
            if isinstance(result, Exception):
                logger.error(f"站点 {site.ip} 采集失败: {str(result)}")
                collected_data.append({
                    "ip": site.ip,
                    "location": site.location,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {},
                    "errors": [str(result)],
                    "status": "failed"
                })
            else:
                collected_data.append(result)
                logger.info(f"站点 {site.ip} 采集成功")
        
        return collected_data
    
    def parse_cooler_state(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析冷却系统状态数据"""
        if not data.get("ok") or "params" not in data:
            return {}
        
        params = data["params"]
        return {
            "supply_temp": params.get("supply_temp"),  # 供液温度
            "return_temp": params.get("return_temp"),  # 回液温度
            "target_temp": params.get("target_temp"),  # 设定温度
            "flow_rate": params.get("flow_rate"),      # 流量
            "pressure": params.get("pressure"),        # 压力
            "compressor_speed": params.get("compressor_speed"),  # 压缩机转速
            "fan_speed": params.get("fan_speed"),      # 风机转速
            "fault_flags": params.get("fault_flags"),  # 故障标志
            "warning_flags": params.get("warning_flags"),  # 警告标志
            "operation_mode": params.get("operation_mode")  # 运行模式
        }
    
    def parse_sensor_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析传感器数据"""
        if not data.get("ok") or "params" not in data:
            return {}
        
        params = data["params"]
        return {
            "ambient_temp": params.get("ambient_temp"),      # 环境温度
            "ambient_humidity": params.get("ambient_humidity"),  # 环境湿度
            "cabinet_temp": params.get("cabinet_temp"),      # 机柜温度
            "total_power": params.get("total_power"),        # 总功耗
            "power_factor": params.get("power_factor"),      # 功率因数
            "voltage": params.get("voltage"),                # 电压
            "current": params.get("current"),                # 电流
            "energy_consumption": params.get("energy_consumption")  # 累计能耗
        }
    
    def parse_miner_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析矿机信息"""
        if not data.get("ok") or "params" not in data:
            return {}
        
        params = data["params"]
        miners = params.get("miners", [])
        
        total_hashrate = 0
        online_count = 0
        miner_details = []
        
        for miner in miners:
            hashrate = miner.get("hashrate", 0)
            total_hashrate += hashrate
            
            if miner.get("is_online"):
                online_count += 1
            
            miner_details.append({
                "index": miner.get("index"),
                "mac_address": miner.get("mac_address"),
                "hashrate": hashrate,
                "temperature": miner.get("temperature"),
                "is_online": miner.get("is_online"),
                "has_error": miner.get("has_error")
            })
        
        return {
            "miner_count": len(miners),
            "online_miner_count": online_count,
            "total_hashrate": total_hashrate,
            "efficiency": params.get("efficiency"),  # 能效比
            "avg_miner_temp": params.get("avg_miner_temp"),  # 平均温度
            "miner_details": miner_details
        }
    
    def process_collected_data(self, collected_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理采集到的原始数据，转换为结构化格式"""
        processed_data = []
        
        for site_data in collected_data:
            processed = {
                "ip": site_data["ip"],
                "location": site_data["location"],
                "timestamp": site_data["timestamp"],
                "status": "success" if not site_data["errors"] else "partial",
                "errors": site_data["errors"]
            }
            
            # 解析各API数据
            data = site_data.get("data", {})
            
            if "coolerState" in data:
                processed.update(self.parse_cooler_state(data["coolerState"]["response"]))
            
            if "sensorData" in data:
                processed.update(self.parse_sensor_data(data["sensorData"]["response"]))
            
            if "minerInfo" in data:
                processed.update(self.parse_miner_info(data["minerInfo"]["response"]))
            
            processed_data.append(processed)
        
        return processed_data
    
    async def run_single_collection(self):
        """执行单次数据采集"""
        logger.info("开始执行单次数据采集...")
        
        start_time = datetime.now()
        collected_data = await self.collect_all_sites()
        end_time = datetime.now()
        
        # 处理数据
        processed_data = self.process_collected_data(collected_data)
        
        # 统计信息
        success_count = sum(1 for d in processed_data if d["status"] == "success")
        partial_count = sum(1 for d in processed_data if d["status"] == "partial")
        failed_count = len(processed_data) - success_count - partial_count
        
        duration = (end_time - start_time).total_seconds()
        
        # 输出结果
        logger.info(f"采集完成，耗时: {duration:.2f} 秒")
        logger.info(f"成功: {success_count}, 部分成功: {partial_count}, 失败: {failed_count}")
        
        # 保存结果到文件
        output_file = f"data/collected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("data", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "collection_time": start_time.isoformat(),
                    "duration_seconds": duration,
                    "total_sites": len(self.sites),
                    "successful_sites": success_count
                },
                "sites": processed_data
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存到: {output_file}")
        
        # 打印摘要
        self.print_summary(processed_data)
        
        return processed_data
    
    def print_summary(self, processed_data: List[Dict[str, Any]]):
        """打印采集结果摘要"""
        print("\n" + "="*60)
        print("数据采集结果摘要")
        print("="*60)
        
        for site_data in processed_data[:5]:  # 只显示前5个站点
            status_icon = "✅" if site_data["status"] == "success" else "⚠️" if site_data["status"] == "partial" else "❌"
            print(f"{status_icon} {site_data['ip']} - {site_data['location']}")
            
            if "total_power" in site_data:
                print(f"   功耗: {site_data.get('total_power', 'N/A')} KW")
            if "total_hashrate" in site_data:
                print(f"   算力: {site_data.get('total_hashrate', 'N/A')} PH/s")
            if "supply_temp" in site_data:
                print(f"   供液温度: {site_data.get('supply_temp', 'N/A')}°C")
        
        if len(processed_data) > 5:
            print(f"... 其余 {len(processed_data) - 5} 个站点省略")

async def main():
    """主函数"""
    print("矿机冷却系统数据采集原型")
    print("="*60)
    
    # 检查配置文件
    if not os.path.exists("config/sites.json"):
        print("错误: 配置文件 config/sites.json 不存在")
        print("请先创建配置文件或运行 generate_config.py 生成")
        sys.exit(1)
    
    # 创建数据目录
    os.makedirs("data", exist_ok=True)
    
    # 初始化采集器
    collector = DataCollector()
    
    try:
        # 执行单次采集
        await collector.run_single_collection()
        
        # 如果要连续采集，可以取消下面的注释
        # while True:
        #     await collector.run_single_collection()
        #     print(f"等待 {collector.collection_interval} 秒后进行下一次采集...")
        #     await asyncio.sleep(collector.collection_interval)
            
    except KeyboardInterrupt:
        print("\n采集已停止")
    except Exception as e:
        logger.error(f"采集过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())