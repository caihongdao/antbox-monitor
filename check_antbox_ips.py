#!/usr/bin/env python3
"""
检测AntBox设备IP有效性
"""

import asyncio
import aiohttp
import sys
import os
from typing import List, Tuple

# 添加项目根目录到Python路径
sys.path.append('/root/.openclaw/workspace')

async def check_single_ip(ip: str) -> Tuple[str, bool, dict]:
    """检测单个IP地址是否为有效的AntBox设备"""
    try:
        # 首先尝试ping检测连通性
        ping_result = await ping_ip(ip)
        if not ping_result:
            return ip, False, {"error": "ping failed"}
        
        # 检查HTTP端口 (通常AntBox设备在80端口提供Web界面)
        http_result = await check_http_port(ip)
        if http_result:
            return ip, True, {"type": "antbox-http", "response_time": http_result}
        
        # 检查CGMiner API端口 4028
        cgminer_result = await check_cgminer_port(ip)
        if cgminer_result:
            return ip, True, {"type": "antbox-cgminer", "response_time": cgminer_result}
        
        # 如果ping通但没有检测到特定服务，标记为可达但未知类型
        return ip, True, {"type": "reachable", "response_time": ping_result}
        
    except Exception as e:
        return ip, False, {"error": str(e)}

async def ping_ip(ip: str) -> float:
    """使用ping检测IP连通性"""
    try:
        process = await asyncio.create_subprocess_shell(
            f"ping -c 1 -W 3 {ip}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, _ = await process.communicate()
        return process.returncode == 0
    except:
        return False

async def check_http_port(ip: str) -> float:
    """检测HTTP端口是否开放并返回响应时间"""
    try:
        start_time = asyncio.get_event_loop().time()
        async with aiohttp.ClientTimeout(total=5) as timeout:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"http://{ip}/", allow_redirects=True) as response:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    # 检查响应是否可能是AntBox设备
                    if response.status == 200:
                        return elapsed
    except:
        pass
    return None

async def check_cgminer_port(ip: str) -> float:
    """检测CGMiner API端口4028是否开放"""
    try:
        import socket
        from contextlib import closing
        
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(5)
            result = sock.connect_ex((ip, 4028))
            return result == 0
    except:
        return False

async def check_antbox_ips(ips: List[str]) -> List[dict]:
    """批量检测AntBox IP列表"""
    print(f"开始检测 {len(ips)} 个IP地址...")
    
    # 创建信号量限制并发数，避免对网络造成过大压力
    semaphore = asyncio.Semaphore(50)  # 最多同时检测50个IP
    
    async def check_with_semaphore(ip):
        async with semaphore:
            return await check_single_ip(ip)
    
    tasks = [check_with_semaphore(ip) for ip in ips]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_ips = []
    invalid_ips = []
    
    for result in results:
        if isinstance(result, tuple):
            ip, is_valid, details = result
            if is_valid:
                valid_ips.append({"ip": ip, "details": details})
                print(f"✓ {ip} - Valid ({details})")
            else:
                invalid_ips.append({"ip": ip, "details": details})
                print(f"✗ {ip} - Invalid ({details})")
        else:
            # 处理异常情况
            print(f"Error processing result: {result}")
    
    return valid_ips, invalid_ips

def get_antbox_ips():
    """获取所有AntBox IP列表"""
    ips = [
        "10.1.101.1", "10.2.101.1", "10.1.102.1", "10.2.102.1", "10.1.103.1", "10.2.103.1",
        "10.1.104.1", "10.2.104.1", "10.1.105.1", "10.2.105.1", "10.1.106.1", "10.2.106.1",
        "10.1.107.1", "10.2.107.1", "10.1.108.1", "10.2.108.1", "10.1.109.1", "10.2.109.1",
        "10.1.110.1", "10.2.110.1", "10.1.111.1", "10.2.111.1", "10.1.112.1", "10.2.112.1",
        "10.1.113.1", "10.2.113.1", "10.1.114.1", "10.2.114.1", "10.1.115.1", "10.2.115.1",
        "10.1.116.1", "10.2.116.1", "10.1.117.1", "10.2.117.1", "10.1.118.1", "10.2.118.1",
        "10.1.119.1", "10.2.119.1", "10.1.120.1", "10.2.120.1", "10.1.121.1", "10.2.121.1",
        "10.1.122.1", "10.2.122.1", "10.1.123.1", "10.2.123.1", "10.1.124.1", "10.2.124.1",
        "10.1.125.1", "10.2.125.1", "10.1.126.1", "10.2.126.1", "10.1.127.1", "10.2.127.1",
        "10.1.128.1", "10.2.128.1", "10.1.129.1", "10.2.129.1", "10.1.130.1", "10.2.130.1",
        "10.1.131.1", "10.2.131.1", "10.1.132.1", "10.2.132.1", "10.1.133.1", "10.2.133.1",
        "10.1.134.1", "10.2.134.1", "10.1.135.1", "10.2.135.1", "10.1.136.1", "10.2.136.1",
        "10.1.137.1", "10.2.137.1", "10.1.138.1", "10.2.138.1", "10.1.139.1", "10.2.139.1",
        "10.1.140.1", "10.2.140.1", "10.1.141.1", "10.2.141.1", "10.1.142.1", "10.2.142.1",
        "10.1.143.1", "10.2.143.1", "10.1.144.1", "10.2.144.1", "10.1.145.1", "10.2.145.1",
        "10.1.146.1", "10.2.146.1", "10.1.147.1", "10.2.147.1", "10.1.148.1", "10.2.148.1",
        "10.1.149.1", "10.2.149.1", "10.1.150.1", "10.2.150.1", "10.3.101.1", "10.3.102.1",
        "10.3.103.1", "10.3.104.1", "10.3.105.1", "10.3.106.1", "10.3.107.1", "10.3.108.1",
        "10.3.109.1", "10.3.110.1", "10.3.111.1", "10.3.112.1", "10.3.113.1", "10.3.114.1",
        "10.3.115.1", "10.3.116.1", "10.3.117.1", "10.3.118.1", "10.3.129.1", "10.3.130.1",
        "10.3.131.1", "10.3.132.1", "10.3.133.1", "10.3.134.1", "10.3.135.1", "10.3.136.1",
        "10.3.137.1", "10.3.138.1", "10.3.139.1", "10.3.140.1", "10.3.141.1", "10.3.142.1",
        "10.3.143.1", "10.3.144.1", "10.4.101.1", "10.4.102.1", "10.4.103.1", "10.4.104.1",
        "10.4.105.1", "10.4.106.1", "10.4.107.1", "10.4.108.1", "10.4.109.1", "10.4.110.1",
        "10.4.111.1", "10.4.113.1", "10.4.114.1", "10.4.115.1", "10.4.116.1", "10.4.117.1",
        "10.4.118.1", "10.4.138.1", "10.4.139.1", "10.4.140.1", "10.4.143.1", "10.4.144.1"
    ]
    return ips

if __name__ == "__main__":
    ips = get_antbox_ips()
    print(f"总共 {len(ips)} 个IP待检测\n")
    
    # 运行检测
    valid_ips, invalid_ips = asyncio.run(check_antbox_ips(ips))
    
    print(f"\n检测完成！")
    print(f"有效IP数量: {len(valid_ips)}")
    print(f"无效IP数量: {len(invalid_ips)}")
    
    print("\n有效IP列表:")
    for item in valid_ips:
        print(f"  {item['ip']} - {item['details']}")
    
    # 保存结果到文件
    import json
    results = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "valid_ips": [item["ip"] for item in valid_ips],
        "invalid_ips": [item["ip"] for item in invalid_ips],
        "valid_count": len(valid_ips),
        "invalid_count": len(invalid_ips)
    }
    
    with open("/root/.openclaw/workspace/antbox_ip_check_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n检测结果已保存到: /root/.openclaw/workspace/antbox_ip_check_results.json")