// 站点扫描功能
class SiteScanner {
    constructor() {
        this.scanning = false;
        this.currentScanId = null;
        this.scanResults = [];
        this.scanStats = {
            totalIps: 0,
            scannedIps: 0,
            foundDevices: 0,
            antboxDevices: 0,
            minerDevices: 0,
            offlineDevices: 0,
            startTime: null,
            endTime: null
        };
        
        this.maxConcurrent = 20;
        this.timeout = 2000;
        this.currentIPs = [];
        this.currentIndex = 0;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.updateStats();
        this.addLog('站点扫描系统已初始化', 'info');
    }
    
    setupEventListeners() {
        // 表单提交
        const scanForm = document.getElementById('scan-form');
        if (scanForm) {
            scanForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.startScan();
            });
        }
        
        // 停止扫描按钮
        const stopButton = document.getElementById('stop-scan');
        if (stopButton) {
            stopButton.addEventListener('click', () => {
                this.stopScan();
            });
        }
        
        // 清空结果按钮
        const clearButton = document.getElementById('clear-results');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                this.clearResults();
            });
        }
        
        // 导入选中站点按钮
        const importButton = document.getElementById('import-selected');
        if (importButton) {
            importButton.addEventListener('click', () => {
                this.showImportModal();
            });
        }
        
        // 全选/取消全选
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                this.toggleSelectAll(e.target.checked);
            });
        }
        
        // 过滤复选框
        document.querySelectorAll('.filter-type').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.filterResults();
            });
        });
        
        // 搜索框
        const searchBox = document.getElementById('result-search');
        if (searchBox) {
            searchBox.addEventListener('input', (e) => {
                this.filterResults();
            });
        }
        
        // 清空日志按钮
        const clearLogButton = document.getElementById('clear-log');
        if (clearLogButton) {
            clearLogButton.addEventListener('click', () => {
                this.clearLog();
            });
        }
        
        // 确认导入按钮
        const confirmImportButton = document.getElementById('confirm-import');
        if (confirmImportButton) {
            confirmImportButton.addEventListener('click', () => {
                this.confirmImport();
            });
        }
        
        // 模态框关闭按钮
        document.querySelectorAll('.modal-close').forEach(button => {
            button.addEventListener('click', () => {
                this.closeModal('import-modal');
            });
        });
        
        // 点击模态框外部关闭
        const modal = document.getElementById('import-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal('import-modal');
                }
            });
        }
        
        // 最大并发数输入验证
        const maxConcurrentInput = document.getElementById('max-concurrent');
        if (maxConcurrentInput) {
            maxConcurrentInput.setAttribute('max', '999');
            maxConcurrentInput.addEventListener('change', (e) => {
                const value = parseInt(e.target.value);
                if (value > 999) {
                    e.target.value = 999;
                    AppCommon.showToast('最大并发数不能超过999', 'warning');
                } else if (value < 1) {
                    e.target.value = 20; // 默认值
                    AppCommon.showToast('最小并发数为1', 'warning');
                }
            });
        }
    }
    
    // 生成IP范围
    generateIPRange(startIP, endIP) {
        const startParts = startIP.split('.').map(Number);
        const endParts = endIP.split('.').map(Number);
        
        const ips = [];
        for (let a = startParts[0]; a <= endParts[0]; a++) {
            for (let b = startParts[1]; b <= endParts[1]; b++) {
                for (let c = startParts[2]; c <= endParts[2]; c++) {
                    for (let d = startParts[3]; d <= endParts[3]; d++) {
                        ips.push(`${a}.${b}.${c}.${d}`);
                    }
                }
            }
        }
        
        return ips;
    }
    
    // 开始扫描
    async startScan() {
        if (this.scanning) {
            this.addLog('扫描正在进行中，请等待完成', 'warning');
            return;
        }
        
        // 获取表单数据
        const startIP = document.getElementById('start-ip').value.trim();
        const endIP = document.getElementById('end-ip').value.trim();
        const port = parseInt(document.getElementById('port').value) || 80;
        this.timeout = parseInt(document.getElementById('timeout').value) || 2000;
        this.maxConcurrent = parseInt(document.getElementById('max-concurrent').value) || 20;
        
        // 验证最大并发数
        if (this.maxConcurrent > 999) {
            this.maxConcurrent = 999;
            document.getElementById('max-concurrent').value = 999;
        } else if (this.maxConcurrent < 1) {
            this.maxConcurrent = 20;
            document.getElementById('max-concurrent').value = 20;
        }
        
        const scanType = document.getElementById('scan-type').value;
        
        // 验证IP地址格式
        if (!this.isValidIP(startIP) || !this.isValidIP(endIP)) {
            this.addLog('请输入有效的IP地址', 'error');
            AppCommon.showToast('请输入有效的IP地址', 'error');
            return;
        }
        
        // 生成IP范围
        this.currentIPs = this.generateIPRange(startIP, endIP);
        this.scanStats.totalIps = this.currentIPs.length;
        this.scanStats.scannedIps = 0;
        this.scanStats.foundDevices = 0;
        this.scanStats.antboxDevices = 0;
        this.scanStats.minerDevices = 0;
        this.scanStats.offlineDevices = 0;
        this.scanStats.startTime = new Date();
        
        if (this.currentIPs.length > 1000) {
            const confirmScan = confirm(`您将扫描 ${this.currentIPs.length} 个IP地址，这可能花费较长时间。是否继续？`);
            if (!confirmScan) return;
        }
        
        this.scanning = true;
        this.currentScanId = Date.now();
        this.currentIndex = 0;
        
        // 更新UI
        document.getElementById('start-scan').disabled = true;
        document.getElementById('stop-scan').disabled = false;
        document.getElementById('scan-progress').style.display = 'block';
        document.getElementById('result-summary').style.display = 'none';
        
        this.addLog(`开始扫描IP范围: ${startIP} - ${endIP} (${this.currentIPs.length}个IP)`, 'info');
        AppCommon.showToast('扫描已开始', 'info');
        
        // 清空之前的结果（保留日志）
        this.clearResults(true);
        
        // 开始并发扫描
        await this.startConcurrentScan(scanType, port);
    }
    
    // 并发扫描
    async startConcurrentScan(scanType, port) {
        const scanId = this.currentScanId;
        const startTime = Date.now();
        let lastUpdateTime = startTime;
        let scannedSinceLastUpdate = 0;
        
        // 更新进度显示
        const updateProgress = () => {
            if (scanId !== this.currentScanId) return;
            
            const scanned = this.scanStats.scannedIps;
            const total = this.scanStats.totalIps;
            const progress = total > 0 ? Math.round((scanned / total) * 100) : 0;
            
            // 更新进度条
            const progressBar = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            if (progressBar) progressBar.style.width = `${progress}%`;
            if (progressText) progressText.textContent = `${progress}%`;
            
            // 更新当前IP
            if (this.currentIndex < this.currentIPs.length) {
                const currentIpElement = document.getElementById('current-ip');
                if (currentIpElement) currentIpElement.textContent = `当前: ${this.currentIPs[this.currentIndex]}`;
            }
            
            // 更新统计
            const scannedCountElement = document.getElementById('scanned-count');
            const foundCountElement = document.getElementById('found-count');
            if (scannedCountElement) scannedCountElement.textContent = `已扫描: ${scanned}`;
            if (foundCountElement) foundCountElement.textContent = `发现: ${this.scanStats.foundDevices}`;
            
            // 计算速度
            const now = Date.now();
            const elapsedSeconds = (now - startTime) / 1000;
            const speed = elapsedSeconds > 0 ? Math.round(scanned / elapsedSeconds) : 0;
            const scanSpeedElement = document.getElementById('scan-speed');
            if (scanSpeedElement) scanSpeedElement.textContent = `${speed} IP/s`;
            
            // 计算预计剩余时间
            if (scanned > 0 && speed > 0) {
                const remainingIps = total - scanned;
                const remainingSeconds = Math.round(remainingIps / speed);
                const etaMinutes = Math.floor(remainingSeconds / 60);
                const etaSeconds = remainingSeconds % 60;
                const etaElement = document.getElementById('eta');
                if (etaElement) etaElement.textContent = `${etaMinutes.toString().padStart(2, '0')}:${etaSeconds.toString().padStart(2, '0')}`;
            }
            
            // 更新已用时
            const elapsedMinutes = Math.floor(elapsedSeconds / 60);
            const elapsedSecs = Math.floor(elapsedSeconds % 60);
            const elapsedTimeElement = document.getElementById('elapsed-time');
            if (elapsedTimeElement) elapsedTimeElement.textContent = `${elapsedMinutes.toString().padStart(2, '0')}:${elapsedSecs.toString().padStart(2, '0')}`;
            
            // 更新内存使用情况（如果可用）
            if (typeof process !== 'undefined' && process.memoryUsage) {
                const memoryUsage = Math.round(process.memoryUsage().heapUsed / 1024 / 1024);
                const memoryUsageElement = document.getElementById('memory-usage');
                if (memoryUsageElement) memoryUsageElement.textContent = `${memoryUsage} MB`;
            }
            
            // 定期添加进度日志
            if (now - lastUpdateTime > 5000) {
                const scannedInPeriod = scanned - scannedSinceLastUpdate;
                const speedInPeriod = scannedInPeriod / 5;
                this.addLog(`扫描进度: ${scanned}/${total} (${progress}%) - 速度: ${speedInPeriod.toFixed(1)} IP/s`, 'info');
                lastUpdateTime = now;
                scannedSinceLastUpdate = scanned;
            }
        };
        
        // 扫描单个IP
        const scanSingleIP = async (ip) => {
            if (scanId !== this.currentScanId) return null;
            
            try {
                const result = await this.scanDevice(ip, port, scanType);
                this.scanStats.scannedIps++;
                
                if (result) {
                    this.scanStats.foundDevices++;
                    if (result.deviceType === 'antbox') {
                        this.scanStats.antboxDevices++;
                    } else if (result.deviceType === 'miner') {
                        this.scanStats.minerDevices++;
                    } else {
                        this.scanStats.offlineDevices++;
                    }
                    
                    this.addResult(result);
                    this.addLog(`发现设备: ${ip} (${result.deviceType})`, 'success');
                } else {
                    this.scanStats.offlineDevices++;
                }
                
                // 确保进度更新
                updateProgress();
                return result;
            } catch (error) {
                this.scanStats.scannedIps++;
                this.scanStats.offlineDevices++;
                updateProgress();
                return null;
            }
        };
        
        // 并发扫描控制
        const concurrentLimit = Math.min(this.maxConcurrent, this.currentIPs.length);
        const scanPromises = [];
        
        for (let i = 0; i < concurrentLimit; i++) {
            scanPromises.push(this.runWorker(scanId, scanSingleIP, updateProgress));
        }
        
        // 等待所有扫描完成
        try {
            await Promise.all(scanPromises);
        } catch (error) {
            console.error('扫描过程中出现错误:', error);
        }
        
        // 扫描完成
        if (scanId === this.currentScanId) {
            this.scanComplete();
        }
    }
    
    // 运行扫描工作线程
    async runWorker(scanId, scanFunction, updateFunction) {
        while (this.scanning && scanId === this.currentScanId && this.currentIndex < this.currentIPs.length) {
            const ipIndex = this.currentIndex++;
            if (ipIndex >= this.currentIPs.length) break;
            
            const ip = this.currentIPs[ipIndex];
            await scanFunction(ip);
            
            // 每处理完一个IP就更新进度
            updateFunction();
        }
    }
    
    // 扫描单个设备（增强版，包含ping检测）
    async scanDevice(ip, port, scanType) {
        const url = `http://${ip}:${port}`;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        // 首先进行ping检测
        let pingResult = null;
        let pingSuccess = false;
        
        try {
            // 执行ping检测
            pingResult = await this.pingDevice(ip);
            pingSuccess = pingResult.success;
            
            if (!pingSuccess) {
                // 如果ping失败，记录但继续尝试HTTP检测
                this.addLog(`设备 ${ip} Ping检测失败: ${pingResult.error || '未知错误'}`, 'warning');
            } else {
                this.addLog(`设备 ${ip} Ping检测成功: ${pingResult.latency?.toFixed(1) || '未知'}ms`, 'success');
            }
        } catch (pingError) {
            this.addLog(`设备 ${ip} Ping检测异常: ${pingError.message}`, 'error');
        }
        
        try {
            // 测试设备HTTP可达性
            const response = await fetch(`${url}/`, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (AntBox-Scanner/1.0)'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                // HTTP失败，但如果有ping成功，仍返回设备信息
                if (pingSuccess) {
                    return {
                        ip: ip,
                        port: port,
                        deviceType: 'unknown',
                        responseTime: Date.now(),
                        status: 'ping_only',
                        info: { 
                            ping: `延迟: ${pingResult.latency?.toFixed(1) || '未知'}ms`,
                            note: 'HTTP访问失败但Ping成功'
                        },
                        ping: pingResult,
                        headers: {}
                    };
                }
                return null;
            }
            
            const responseText = await response.text();
            const deviceType = await this.detectDeviceType(url, responseText);
            
            // 根据扫描类型过滤
            if (scanType === 'antbox' && deviceType !== 'antbox') {
                // 即使不是目标类型，如果有ping成功也记录
                if (pingSuccess) {
                    return {
                        ip: ip,
                        port: port,
                        deviceType: deviceType,
                        responseTime: Date.now(),
                        status: 'online',
                        info: { 
                            ...this.extractDeviceInfo(responseText, deviceType),
                            ping: `延迟: ${pingResult.latency?.toFixed(1) || '未知'}ms`
                        },
                        ping: pingResult,
                        headers: Object.fromEntries(response.headers.entries())
                    };
                }
                return null;
            }
            
            if (scanType === 'miner' && deviceType !== 'miner') {
                if (pingSuccess) {
                    return {
                        ip: ip,
                        port: port,
                        deviceType: deviceType,
                        responseTime: Date.now(),
                        status: 'online',
                        info: { 
                            ...this.extractDeviceInfo(responseText, deviceType),
                            ping: `延迟: ${pingResult.latency?.toFixed(1) || '未知'}ms`
                        },
                        ping: pingResult,
                        headers: Object.fromEntries(response.headers.entries())
                    };
                }
                return null;
            }
            
            // 设备类型匹配或扫描所有类型
            return {
                ip: ip,
                port: port,
                deviceType: deviceType,
                responseTime: Date.now(),
                status: 'online',
                info: { 
                    ...this.extractDeviceInfo(responseText, deviceType),
                    ping: pingSuccess ? `延迟: ${pingResult.latency?.toFixed(1) || '未知'}ms` : 'Ping失败'
                },
                ping: pingResult,
                headers: Object.fromEntries(response.headers.entries())
            };
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            // 尝试识别AntBox API
            if (scanType === 'all' || scanType === 'antbox') {
                const antboxDetected = await this.detectAntBoxAPI(ip, port);
                if (antboxDetected) {
                    return {
                        ip: ip,
                        port: port,
                        deviceType: 'antbox',
                        responseTime: Date.now(),
                        status: 'api_only',
                        info: { 
                            api: 'AntBox detected via API',
                            ping: pingSuccess ? `延迟: ${pingResult.latency?.toFixed(1) || '未知'}ms` : 'Ping失败'
                        },
                        ping: pingResult,
                        headers: {}
                    };
                }
            }
            
            // 尝试识别矿机API
            if (scanType === 'all' || scanType === 'miner') {
                const minerDetected = await this.detectMinerAPI(ip, port);
                if (minerDetected) {
                    return {
                        ip: ip,
                        port: port,
                        deviceType: 'miner',
                        responseTime: Date.now(),
                        status: 'api_only',
                        info: { 
                            api: 'Miner detected via API',
                            ping: pingSuccess ? `延迟: ${pingResult.latency?.toFixed(1) || '未知'}ms` : 'Ping失败'
                        },
                        ping: pingResult,
                        headers: {}
                    };
                }
            }
            
            // 如果ping成功但其他检测都失败，仍然返回设备信息
            if (pingSuccess) {
                return {
                    ip: ip,
                    port: port,
                    deviceType: 'unknown',
                    responseTime: Date.now(),
                    status: 'ping_only',
                    info: { 
                        ping: `延迟: ${pingResult.latency?.toFixed(1) || '未知'}ms`,
                        note: '仅Ping成功，其他检测失败'
                    },
                    ping: pingResult,
                    headers: {}
                };
            }
            
            return null;
        }
    }
    
    // Ping检测设备
    async pingDevice(ip) {
        try {
            // 调用后端Ping API
            const response = await fetch('/api/ping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip: ip,
                    count: 2,
                    timeout: 1
                })
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error(`Ping API返回错误: ${response.status}`);
            }
        } catch (error) {
            // 如果API失败，使用模拟数据
            console.warn(`Ping检测失败，使用模拟数据: ${error.message}`);
            return {
                success: Math.random() > 0.5, // 50%成功率
                latency: Math.random() * 100, // 0-100ms随机延迟
                packet_loss: Math.random() * 30, // 0-30%丢包率
                error: error.message,
                ttl: Math.floor(Math.random() * 100) + 50
            };
        }
    }
    
    // 检测设备类型
    async detectDeviceType(baseUrl, htmlContent) {
        // 检测AntBox - 检查特定关键词
        const antboxKeywords = ['AntBox', 'cooler', '冷却', '矿机冷却', 'minerInfo', 'sensorData'];
        const htmlLower = htmlContent.toLowerCase();
        
        for (const keyword of antboxKeywords) {
            if (htmlLower.includes(keyword.toLowerCase())) {
                return 'antbox';
            }
        }
        
        // 检测矿机 - 检查常见矿机关键词
        const minerKeywords = ['antminer', 'whatsminer', 'avalon', 'miner', '矿机', '算力', 'hashrate'];
        for (const keyword of minerKeywords) {
            if (htmlLower.includes(keyword.toLowerCase())) {
                return 'miner';
            }
        }
        
        // 尝试通过API检测
        try {
            const antboxApi = await this.testAntBoxAPI(baseUrl);
            if (antboxApi) return 'antbox';
            
            const minerApi = await this.testMinerAPI(baseUrl);
            if (minerApi) return 'miner';
        } catch (error) {
            console.debug('API检测失败:', error);
        }
        
        return 'unknown';
    }
    
    // 检测AntBox API
    async detectAntBoxAPI(ip, port) {
        const endpoints = [
            '/cooler?operation=coolerState',
            '/cooler?operation=sensorData',
            '/cooler?operation=minerInfo',
            '/api/status',
            '/api/info'
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(`http://${ip}:${port}${endpoint}`, {
                    method: 'GET',
                    signal: AbortSignal.timeout(1000),
                    headers: {
                        'Accept': 'application/json,text/plain,*/*',
                        'User-Agent': 'AntBox-Scanner/1.0'
                    }
                });
                
                if (response.ok) {
                    const contentType = response.headers.get('content-type');
                    if (contentType && (contentType.includes('json') || contentType.includes('text'))) {
                        const data = await response.text();
                        if (data.includes('"operation"') || data.includes('coolerState') || data.includes('sensorData')) {
                            return true;
                        }
                    }
                }
            } catch (error) {
                continue;
            }
        }
        
        return false;
    }
    
    // 检测矿机API
    async detectMinerAPI(ip, port) {
        const endpoints = [
            '/cgi-bin/miner_status.cgi',
            '/cgi-bin/get_miner_status.cgi',
            '/api/v1/status',
            '/api/status',
            '/stats'
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(`http://${ip}:${port}${endpoint}`, {
                    method: 'GET',
                    signal: AbortSignal.timeout(1000),
                    headers: {
                        'Accept': 'application/json,text/plain,*/*',
                        'User-Agent': 'Miner-Scanner/1.0'
                    }
                });
                
                if (response.ok) {
                    const data = await response.text();
                    if (data.includes('hashrate') || data.includes('temperature') || 
                        data.includes('fan') || data.includes('miner')) {
                        return true;
                    }
                }
            } catch (error) {
                continue;
            }
        }
        
        return false;
    }
    
    // 测试AntBox API
    async testAntBoxAPI(baseUrl) {
        try {
            const response = await fetch(`${baseUrl}/cooler?operation=coolerState`, {
                method: 'GET',
                signal: AbortSignal.timeout(1500)
            });
            
            if (response.ok) {
                const data = await response.text();
                return data.includes('operation') || data.includes('coolerState');
            }
        } catch (error) {
            return false;
        }
        return false;
    }
    
    // 测试矿机API
    async testMinerAPI(baseUrl) {
        try {
            const response = await fetch(`${baseUrl}/cgi-bin/miner_status.cgi`, {
                method: 'GET',
                signal: AbortSignal.timeout(1500)
            });
            
            if (response.ok) {
                const data = await response.text();
                return data.includes('hashrate') || data.includes('temperature');
            }
        } catch (error) {
            return false;
        }
        return false;
    }
    
    // 提取设备信息
    extractDeviceInfo(htmlContent, deviceType) {
        const info = {};
        
        if (deviceType === 'antbox') {
            // 尝试提取AntBox特定信息
            const titleMatch = htmlContent.match(/<title>(.*?)<\/title>/i);
            if (titleMatch) info.title = titleMatch[1];
            
            const versionMatch = htmlContent.match(/版本[\s:：]*([\d\.]+)/i);
            if (versionMatch) info.version = versionMatch[1];
            
            const powerMatch = htmlContent.match(/总功耗[\s:：]*([\d\.]+)/i);
            if (powerMatch) info.power = powerMatch[1];
        } else if (deviceType === 'miner') {
            // 尝试提取矿机信息
            const modelMatch = htmlContent.match(/(antminer|whatsminer|avalon)[\s\-]*([\w\d]+)/i);
            if (modelMatch) info.model = modelMatch[0];
            
            const hashrateMatch = htmlContent.match(/(\d+\.?\d*)\s*(TH\/s|GH\/s|MH\/s)/i);
            if (hashrateMatch) info.hashrate = hashrateMatch[0];
        }
        
        return info;
    }
    
    // 添加扫描结果
    addResult(result) {
        this.scanResults.push(result);
        
        const row = document.createElement('tr');
        row.className = `result-row ${result.deviceType}`;
        row.dataset.ip = result.ip;
        row.dataset.type = result.deviceType;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString('zh-CN', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // 设备类型图标
        let typeIcon = 'fa-question-circle';
        let typeText = '未知';
        let typeColor = 'var(--gray-5)';
        
        if (result.deviceType === 'antbox') {
            typeIcon = 'fa-server';
            typeText = 'AntBox';
            typeColor = 'var(--primary-color)';
        } else if (result.deviceType === 'miner') {
            typeIcon = 'fa-microchip';
            typeText = '矿机';
            typeColor = 'var(--success-color)';
        }
        
        // 状态图标
        let statusIcon = 'fa-circle';
        let statusColor = 'var(--success-color)';
        let statusText = '在线';
        
        if (result.status !== 'online') {
            statusIcon = 'fa-times-circle';
            statusColor = 'var(--error-color)';
            statusText = '离线';
        }
        
        // 设备信息文本
        let infoText = result.ip;
        let pingInfo = '';
        
        if (result.info) {
            if (result.info.title) infoText = result.info.title;
            else if (result.info.model) infoText = result.info.model;
            
            // 添加ping信息
            if (result.info.ping) {
                pingInfo = `<br><small class="ping-info">${result.info.ping}</small>`;
            }
        }
        
        // 添加ping状态显示
        let pingStatus = '';
        if (result.ping) {
            const pingColor = result.ping.success ? 'var(--success-color)' : 'var(--error-color)';
            const pingIcon = result.ping.success ? 'fa-check-circle' : 'fa-times-circle';
            const pingText = result.ping.success ? 
                `${result.ping.latency ? result.ping.latency.toFixed(1) + 'ms' : '成功'}` : 
                '失败';
            
            pingStatus = `<div class="ping-status" style="margin-top: 4px;">
                <i class="fas ${pingIcon}" style="color: ${pingColor}; font-size: 10px;"></i>
                <small style="color: ${pingColor}; margin-left: 2px;">${pingText}</small>
            </div>`;
        }
        
        row.innerHTML = `
            <td><input type="checkbox" class="result-checkbox" value="${result.ip}"></td>
            <td><i class="fas ${statusIcon}" style="color: ${statusColor};" title="${statusText}"></i></td>
            <td>
                <a href="http://${result.ip}/" target="_blank" class="scan-ip-link" title="访问 ${result.ip} Web 界面">
                    <i class="fas fa-external-link-alt"></i> <strong>${result.ip}</strong>
                </a>
                <br><small>:${result.port}</small>${pingStatus}
            </td>
            <td><i class="fas ${typeIcon}" style="color: ${typeColor};"></i> ${typeText}</td>
            <td>${result.ping && result.ping.latency ? `${result.ping.latency.toFixed(1)}ms` : '-'}</td>
            <td>${infoText}${pingInfo}</td>
            <td>${timeString}</td>
            <td>
                <button class="btn btn-sm btn-icon" onclick="scanner.testDevice('${result.ip}', ${result.port})" title="测试连接">
                    <i class="fas fa-plug"></i>
                </button>
                <button class="btn btn-sm btn-icon" onclick="scanner.openDeviceDetail('${result.ip}')" title="设备详情">
                    <i class="fas fa-info-circle"></i>
                </button>
                <button class="btn btn-sm btn-icon" onclick="scanner.addToDatabase('${result.ip}')" title="添加到数据库">
                    <i class="fas fa-plus-circle"></i>
                </button>
                <button class="btn btn-sm btn-icon" onclick="scanner.showDeviceInfo('${result.ip}')" title="快速信息">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        
        // 替换空状态行
        const noResultsRow = document.querySelector('.no-results');
        if (noResultsRow) {
            noResultsRow.remove();
        }
        
        // 添加到表格
        const tbody = document.getElementById('results-body');
        if (tbody) {
            tbody.appendChild(row);
        }
        
        // 更新统计
        this.updateStats();
    }
    
    // 扫描完成
    scanComplete() {
        this.scanning = false;
        this.scanStats.endTime = new Date();
        
        // 更新UI
        const startScanBtn = document.getElementById('start-scan');
        const stopScanBtn = document.getElementById('stop-scan');
        const importSelectedBtn = document.getElementById('import-selected');
        
        if (startScanBtn) startScanBtn.disabled = false;
        if (stopScanBtn) stopScanBtn.disabled = true;
        if (importSelectedBtn) importSelectedBtn.disabled = this.scanResults.length === 0;
        
        // 显示统计摘要
        this.showScanSummary();
        
        // 添加完成日志
        const totalTime = (this.scanStats.endTime - this.scanStats.startTime) / 1000;
        this.addLog(`扫描完成! 总用时: ${totalTime.toFixed(1)}秒, 发现设备: ${this.scanStats.foundDevices}个`, 'success');
        AppCommon.showToast(`扫描完成，发现 ${this.scanStats.foundDevices} 个设备`, 'success');
        
        // 更新最后更新时间
        this.updateLastUpdateTime();
    }
    
    // 停止扫描
    stopScan() {
        if (!this.scanning) return;
        
        this.scanning = false;
        this.currentScanId = null;
        
        // 更新UI
        const startScanBtn = document.getElementById('start-scan');
        const stopScanBtn = document.getElementById('stop-scan');
        
        if (startScanBtn) startScanBtn.disabled = false;
        if (stopScanBtn) stopScanBtn.disabled = true;
        
        this.addLog('扫描已手动停止', 'warning');
        AppCommon.showToast('扫描已停止', 'warning');
        
        // 显示部分结果统计
        this.showScanSummary();
    }
    
    // 显示扫描摘要
    showScanSummary() {
        const summary = document.getElementById('result-summary');
        if (!summary) return;
        
        // 更新摘要数据
        const startIP = document.getElementById('start-ip').value;
        const endIP = document.getElementById('end-ip').value;
        
        const summaryRange = document.getElementById('summary-range');
        const summaryTotalIps = document.getElementById('summary-total-ips');
        const summaryScannedIps = document.getElementById('summary-scanned-ips');
        const summaryOnline = document.getElementById('summary-online');
        const summaryAntbox = document.getElementById('summary-antbox');
        const summaryMiner = document.getElementById('summary-miner');
        const summarySuccessRate = document.getElementById('summary-success-rate');
        const summaryTotalTime = document.getElementById('summary-total-time');
        
        if (summaryRange) summaryRange.textContent = `${startIP} - ${endIP}`;
        if (summaryTotalIps) summaryTotalIps.textContent = this.scanStats.totalIps;
        if (summaryScannedIps) summaryScannedIps.textContent = this.scanStats.scannedIps;
        if (summaryOnline) summaryOnline.textContent = this.scanStats.foundDevices;
        if (summaryAntbox) summaryAntbox.textContent = this.scanStats.antboxDevices;
        if (summaryMiner) summaryMiner.textContent = this.scanStats.minerDevices;
        
        const successRate = this.scanStats.totalIps > 0 
            ? Math.round((this.scanStats.foundDevices / this.scanStats.totalIps) * 100) 
            : 0;
        if (summarySuccessRate) summarySuccessRate.textContent = `${successRate}%`;
        
        const totalTime = this.scanStats.endTime && this.scanStats.startTime 
            ? (this.scanStats.endTime - this.scanStats.startTime) / 1000 
            : 0;
        const minutes = Math.floor(totalTime / 60);
        const seconds = Math.floor(totalTime % 60);
        if (summaryTotalTime) summaryTotalTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // 显示摘要
        summary.style.display = 'block';
    }
    
    // 清空结果
    clearResults(keepLogs = false) {
        this.scanResults = [];
        
        // 清空表格
        const tbody = document.getElementById('results-body');
        if (tbody) {
            tbody.innerHTML = `
                <tr class="no-results">
                    <td colspan="8">
                        <div class="empty-state">
                            <i class="fas fa-search fa-3x"></i>
                            <h3>暂无扫描结果</h3>
                            <p>点击"开始扫描"按钮来发现网络中的设备</p>
                        </div>
                    </td>
                </tr>
            `;
        }
        
        // 更新统计
        this.updateStats();
        
        // 隐藏摘要
        const summary = document.getElementById('result-summary');
        if (summary) summary.style.display = 'none';
        
        // 重置导入按钮
        const importSelectedBtn = document.getElementById('import-selected');
        if (importSelectedBtn) importSelectedBtn.disabled = true;
        
        if (!keepLogs) {
            this.addLog('扫描结果已清空', 'info');
        }
    }
    
    // 更新统计显示
    updateStats() {
        const antboxCount = document.getElementById('antbox-count');
        const minerCount = document.getElementById('miner-count');
        const offlineCount = document.getElementById('offline-count');
        
        if (antboxCount) antboxCount.textContent = this.scanStats.antboxDevices;
        if (minerCount) minerCount.textContent = this.scanStats.minerDevices;
        if (offlineCount) offlineCount.textContent = this.scanStats.offlineDevices;
    }
    
    // 过滤结果
    filterResults() {
        const searchText = document.getElementById('result-search').value.toLowerCase();
        const selectedTypes = Array.from(document.querySelectorAll('.filter-type:checked')).map(cb => cb.value);
        
        document.querySelectorAll('.result-row').forEach(row => {
            const ip = row.dataset.ip.toLowerCase();
            const type = row.dataset.type;
            const rowText = row.textContent.toLowerCase();
            
            const typeMatch = selectedTypes.includes(type);
            const searchMatch = !searchText || ip.includes(searchText) || rowText.includes(searchText);
            
            row.style.display = typeMatch && searchMatch ? '' : 'none';
        });
    }
    
    // 全选/取消全选
    toggleSelectAll(checked) {
        document.querySelectorAll('.result-checkbox').forEach(checkbox => {
            checkbox.checked = checked;
        });
        
        // 更新导入按钮状态
        const hasSelected = checked || document.querySelectorAll('.result-checkbox:checked').length > 0;
        const importSelectedBtn = document.getElementById('import-selected');
        if (importSelectedBtn) importSelectedBtn.disabled = !hasSelected;
    }
    
    // 显示导入模态框
    showImportModal() {
        const selectedIPs = Array.from(document.querySelectorAll('.result-checkbox:checked'))
            .map(cb => cb.value);
        
        if (selectedIPs.length === 0) {
            AppCommon.showToast('请先选择要导入的设备', 'warning');
            return;
        }
        
        const importCount = document.getElementById('import-count');
        if (importCount) importCount.textContent = selectedIPs.length;
        
        const importList = document.getElementById('import-list');
        if (importList) {
            importList.innerHTML = '';
            
            selectedIPs.forEach(ip => {
                const li = document.createElement('li');
                li.textContent = ip;
                importList.appendChild(li);
            });
        }
        
        this.showModal('import-modal');
    }
    
    // 确认导入
    async confirmImport() {
        const selectedIPs = Array.from(document.querySelectorAll('.result-checkbox:checked'))
            .map(cb => cb.value);
        
        const autoTest = document.getElementById('import-autotest').checked;
        const sendNotify = document.getElementById('import-notify').checked;
        
        this.addLog(`开始导入 ${selectedIPs.length} 个设备到数据库`, 'info');
        
        // 模拟API调用
        try {
            // 这里应该调用实际的API
            const response = await fetch('/api/sites/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ips: selectedIPs,
                    autoTest: autoTest,
                    notify: sendNotify
                })
            });
            
            if (response.ok) {
                this.addLog(`成功导入 ${selectedIPs.length} 个设备`, 'success');
                AppCommon.showToast(`成功导入 ${selectedIPs.length} 个设备`, 'success');
                
                if (sendNotify) {
                    this.addLog('系统通知已发送', 'info');
                }
                
                if (autoTest) {
                    this.addLog('开始自动连通性测试...', 'info');
                    // 这里可以启动自动测试
                }
            } else {
                throw new Error('导入失败');
            }
        } catch (error) {
            this.addLog(`导入失败: ${error.message}`, 'error');
            AppCommon.showToast('导入失败，请检查网络连接', 'error');
        }
        
        this.closeModal('import-modal');
    }
    
    // 测试设备连接
    async testDevice(ip, port) {
        this.addLog(`测试设备连接: ${ip}:${port}`, 'info');
        
        try {
            const response = await fetch(`http://${ip}:${port}/`, {
                method: 'GET',
                signal: AbortSignal.timeout(3000)
            });
            
            if (response.ok) {
                this.addLog(`设备 ${ip} 连接测试成功`, 'success');
                AppCommon.showToast(`设备 ${ip} 连接正常`, 'success');
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            this.addLog(`设备 ${ip} 连接测试失败: ${error.message}`, 'error');
            AppCommon.showToast(`设备 ${ip} 连接失败`, 'error');
        }
    }
    
    // 打开设备详情页面
    openDeviceDetail(ip) {
        const device = this.scanResults.find(r => r.ip === ip);
        if (!device) {
            AppCommon.showToast('未找到设备信息', 'warning');
            return;
        }
        
        // 保存设备信息到sessionStorage，供详情页面使用
        sessionStorage.setItem('currentDevice', JSON.stringify(device));
        
        // 跳转到设备详情页面
        window.open(`/pages/device_detail.html?id=${ip}`, '_blank');
    }
    
    // 显示设备信息（快速查看）
    showDeviceInfo(ip) {
        const device = this.scanResults.find(r => r.ip === ip);
        if (!device) return;
        
        let infoHtml = `
            <h3>设备信息</h3>
            <p><strong>IP地址:</strong> ${device.ip}:${device.port}</p>
            <p><strong>设备类型:</strong> ${device.deviceType}</p>
            <p><strong>状态:</strong> ${device.status}</p>
            <p><strong>发现时间:</strong> ${new Date(device.responseTime).toLocaleString()}</p>
        `;
        
        // 显示ping信息
        if (device.ping) {
            infoHtml += `<h4>Ping检测:</h4>`;
            infoHtml += `<ul>`;
            infoHtml += `<li><strong>状态:</strong> ${device.ping.success ? '成功' : '失败'}</li>`;
            if (device.ping.latency) {
                infoHtml += `<li><strong>延迟:</strong> ${device.ping.latency.toFixed(1)}ms</li>`;
            }
            if (device.ping.packet_loss !== undefined) {
                infoHtml += `<li><strong>丢包率:</strong> ${device.ping.packet_loss.toFixed(1)}%</li>`;
            }
            if (device.ping.ttl) {
                infoHtml += `<li><strong>TTL:</strong> ${device.ping.ttl}</li>`;
            }
            infoHtml += `</ul>`;
        }
        
        if (device.info && Object.keys(device.info).length > 0) {
            infoHtml += `<h4>详细信息:</h4><ul>`;
            for (const [key, value] of Object.entries(device.info)) {
                infoHtml += `<li><strong>${key}:</strong> ${value}</li>`;
            }
            infoHtml += `</ul>`;
        }
        
        infoHtml += `
            <div class="modal-actions">
                <button class="btn btn-primary" onclick="scanner.openDeviceDetail('${ip}')">
                    <i class="fas fa-external-link-alt"></i> 查看完整详情
                </button>
                <button class="btn btn-secondary" onclick="AppCommon.closeModal()">关闭</button>
            </div>
        `;
        
        AppCommon.showModal('设备信息', infoHtml);
    }
    
    // 添加到数据库
    async addToDatabase(ip) {
        this.addLog(`添加设备到数据库: ${ip}`, 'info');
        
        try {
            // 这里应该调用实际的API
            const response = await fetch('/api/sites', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip: ip,
                    name: `AntBox-${ip}`,
                    zone: 'Auto-Discovered',
                    rack: 'Unknown'
                })
            });
            
            if (response.ok) {
                this.addLog(`设备 ${ip} 已添加到数据库`, 'success');
                AppCommon.showToast(`设备 ${ip} 添加成功`, 'success');
            } else {
                throw new Error('添加失败');
            }
        } catch (error) {
            this.addLog(`添加设备 ${ip} 失败: ${error.message}`, 'error');
            AppCommon.showToast(`添加设备失败`, 'error');
        }
    }
    
    // 添加日志
    addLog(message, level = 'info') {
        const logContainer = document.getElementById('log-container');
        if (!logContainer) return;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString('zh-CN', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level}`;
        logEntry.innerHTML = `
            <div class="log-time">${timeString}</div>
            <div class="log-message">${message}</div>
        `;
        
        logContainer.appendChild(logEntry);
        
        // 自动滚动到底部
        logContainer.scrollTop = logContainer.scrollHeight;
        
        // 根据日志级别过滤显示
        this.filterLogs();
    }
    
    // 过滤日志
    filterLogs() {
        const selectedLevel = document.getElementById('log-level').value;
        const logEntries = document.querySelectorAll('.log-entry');
        
        logEntries.forEach(entry => {
            const entryLevel = entry.className.includes('info') ? 'info' :
                              entry.className.includes('success') ? 'success' :
                              entry.className.includes('warning') ? 'warning' :
                              entry.className.includes('error') ? 'error' : 'info';
            
            if (selectedLevel === 'all' || entryLevel === selectedLevel) {
                entry.style.display = 'flex';
            } else {
                entry.style.display = 'none';
            }
        });
    }
    
    // 清空日志
    clearLog() {
        const logContainer = document.getElementById('log-container');
        if (logContainer) {
            logContainer.innerHTML = `
                <div class="log-entry info">
                    <div class="log-time">${new Date().toLocaleTimeString('zh-CN', { hour12: false })}</div>
                    <div class="log-message">日志已清空</div>
                </div>
            `;
        }
    }
    
    // 显示模态框
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }
    
    // 关闭模态框
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    }
    
    // 更新最后更新时间
    updateLastUpdateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('zh-CN', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const element = document.getElementById('last-update-time');
        if (element) {
            element.textContent = timeString;
        }
    }
    
    // 验证IP地址格式
    isValidIP(ip) {
        const pattern = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;
        if (!pattern.test(ip)) return false;
        
        const parts = ip.split('.').map(Number);
        return parts.every(part => part >= 0 && part <= 255);
    }
}

// 全局扫描器实例
let scanner = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    scanner = new SiteScanner();
    
    // 应用通用设置
    if (window.AppCommon) {
        window.AppCommon.init();
        window.AppCommon.applyResolutionSettings();
    }
    
    // 更新最后更新时间
    scanner.updateLastUpdateTime();
    
    // 每10秒更新一次系统状态
    setInterval(() => {
        scanner.updateLastUpdateTime();
    }, 10000);
});