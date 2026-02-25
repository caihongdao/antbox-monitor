#!/usr/bin/env python3
"""
测试所有站点的API一致性
使用异步并发验证84个AntBox站点的API结构和数据格式
"""

import asyncio
import aiohttp
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Set

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SiteAPITester:
    """站点API测试器"""
    
    def __init__(self, config_path: str = "config/all_sites.json"):
        self.config_path = config_path
        self.sites: List[Dict[str, str]] = []
        self.api_endpoints: Dict[str, str] = {}
        self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.sites = config.get("sites", [])
            self.api_endpoints = config.get("api_endpoints", {})
            self.timeout = config.get("timeout", 5)
            self.retry_count = config.get("retry_count", 3)
            
            logger.info(f"配置加载成功，共 {len(self.sites)} 个站点")
            logger.info(f"API端点: {list(self.api_endpoints.keys())}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            sys.exit(1)
    
    def get_api_url(self, ip: str, endpoint_path: str) -> str:
        """构建API URL"""
        return f"http://{ip}{endpoint_path}"
    
    async def test_site_endpoint(self, session: aiohttp.ClientSession, 
                                ip: str, endpoint_name: str, 
                                endpoint_path: str) -> Dict[str, Any]:
        """测试单个站点的单个API端点"""
        url = self.get_api_url(ip, endpoint_path)
        
        for attempt in range(self.retry_count):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    response_text = await response.text()
                    
                    # 尝试解析JSON
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError:
                        return {
                            "ip": ip,
                            "endpoint": endpoint_name,
                            "status": "invalid_json",
                            "http_status": response.status,
                            "error": "JSON解析失败",
                            "response_preview": response_text[:200] if response_text else ""
                        }
                    
                    # 检查基本响应结构
                    is_valid = data.get("ok") is not None and "method" in data and "params" in data
                    
                    return {
                        "ip": ip,
                        "endpoint": endpoint_name,
                        "status": "success" if is_valid else "invalid_format",
                        "http_status": response.status,
                        "ok": data.get("ok"),
                        "method": data.get("method"),
                        "has_params": "params" in data,
                        "params_keys": list(data.get("params", {}).keys()) if "params" in data else []
                    }
                    
            except asyncio.TimeoutError:
                if attempt == self.retry_count - 1:
                    return {
                        "ip": ip,
                        "endpoint": endpoint_name,
                        "status": "timeout",
                        "http_status": None,
                        "error": f"请求超时 (尝试 {self.retry_count} 次)"
                    }
                await asyncio.sleep(1)
                
            except aiohttp.ClientError as e:
                if attempt == self.retry_count - 1:
                    return {
                        "ip": ip,
                        "endpoint": endpoint_name,
                        "status": "connection_error",
                        "http_status": None,
                        "error": str(e)
                    }
                await asyncio.sleep(1)
                
            except Exception as e:
                return {
                    "ip": ip,
                    "endpoint": endpoint_name,
                    "status": "unknown_error",
                    "http_status": None,
                    "error": str(e)
                }
        
        return {
            "ip": ip,
            "endpoint": endpoint_name,
            "status": "max_retries_exceeded",
            "http_status": None,
            "error": f"达到最大重试次数 ({self.retry_count})"
        }
    
    async def test_site(self, session: aiohttp.ClientSession, site: Dict[str, str]) -> Dict[str, Any]:
        """测试单个站点的所有API端点"""
        ip = site["ip"]
        location = site.get("location", "")
        
        logger.info(f"测试站点: {ip} ({location})")
        
        # 并发测试所有API端点
        tasks = []
        for endpoint_name, endpoint_path in self.api_endpoints.items():
            task = self.test_site_endpoint(session, ip, endpoint_name, endpoint_path)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 分析测试结果
        endpoint_results = {r["endpoint"]: r for r in results}
        
        # 确定站点状态
        success_count = sum(1 for r in results if r["status"] == "success")
        if success_count == len(results):
            site_status = "fully_accessible"
        elif success_count > 0:
            site_status = "partially_accessible"
        else:
            site_status = "inaccessible"
        
        return {
            "ip": ip,
            "location": location,
            "status": site_status,
            "endpoint_results": endpoint_results,
            "test_time": datetime.utcnow().isoformat()
        }
    
    async def test_all_sites(self) -> List[Dict[str, Any]]:
        """测试所有站点"""
        logger.info(f"开始测试 {len(self.sites)} 个站点的API一致性")
        
        start_time = datetime.now()
        
        # 限制并发连接数
        connector = aiohttp.TCPConnector(limit=50)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for site in self.sites:
                task = self.test_site(session, site)
                tasks.append(task)
            
            # 并发执行所有站点测试
            results = await asyncio.gather(*tasks)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"测试完成，耗时: {duration:.2f} 秒")
        
        return results
    
    def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析测试结果，检查API一致性"""
        # 统计信息
        total_sites = len(results)
        fully_accessible = sum(1 for r in results if r["status"] == "fully_accessible")
        partially_accessible = sum(1 for r in results if r["status"] == "partially_accessible")
        inaccessible = sum(1 for r in results if r["status"] == "inaccessible")
        
        # 检查API响应格式一致性
        endpoint_formats: Dict[str, Set[str]] = {}
        endpoint_params: Dict[str, Set[tuple]] = {}
        
        for result in results:
            if result["status"] != "fully_accessible":
                continue
                
            for endpoint_name, endpoint_result in result["endpoint_results"].items():
                if endpoint_result["status"] == "success":
                    # 记录响应格式
                    format_key = f"{endpoint_result['ok']}-{endpoint_result['method']}"
                    endpoint_formats.setdefault(endpoint_name, set()).add(format_key)
                    
                    # 记录参数键
                    params_tuple = tuple(sorted(endpoint_result.get("params_keys", [])))
                    endpoint_params.setdefault(endpoint_name, set()).add(params_tuple)
        
        # 分析一致性
        consistency_report = {}
        for endpoint_name in self.api_endpoints.keys():
            formats = endpoint_formats.get(endpoint_name, set())
            params_sets = endpoint_params.get(endpoint_name, set())
            
            consistency_report[endpoint_name] = {
                "format_consistency": len(formats) == 1,
                "unique_formats": list(formats),
                "params_consistency": len(params_sets) == 1,
                "unique_params_sets": [list(s) for s in params_sets]
            }
        
        # 识别问题站点
        problem_sites = []
        for result in results:
            if result["status"] != "fully_accessible":
                problems = []
                for endpoint_name, endpoint_result in result["endpoint_results"].items():
                    if endpoint_result["status"] != "success":
                        problems.append(f"{endpoint_name}: {endpoint_result.get('error', endpoint_result['status'])}")
                
                if problems:
                    problem_sites.append({
                        "ip": result["ip"],
                        "location": result["location"],
                        "status": result["status"],
                        "problems": problems
                    })
        
        return {
            "summary": {
                "total_sites": total_sites,
                "fully_accessible": fully_accessible,
                "partially_accessible": partially_accessible,
                "inaccessible": inaccessible,
                "accessibility_rate": (fully_accessible + partially_accessible) / total_sites * 100 if total_sites > 0 else 0,
                "full_accessibility_rate": fully_accessible / total_sites * 100 if total_sites > 0 else 0,
                "test_duration_seconds": duration if 'duration' in locals() else 0
            },
            "consistency": consistency_report,
            "problem_sites": problem_sites
        }
    
    def save_results(self, results: List[Dict[str, Any]], analysis: Dict[str, Any]):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("test_results", exist_ok=True)
        
        # 保存原始结果
        raw_file = f"test_results/api_test_raw_{timestamp}.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "test_time": datetime.now().isoformat(),
                    "config_file": self.config_path,
                    "total_sites": len(self.sites)
                },
                "results": results
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"原始测试结果已保存到: {raw_file}")
        
        # 保存分析报告
        report_file = f"test_results/api_test_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析报告已保存到: {report_file}")
        
        # 生成文本报告
        text_file = f"test_results/api_test_summary_{timestamp}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("AntBox站点API一致性测试报告\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"配置文件: {self.config_path}\n")
            f.write(f"站点总数: {analysis['summary']['total_sites']}\n\n")
            
            f.write("访问性统计:\n")
            f.write(f"  完全可访问: {analysis['summary']['fully_accessible']} ({analysis['summary']['full_accessibility_rate']:.1f}%)\n")
            f.write(f"  部分可访问: {analysis['summary']['partially_accessible']}\n")
            f.write(f"  不可访问: {analysis['summary']['inaccessible']}\n")
            f.write(f"  总体访问率: {analysis['summary']['accessibility_rate']:.1f}%\n\n")
            
            f.write("API一致性分析:\n")
            for endpoint_name, consistency in analysis["consistency"].items():
                f.write(f"  {endpoint_name}:\n")
                f.write(f"    格式一致性: {'✅' if consistency['format_consistency'] else '❌'}\n")
                if not consistency['format_consistency']:
                    f.write(f"    发现的不同格式: {consistency['unique_formats']}\n")
                f.write(f"    参数一致性: {'✅' if consistency['params_consistency'] else '❌'}\n")
                if not consistency['params_consistency']:
                    f.write(f"    发现的不同参数集: {consistency['unique_params_sets']}\n")
            
            if analysis["problem_sites"]:
                f.write("\n问题站点列表:\n")
                for problem_site in analysis["problem_sites"][:20]:  # 只显示前20个
                    f.write(f"  {problem_site['ip']} - {problem_site['location']}\n")
                    for problem in problem_site['problems']:
                        f.write(f"    - {problem}\n")
                
                if len(analysis["problem_sites"]) > 20:
                    f.write(f"  ... 还有 {len(analysis['problem_sites']) - 20} 个问题站点\n")
            else:
                f.write("\n✅ 所有站点均可正常访问\n")
        
        logger.info(f"文本报告已保存到: {text_file}")
        
        return raw_file, report_file, text_file
    
    def print_summary(self, analysis: Dict[str, Any]):
        """打印测试结果摘要"""
        print("\n" + "="*70)
        print("AntBox站点API一致性测试结果摘要")
        print("="*70)
        
        summary = analysis["summary"]
        print(f"\n📊 站点访问性统计:")
        print(f"   站点总数: {summary['total_sites']}")
        print(f"   ✅ 完全可访问: {summary['fully_accessible']} ({summary['full_accessibility_rate']:.1f}%)")
        print(f"   ⚠️  部分可访问: {summary['partially_accessible']}")
        print(f"   ❌ 不可访问: {summary['inaccessible']}")
        print(f"   总体访问率: {summary['accessibility_rate']:.1f}%")
        
        print(f"\n⏱️  测试耗时: {summary['test_duration_seconds']:.2f} 秒")
        
        print(f"\n🔍 API一致性分析:")
        for endpoint_name, consistency in analysis["consistency"].items():
            format_icon = "✅" if consistency["format_consistency"] else "❌"
            params_icon = "✅" if consistency["params_consistency"] else "❌"
            print(f"   {endpoint_name}: 格式{format_icon} 参数{params_icon}")
        
        if analysis["problem_sites"]:
            print(f"\n⚠️  发现 {len(analysis['problem_sites'])} 个问题站点:")
            for problem_site in analysis["problem_sites"][:5]:  # 只显示前5个
                print(f"   {problem_site['ip']} - {problem_site['status']}")
                for problem in problem_site['problems'][:2]:  # 只显示前2个问题
                    print(f"     • {problem}")
            
            if len(analysis["problem_sites"]) > 5:
                print(f"   ... 还有 {len(analysis['problem_sites']) - 5} 个问题站点")
        else:
            print("\n🎉 所有站点API访问正常且格式一致！")

async def main():
    """主函数"""
    print("AntBox站点API一致性测试")
    print("="*60)
    print("正在验证84个站点的API结构和数据格式一致性...")
    
    # 检查配置文件
    if not os.path.exists("config/all_sites.json"):
        print("错误: 配置文件 config/all_sites.json 不存在")
        print("请先运行 create_full_config.py 生成完整配置文件")
        sys.exit(1)
    
    # 创建测试结果目录
    os.makedirs("test_results", exist_ok=True)
    
    # 初始化测试器
    tester = SiteAPITester("config/all_sites.json")
    
    try:
        # 执行测试
        print(f"开始测试 {len(tester.sites)} 个站点...")
        results = await tester.test_all_sites()
        
        # 分析结果
        print("分析测试结果...")
        analysis = tester.analyze_results(results)
        
        # 保存结果
        print("保存测试结果...")
        raw_file, report_file, text_file = tester.save_results(results, analysis)
        
        # 打印摘要
        tester.print_summary(analysis)
        
        print(f"\n📁 测试结果文件:")
        print(f"   原始数据: {raw_file}")
        print(f"   分析报告: {report_file}")
        print(f"   文本摘要: {text_file}")
        
        # 提供建议
        print(f"\n💡 建议下一步:")
        if analysis["summary"]["full_accessibility_rate"] >= 95:
            print("   ✅ API一致性良好，可以开始系统开发")
            print("   建议按选项A继续推进：实现数据采集服务")
        else:
            print("   ⚠️  部分站点存在问题，建议先解决访问性问题")
            print("   检查网络连接或站点状态后再继续")
            
    except KeyboardInterrupt:
        print("\n测试已停止")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())