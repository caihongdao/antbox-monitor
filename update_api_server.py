#!/usr/bin/env python3
"""
更新API服务器，添加Ping检测端点
"""

import sys
import os

def update_api_server(filepath):
    """更新API服务器文件"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 添加必要的导入
    import_statements = [
        "# Ping检测模块",
        "from ping_detection import ping_endpoint, ping_batch_endpoint"
    ]
    
    # 在import fastapi之后添加
    if "import fastapi" in content and "from ping_detection import" not in content:
        # 找到import fastapi的位置
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip() == "import fastapi" or line.strip().startswith("import fastapi "):
                # 在下一行添加我们的导入
                new_lines.append("")
                new_lines.extend(import_statements)
        
        content = '\n'.join(new_lines)
        print("✓ 已添加Ping检测模块导入")
    else:
        print("✓ 导入语句已存在或不需要添加")
    
    # 2. 添加Ping API路由
    ping_api_code = '''
# Ping检测API
@app.post("/api/ping")
async def ping_device(ip: str, count: int = 2, timeout: int = 2):
    """Ping检测单个设备"""
    return await ping_endpoint(ip, count, timeout)

@app.post("/api/ping/batch")
async def ping_devices_batch(ips: List[str], max_concurrent: int = 10, count: int = 2, timeout: int = 2):
    """批量Ping检测"""
    return await ping_batch_endpoint(ips, max_concurrent, count, timeout)
'''
    
    if "@app.post(\"/api/ping\")" not in content:
        # 在if __name__ == "__main__":之前添加
        if 'if __name__ == "__main__":' in content:
            before_main = content.split('if __name__ == "__main__":')[0]
            after_main = 'if __name__ == "__main__":' + content.split('if __name__ == "__main__":')[1]
            
            new_content = before_main + ping_api_code + '\n\n' + after_main
            content = new_content
            print("✓ 已添加Ping API路由")
        else:
            print("✗ 未找到if __name__ == '__main__'，无法添加路由")
    else:
        print("✓ Ping API路由已存在")
    
    # 3. 确保List导入
    if "List[" in content and "from typing import List" not in content:
        # 检查是否已经有typing导入
        if "from typing import" in content:
            # 在现有的typing导入中添加List
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.strip().startswith("from typing import"):
                    # 检查是否已经包含List
                    if "List" not in line:
                        line = line.rstrip(',') + ", List"
                new_lines.append(line)
            content = '\n'.join(new_lines)
            print("✓ 已添加List类型导入")
    
    # 写入更新后的文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ API服务器文件已更新: {filepath}")
    return True

def main():
    if len(sys.argv) != 2:
        print("用法: python update_api_server.py <api_server.py路径>")
        sys.exit(1)
    
    api_file = sys.argv[1]
    if not os.path.exists(api_file):
        print(f"错误: 文件不存在: {api_file}")
        sys.exit(1)
    
    # 备份原文件
    backup_file = api_file + '.backup'
    import shutil
    shutil.copy2(api_file, backup_file)
    print(f"✓ 已创建备份: {backup_file}")
    
    # 更新文件
    if update_api_server(api_file):
        print("\n🎉 API服务器更新完成!")
        print("请重启服务以使更改生效:")
        print("sudo systemctl restart antmonitor.service")

if __name__ == "__main__":
    main()