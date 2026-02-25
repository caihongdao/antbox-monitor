#!/usr/bin/env python3
"""
Ping检测模块
用于检测服务器与站点IP之间的连通性
"""

import subprocess
import re
import asyncio
from typing import Dict, Optional, List, Tuple
import ipaddress

class PingDetector:
    """Ping检测器"""
    
    def __init__(self, timeout: int = 2, count: int = 2):
        """
        初始化Ping检测器
        
        Args:
            timeout: 超时时间（秒）
            count: Ping包数量
        """
        self.timeout = timeout
        self.count = count
        
    async def ping(self, ip: str, port: int = None) -> Dict:
        """
        Ping检测单个IP
        
        Args:
            ip: IP地址
            port: 可选端口，用于显示
            
        Returns:
            {
                "ip": ip,
                "port": port,
                "success": bool,
                "latency": float,  # 延迟（毫秒）
                "packet_loss": float,  # 丢包率
                "error": str,  # 错误信息
                "ttl": int,  # TTL值
                "platform": str  # 操作系统平台
            }
        """
        try:
            # 验证IP地址
            ipaddress.ip_address(ip)
        except ValueError:
            return {
                "ip": ip,
                "port": port,
                "success": False,
                "latency": None,
                "packet_loss": 100.0,
                "error": f"无效的IP地址: {ip}",
                "ttl": None,
                "platform": None
            }
        
        # 构建ping命令
        # 根据操作系统选择不同的ping参数
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            cmd = ["ping", "-n", str(self.count), "-w", str(self.timeout * 1000), ip]
        else:  # Linux, macOS等
            cmd = ["ping", "-c", str(self.count), "-W", str(self.timeout), ip]
        
        try:
            # 执行ping命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout + 2
            )
            
            output = stdout.decode('utf-8', errors='ignore')
            error_output = stderr.decode('utf-8', errors='ignore')
            
            # 解析ping结果
            result = self._parse_ping_output(output, system)
            result["ip"] = ip
            result["port"] = port
            result["platform"] = system
            
            if process.returncode != 0 and not result["success"]:
                result["error"] = error_output or f"Ping失败，返回码: {process.returncode}"
            
            return result
            
        except asyncio.TimeoutError:
            return {
                "ip": ip,
                "port": port,
                "success": False,
                "latency": None,
                "packet_loss": 100.0,
                "error": "Ping超时",
                "ttl": None,
                "platform": system if 'system' in locals() else "unknown"
            }
        except Exception as e:
            return {
                "ip": ip,
                "port": port,
                "success": False,
                "latency": None,
                "packet_loss": 100.0,
                "error": f"Ping执行错误: {str(e)}",
                "ttl": None,
                "platform": system if 'system' in locals() else "unknown"
            }
    
    def _parse_ping_output(self, output: str, system: str) -> Dict:
        """解析ping命令输出"""
        result = {
            "success": False,
            "latency": None,
            "packet_loss": 100.0,
            "error": None,
            "ttl": None
        }
        
        # 检测是否成功
        if system == "windows":
            # Windows ping输出
            if "Reply from" in output:
                result["success"] = True
                
                # 解析延迟
                time_match = re.search(r"time[=<](\d+\.?\d*)\s*ms", output)
                if time_match:
                    result["latency"] = float(time_match.group(1))
                
                # 解析TTL
                ttl_match = re.search(r"TTL=(\d+)", output)
                if ttl_match:
                    result["ttl"] = int(ttl_match.group(1))
                
                # 解析丢包率
                stats_match = re.search(r"Lost = (\d+).*?\((\d+)% loss\)", output, re.DOTALL)
                if stats_match:
                    lost = int(stats_match.group(1))
                    sent = lost + self.count  # 假设发送了count个包
                    result["packet_loss"] = float(stats_match.group(2))
                else:
                    # 如果没有统计信息，假设100%成功
                    result["packet_loss"] = 0.0
                    
        else:  # Linux/macOS
            if "ttl=" in output.lower() or "time=" in output.lower():
                result["success"] = True
                
                # 解析延迟（取平均延迟）
                time_match = re.search(r"min/avg/max/mdev = [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+", output)
                if time_match:
                    result["latency"] = float(time_match.group(1))
                else:
                    # 尝试其他格式
                    time_match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+", output)
                    if time_match:
                        result["latency"] = float(time_match.group(1))
                
                # 解析TTL
                ttl_match = re.search(r"ttl=(\d+)", output, re.IGNORECASE)
                if ttl_match:
                    result["ttl"] = int(ttl_match.group(1))
                
                # 解析丢包率
                stats_match = re.search(r"(\d+)% packet loss", output)
                if stats_match:
                    result["packet_loss"] = float(stats_match.group(1))
                else:
                    # 如果没有统计信息，假设100%成功
                    result["packet_loss"] = 0.0
        
        return result
    
    async def ping_batch(self, ips: List[str], max_concurrent: int = 10) -> List[Dict]:
        """
        批量Ping检测
        
        Args:
            ips: IP地址列表
            max_concurrent: 最大并发数
            
        Returns:
            Ping结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def ping_with_semaphore(ip):
            async with semaphore:
                return await self.ping(ip)
        
        tasks = [ping_with_semaphore(ip) for ip in ips]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    "ip": ips[i],
                    "success": False,
                    "latency": None,
                    "packet_loss": 100.0,
                    "error": f"Ping异常: {str(result)}",
                    "ttl": None,
                    "platform": "unknown"
                })
            else:
                final_results.append(result)
        
        return final_results

# FastAPI路由函数
async def ping_endpoint(ip: str, count: int = 2, timeout: int = 2):
    """Ping检测API端点"""
    detector = PingDetector(timeout=timeout, count=count)
    result = await detector.ping(ip)
    return result

async def ping_batch_endpoint(ips: List[str], max_concurrent: int = 10, count: int = 2, timeout: int = 2):
    """批量Ping检测API端点"""
    detector = PingDetector(timeout=timeout, count=count)
    results = await detector.ping_batch(ips, max_concurrent)
    return results

# 测试函数
async def test_ping():
    """测试Ping功能"""
    detector = PingDetector()
    
    # 测试单个IP
    print("测试单个IP:")
    result = await detector.ping("8.8.8.8")
    print(f"结果: {result}")
    
    # 测试批量
    print("\n测试批量Ping:")
    ips = ["8.8.8.8", "1.1.1.1", "192.168.1.1", "invalid.ip"]
    results = await detector.ping_batch(ips, max_concurrent=2)
    for r in results:
        print(f"{r['ip']}: {'成功' if r['success'] else '失败'} - 延迟: {r.get('latency', 'N/A')}ms")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_ping())