import os
import re

def rewrite_js(filepath):
    with open(filepath, 'r') as f:
        js = f.read()
        
    # We will replace startConcurrentScan and runWorker completely
    js = js.replace('async startConcurrentScan(scanType, port) {', 'async startConcurrentScan_old(scanType, port) {')
    js = js.replace('async runWorker(scanId, scanFunction, updateFunction) {', 'async runWorker_old(scanId, scanFunction, updateFunction) {')
    js = js.replace('async scanDevice(ip, port, scanType) {', 'async scanDevice_old(ip, port, scanType) {')
    
    # We'll just append our new logic at the end and modify startScan and stopScan
    
    new_methods = """
    // ==== BACKEND SCANNER INTEGRATION ====
    
    async startConcurrentScan(scanType, port) {
        const startIP = document.getElementById('start-ip').value.trim();
        const endIP = document.getElementById('end-ip').value.trim();
        const maxConcurrent = parseInt(document.getElementById('max-concurrent').value) || 50;
        
        try {
            const response = await fetch('/api/scan/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_ip: startIP,
                    end_ip: endIP,
                    scan_type: scanType,
                    port: port,
                    concurrent_limit: maxConcurrent
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                this.addLog(`启动扫描失败: ${data.message}`, 'error');
                this.scanComplete();
                return;
            }
            
            // Start polling
            this.scanResults = [];
            this.renderedIPs = new Set();
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
            for (const result of data.results) {
                if (!this.renderedIPs.has(result.ip)) {
                    this.renderedIPs.add(result.ip);
                    this.addResult(result);
                    this.addLog(`发现设备: ${result.ip} (${result.deviceType})`, 'success');
                }
            }
            
            // Update progress UI
            this.updateProgressUI(data);
            
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
    
    updateProgressUI(data) {
        const progress = data.progress || 0;
        const progressBar = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        if (progressBar) progressBar.style.width = `${progress}%`;
        if (progressText) progressText.textContent = `${progress}%`;
        
        const scannedCountElement = document.getElementById('scanned-count');
        const foundCountElement = document.getElementById('found-count');
        if (scannedCountElement) scannedCountElement.textContent = `已扫描: ${data.scanned_ips}`;
        if (foundCountElement) foundCountElement.textContent = `发现: ${data.found_devices}`;
        
        this.updateStats();
    }
    
    async stopScan() {
        if (!this.scanning) return;
        
        try {
            await fetch('/api/scan/stop', { method: 'POST' });
        } catch (e) {
            console.error(e);
        }
        
        this.scanning = false;
        if (this.pollInterval) clearInterval(this.pollInterval);
        
        const startScanBtn = document.getElementById('start-scan');
        const stopScanBtn = document.getElementById('stop-scan');
        
        if (startScanBtn) startScanBtn.disabled = false;
        if (stopScanBtn) stopScanBtn.disabled = true;
        
        this.addLog('扫描已手动停止', 'warning');
        AppCommon.showToast('扫描已停止', 'warning');
        this.showScanSummary();
    }
"""
    # Replace stopScan implementation to use the new one, but we already have one.
    # Let's just append and let the new one overwrite? No, class methods with same name overwrite in JS? Yes, if we redeclare it. But let's actually string replace the startScan and stopScan methods properly.
    pass

if __name__ == "__main__":
    pass
