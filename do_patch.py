import re

def patch():
    with open('js/scan_backend.js', 'r') as f:
        js = f.read()

    # 1. Replace startConcurrentScan
    scan_regex = re.compile(r'async startConcurrentScan\(scanType, port\) \{.*?\}\n    \n    // 运行扫描工作线程', re.DOTALL)
    new_scan = """async startConcurrentScan(scanType, port) {
        const startIP = document.getElementById('start-ip').value.trim();
        const endIP = document.getElementById('end-ip').value.trim();
        
        try {
            const response = await fetch('/api/scan/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_ip: startIP,
                    end_ip: endIP,
                    scan_type: scanType,
                    port: port,
                    concurrent_limit: this.maxConcurrent
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                this.addLog(`启动扫描失败: ${data.message}`, 'error');
                this.scanComplete();
                return;
            }
            
            this.renderedIPs = new Set();
            this.scanResults = [];
            this.pollInterval = setInterval(() => this.pollScanStatus(), 1500);
            
        } catch (error) {
            this.addLog(`无法连接到扫描服务器: ${error.message}`, 'error');
            this.scanComplete();
        }
    }
    
    async pollScanStatus() {
        if (!this.scanning) return;
        
        try {
            const response = await fetch('/api/scan/status');
            const data = await response.json();
            
            // Update stats
            this.scanStats.totalIps = data.total_ips;
            this.scanStats.scannedIps = data.scanned_ips;
            this.scanStats.foundDevices = data.found_devices;
            this.scanStats.antboxDevices = data.antbox_devices;
            this.scanStats.minerDevices = data.miner_devices;
            this.scanStats.offlineDevices = data.offline_devices;
            
            // Render new results
            if (data.results) {
                for (const result of data.results) {
                    if (!this.renderedIPs.has(result.ip)) {
                        this.renderedIPs.add(result.ip);
                        this.addResult(result);
                        this.addLog(`发现设备: ${result.ip} (${result.deviceType})`, 'success');
                    }
                }
            }
            
            // Update progress UI
            const progressBar = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            const progress = data.progress || 0;
            if (progressBar) progressBar.style.width = `${progress}%`;
            if (progressText) progressText.textContent = `${progress}%`;
            
            const scannedCountElement = document.getElementById('scanned-count');
            const foundCountElement = document.getElementById('found-count');
            if (scannedCountElement) scannedCountElement.textContent = `已扫描: ${data.scanned_ips}`;
            if (foundCountElement) foundCountElement.textContent = `发现: ${data.found_devices}`;
            
            this.updateStats();
            
            if (data.status === 'completed' || data.status === 'stopped' || data.status === 'error') {
                clearInterval(this.pollInterval);
                if (data.status === 'error') {
                    this.addLog(`扫描出错: ${data.error}`, 'error');
                }
                this.scanComplete();
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }
    
    // 运行扫描工作线程"""
    
    js = scan_regex.sub(new_scan, js)
    
    # 2. Patch stopScan
    stop_regex = re.compile(r'stopScan\(\) \{.*?this\.addLog\(\'扫描已手动停止\', \'warning\'\);', re.DOTALL)
    new_stop = """stopScan() {
        if (!this.scanning) return;
        
        fetch('/api/scan/stop', { method: 'POST' }).catch(e => console.error(e));
        
        this.scanning = false;
        if (this.pollInterval) clearInterval(this.pollInterval);
        this.currentScanId = null;
        
        const startScanBtn = document.getElementById('start-scan');
        const stopScanBtn = document.getElementById('stop-scan');
        
        if (startScanBtn) startScanBtn.disabled = false;
        if (stopScanBtn) stopScanBtn.disabled = true;
        
        this.addLog('扫描已手动停止', 'warning');"""
        
    js = stop_regex.sub(new_stop, js)
    
    with open('js/scan_backend.js', 'w') as f:
        f.write(js)

if __name__ == '__main__':
    patch()
