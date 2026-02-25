#!/usr/bin/env python3
"""
仪表盘原型HTTP服务器
启动本地HTTP服务器并打开浏览器预览仪表盘
"""

import http.server
import socketserver
import webbrowser
import sys
import os
from datetime import datetime

PORT = 8080
HOST = "localhost"
DASHBOARD_FILE = "dashboard.html"

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """支持CORS的HTTP请求处理器"""
    
    def end_headers(self):
        # 添加CORS头部
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """处理OPTIONS预检请求"""
        self.send_response(200)
        self.end_headers()

def check_file_exists():
    """检查仪表盘文件是否存在"""
    if not os.path.exists(DASHBOARD_FILE):
        print(f"❌ 错误: 找不到仪表盘文件 '{DASHBOARD_FILE}'")
        print("请确保在项目根目录运行此脚本")
        return False
    return True

def get_file_size():
    """获取仪表盘文件大小"""
    try:
        size = os.path.getsize(DASHBOARD_FILE)
        return size
    except:
        return 0

def print_banner():
    """打印启动横幅"""
    print("\n" + "="*60)
    print("矿机冷却系统监控平台 - 仪表盘原型")
    print("="*60)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作目录: {os.getcwd()}")
    print(f"仪表盘文件: {DASHBOARD_FILE} ({get_file_size() / 1024:.1f} KB)")
    print(f"服务器地址: http://{HOST}:{PORT}")
    print("="*60 + "\n")

def start_server():
    """启动HTTP服务器"""
    try:
        # 切换到包含dashboard.html的目录
        os.chdir(os.path.dirname(os.path.abspath(__file__)) or '.')
        
        if not check_file_exists():
            return False
        
        print_banner()
        
        # 创建HTTP服务器
        handler = CORSRequestHandler
        
        with socketserver.TCPServer((HOST, PORT), handler) as httpd:
            print(f"✅ HTTP服务器已启动，监听端口 {PORT}")
            print("📊 仪表盘地址:")
            print(f"   http://{HOST}:{PORT}/{DASHBOARD_FILE}")
            print("\n📋 其他可用文件:")
            print(f"   http://{HOST}:{PORT}/README-prototype.md")
            print(f"   http://{HOST}:{PORT}/ui_design.md")
            print("\n🛑 按 Ctrl+C 停止服务器")
            print("-"*40)
            
            # 尝试自动打开浏览器
            try:
                url = f"http://{HOST}:{PORT}/{DASHBOARD_FILE}"
                print(f"🌐 正在打开浏览器访问 {url}...")
                webbrowser.open(url)
                print("✅ 浏览器已启动")
            except Exception as e:
                print(f"⚠️ 无法自动打开浏览器: {e}")
                print("请手动访问上述URL")
            
            print("\n服务器日志:")
            print("-"*40)
            
            # 启动服务器
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\n🛑 收到中断信号，正在关闭服务器...")
        return True
    except OSError as e:
        if e.errno == 48 or e.errno == 98:  # Address already in use
            print(f"❌ 端口 {PORT} 已被占用")
            print("请尝试以下操作:")
            print(f"  1. 杀死占用端口 {PORT} 的进程")
            print(f"  2. 使用其他端口: python serve_dashboard.py 8081")
            print(f"  3. 检查是否有其他HTTP服务器在运行")
        else:
            print(f"❌ 服务器启动失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
        return False

if __name__ == "__main__":
    # 检查是否指定了自定义端口
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
            if PORT < 1 or PORT > 65535:
                print(f"❌ 端口号必须在1-65535之间")
                sys.exit(1)
        except ValueError:
            print(f"❌ 无效的端口号: {sys.argv[1]}")
            print("用法: python serve_dashboard.py [端口号]")
            sys.exit(1)
    
    success = start_server()
    sys.exit(0 if success else 1)