import sys

def inject_scan_api(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # API endpoints
    api_block = """
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

"""
    if "@app.post(\"/api/scan/start\")" not in content:
        # insert before if __name__ == "__main__":
        content = content.replace('if __name__ == "__main__":', api_block + '\nif __name__ == "__main__":')
    
    with open(filepath, 'w') as f:
        f.write(content)
        
    print("Injected scan APIs to", filepath)

if __name__ == "__main__":
    import sys; inject_scan_api(sys.argv[1] if len(sys.argv) > 1 else "api_server.py")
