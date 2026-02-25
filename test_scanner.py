import asyncio
import sys
from scanner_module import scanner

async def main():
    start_ip = "192.168.0.50"
    end_ip = "192.168.0.60"
    
    print(f"=== Starting Local Scan Test ({start_ip} - {end_ip}) ===")
    
    # Check what happens
    res = scanner.start_scan(start_ip, end_ip, "all", 80, 50)
    print("Start result:", res)
    
    while True:
        status = scanner.get_status()
        print(f"Status: {status['status']} | Progress: {status['progress']}% | Scanned: {status['scanned_ips']} | Found: {status['found_devices']}")
        
        if status['status'] in ['completed', 'stopped', 'error']:
            print("\nFinal Results:")
            for dev in status['results']:
                print(f"- IP: {dev['ip']} | Type: {dev['deviceType']} | Info: {dev['info']}")
            break
            
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
