import asyncio
import json
import logging
import ipaddress
import time
from typing import Dict, List, Optional
from ping_detection import PingDetector
import socket
import aiohttp

logger = logging.getLogger("scanner_module")

class NetworkScanner:
    def __init__(self):
        self.active_scan_task: Optional[asyncio.Task] = None
        self.scan_status = {
            "status": "idle", # idle, scanning, completed, stopped, error
            "start_time": None,
            "end_time": None,
            "progress": 0,
            "total_ips": 0,
            "scanned_ips": 0,
            "found_devices": 0,
            "antbox_devices": 0,
            "miner_devices": 0,
            "offline_devices": 0,
            "results": [],
            "error": None
        }
        self.should_stop = False
        self.ping_detector = PingDetector(timeout=1, count=2)

    def generate_ips(self, start_ip: str, end_ip: str) -> List[str]:
        try:
            start = ipaddress.IPv4Address(start_ip)
            end = ipaddress.IPv4Address(end_ip)
            if start > end:
                return []
            return [str(ipaddress.IPv4Address(ip)) for ip in range(int(start), int(end) + 1)]
        except Exception as e:
            logger.error(f"Invalid IP range: {e}")
            return []

    async def scan_cgminer_api(self, ip: str, port: int = 4028) -> Optional[Dict]:
        """BTCTools-like ASIC miner detection using CGMiner API"""
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=1.5)
            # Try getting summary first
            req = json.dumps({"command": "summary"})
            writer.write(req.encode('utf-8'))
            await writer.drain()
            
            data = await asyncio.wait_for(reader.read(4096), timeout=1.5)
            writer.close()
            await writer.wait_closed()
            
            response = data.decode('utf-8').replace('\x00', '')
            parsed = json.loads(response)
            
            # Extract basic miner info
            miner_info = {"api": "CGMiner/BMMiner", "port": port}
            if "SUMMARY" in parsed and len(parsed["SUMMARY"]) > 0:
                summary = parsed["SUMMARY"][0]
                if "GHS av" in summary:
                    miner_info["hashrate"] = f"{summary['GHS av']:.2f} GH/s"
                elif "MHS av" in summary:
                    miner_info["hashrate"] = f"{summary['MHS av']:.2f} MH/s"
                
                if "Temperature" in summary:
                    miner_info["temperature"] = f"{summary['Temperature']}°C"
                elif "Temp" in summary:
                    miner_info["temperature"] = f"{summary['Temp']}°C"
                    
            return miner_info
        except Exception as e:
            return None

    async def scan_http_api(self, ip: str, port: int = 80) -> Optional[Dict]:
        """Detect AntBox or Web-based Miners"""
        url = f"http://{ip}:{port}/"
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(url, timeout=1.5) as resp:
                    html = await resp.text()
                    html_lower = html.lower()
                    
                    # Simple AntBox detection
                    if "antbox" in html_lower or "cooler" in html_lower or "矿机冷却" in html_lower:
                        return {"type": "antbox", "port": port, "info": {"title": "AntBox Cooler System"}}
                    # Simple Miner detection
                    if "antminer" in html_lower or "whatsminer" in html_lower or "avalon" in html_lower:
                        return {"type": "miner", "port": port, "info": {"title": "Web-based Miner"}}
                    
                    return {"type": "unknown", "port": port, "info": {"status": "HTTP available"}}
        except Exception:
            return None

    async def check_device(self, ip: str, scan_type: str, port: int) -> Optional[Dict]:
        """Check a single IP for ping, ASIC API, and HTTP"""
        ping_res = await self.ping_detector.ping(ip)
        
        result = {
            "ip": ip,
            "port": port,
            "deviceType": "unknown",
            "responseTime": int(time.time() * 1000),
            "status": "offline",
            "ping": ping_res,
            "info": {}
        }
        
        # If ping is successful, mark as ping_only temporarily
        if ping_res.get("success"):
            result["status"] = "ping_only"
            result["info"]["ping"] = f"延迟: {ping_res.get('latency', 0):.1f}ms"
        
        # 1. Check BTCTools-like ASIC API (Port 4028)
        cgminer_res = await self.scan_cgminer_api(ip, 4028)
        if cgminer_res:
            result["deviceType"] = "miner"
            result["status"] = "online"
            result["info"].update(cgminer_res)
            
            # If we only want antbox, filter it out (unless scan_type is 'all' or 'miner')
            if scan_type == 'antbox':
                return result if ping_res.get("success") else None
            return result
            
        # 2. Check HTTP API (Port 80 by default)
        http_res = await self.scan_http_api(ip, port)
        if http_res:
            result["deviceType"] = http_res["type"]
            result["status"] = "online"
            result["port"] = http_res["port"]
            result["info"].update(http_res["info"])
            
            if scan_type != 'all' and result["deviceType"] != scan_type:
                # Type mismatch but found device
                if result["deviceType"] == "unknown" and not ping_res.get("success"):
                    return None
            return result
            
        if result["status"] == "ping_only":
            return result
            
        return None

    async def _scan_worker(self, queue: asyncio.Queue, scan_type: str, port: int):
        while not self.should_stop:
            try:
                ip = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
                
            try:
                device = await self.check_device(ip, scan_type, port)
                self.scan_status["scanned_ips"] += 1
                
                if device:
                    self.scan_status["found_devices"] += 1
                    if device["deviceType"] == "antbox":
                        self.scan_status["antbox_devices"] += 1
                    elif device["deviceType"] == "miner":
                        self.scan_status["miner_devices"] += 1
                    else:
                        self.scan_status["offline_devices"] += 1
                        
                    self.scan_status["results"].append(device)
                else:
                    self.scan_status["offline_devices"] += 1
                    
                # Calculate progress
                self.scan_status["progress"] = int((self.scan_status["scanned_ips"] / self.scan_status["total_ips"]) * 100)
                
            except Exception as e:
                logger.error(f"Error scanning {ip}: {e}")
                self.scan_status["scanned_ips"] += 1
                self.scan_status["offline_devices"] += 1
            finally:
                queue.task_done()

    async def run_scan(self, start_ip: str, end_ip: str, scan_type: str = 'all', port: int = 80, concurrent_limit: int = 50):
        ips = self.generate_ips(start_ip, end_ip)
        if not ips:
            self.scan_status["status"] = "error"
            self.scan_status["error"] = "Invalid IP range"
            return

        self.should_stop = False
        self.scan_status = {
            "status": "scanning",
            "start_time": time.time(),
            "end_time": None,
            "progress": 0,
            "total_ips": len(ips),
            "scanned_ips": 0,
            "found_devices": 0,
            "antbox_devices": 0,
            "miner_devices": 0,
            "offline_devices": 0,
            "results": [],
            "error": None
        }

        queue = asyncio.Queue()
        for ip in ips:
            queue.put_nowait(ip)

        workers = []
        for _ in range(min(concurrent_limit, len(ips))):
            worker = asyncio.create_task(self._scan_worker(queue, scan_type, port))
            workers.append(worker)

        await queue.join()

        if self.should_stop:
            self.scan_status["status"] = "stopped"
        else:
            self.scan_status["status"] = "completed"
            
        self.scan_status["end_time"] = time.time()
        self.scan_status["progress"] = 100

    def start_scan(self, start_ip: str, end_ip: str, scan_type: str = 'all', port: int = 80, concurrent_limit: int = 50):
        if self.active_scan_task and not self.active_scan_task.done():
            return {"success": False, "message": "Scan already in progress"}
            
        self.active_scan_task = asyncio.create_task(self.run_scan(start_ip, end_ip, scan_type, port, concurrent_limit))
        return {"success": True, "message": "Scan started"}

    def stop_scan(self):
        if self.active_scan_task and not self.active_scan_task.done():
            self.should_stop = True
            return {"success": True, "message": "Stopping scan"}
        return {"success": False, "message": "No active scan"}

    def get_status(self):
        return self.scan_status

scanner = NetworkScanner()
