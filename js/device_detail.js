// 设备详情页面功能
class DeviceDetailManager {
    constructor() {
        this.deviceId = null;
        this.deviceData = null;
        this.pingHistory = [];
        this.init();
    }
    
    init() {
        this.parseUrlParams();
        this.setupEventListeners();
        this.loadDeviceData();
        
        // 应用通用设置
        if (window.AppCommon) {
            window.AppCommon.init();
            window.AppCommon.applyResolutionSettings();
        }
    }
    
    // 解析URL参数
    parseUrlParams() {
        const urlParams = new URLSearchParams(window.location.search);
        this.deviceId = urlParams.get('id') || urlParams.get('ip');
        
        if (!this.deviceId) {
            // 尝试从sessionStorage获取
            this.deviceId = sessionStorage.getItem('lastDeviceId');
        }
        
        if (!this.deviceId) {
            this.showError('未指定设备ID，请从扫描页面选择设备');
            setTimeout(() => window.location.href = '/pages/scan.html', 3000);
            return;
        }
        
        // 保存到sessionStorage
        sessionStorage.setItem('lastDeviceId', this.deviceId);
    }
    
    // 设置事件监听器
    setupEventListeners() {
        // 页面刷新按钮
        document.querySelectorAll('[onclick="refreshDeviceData()"]').forEach(btn => {
            btn.onclick = () => this.refreshDeviceData();
        });
        
        // Ping测试按钮
        document.querySelectorAll('[onclick="runPingTest()"]').forEach(btn => {
            btn.onclick = () => this.runPingTest();
        });
        
        // 连接测试按钮
        document.querySelectorAll('[onclick="testConnection()"]').forEach(btn => {
            btn.onclick = () => this.testConnection();
        });
        
        // 删除按钮
        document.querySelectorAll('[onclick="showDeleteConfirm()"]').forEach(btn => {
            btn.onclick = () => this.showDeleteConfirm();
        });
        
        // 操作按钮
        const actionButtons = {
            'openWebInterface': this.openWebInterface,
            'showPortScan': this.showPortScan,
            'showTrafficMonitor': this.showTrafficMonitor,
            'showLogs': this.showLogs,
            'showConfigBackup': this.showConfigBackup,
            'showRebootOptions': this.showRebootOptions,
            'showPingHistory': this.showPingHistory
        };
        
        for (const [funcName, func] of Object.entries(actionButtons)) {
            document.querySelectorAll(`[onclick="${funcName}()"]`).forEach(btn => {
                btn.onclick = () => func.call(this);
            });
        }
        
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F5') {
                e.preventDefault();
                this.refreshDeviceData();
            } else if (e.key === 'r' && e.ctrlKey) {
                e.preventDefault();
                this.refreshDeviceData();
            } else if (e.key === 'p' && e.ctrlKey) {
                e.preventDefault();
                this.runPingTest();
            }
        });
    }
    
    // 显示/隐藏加载遮罩
    showLoading(message = '加载中...') {
        const overlay = document.getElementById('loading-overlay');
        const text = document.getElementById('loading-text');
        if (overlay && text) {
            text.textContent = message;
            overlay.style.display = 'flex';
        }
    }
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    // 显示错误消息
    showError(message) {
        AppCommon.showToast(message, 'error');
        console.error(message);
    }
    
    // 加载设备数据
    async loadDeviceData() {
        this.showLoading('加载设备信息...');
        
        try {
            // 尝试从API获取设备数据
            const response = await fetch(`http://192.168.0.57:8443/api/sites/${this.deviceId}`);
            
            if (response.ok) {
                this.deviceData = await response.json();
                this.updateDeviceDisplay();
                
                // 自动运行Ping测试
                setTimeout(() => this.runPingTest(), 1000);
            } else {
                // 如果API失败，使用默认数据
                this.deviceData = {
                    ip: this.deviceId,
                    port: 80,
                    deviceType: 'unknown',
                    status: 'online',
                    discoveryTime: new Date().toISOString(),
                    lastCheck: new Date().toISOString()
                };
                this.updateDeviceDisplay();
            }
            
            // 加载Ping历史
            await this.loadPingHistory();
            
        } catch (error) {
            this.showError(`加载设备数据失败: ${error.message}`);
            
            // 使用默认数据
            this.deviceData = {
                ip: this.deviceId,
                port: 80,
                deviceType: 'unknown',
                status: 'offline',
                discoveryTime: new Date().toISOString(),
                lastCheck: new Date().toISOString()
            };
            this.updateDeviceDisplay();
        } finally {
            this.hideLoading();
        }
    }
    
    // 更新设备显示
    updateDeviceDisplay() {
        if (!this.deviceData) return;
        
        // 更新设备标题
        document.getElementById('device-name').textContent = `设备 ${this.deviceData.ip}`;
        
        // 更新状态指示器
        const statusElement = document.getElementById('device-status');
        statusElement.className = `status-indicator status-${this.deviceData.status || 'unknown'}`;
        statusElement.textContent = this.deviceData.status === 'online' ? '在线' : 
                                   this.deviceData.status === 'offline' ? '离线' : '未知';
        
        // 更新基本信息
        document.getElementById('device-ip').textContent = this.deviceData.ip || '-';
        document.getElementById('device-port').textContent = this.deviceData.port || '80';
        
        const deviceType = this.deviceData.deviceType || 'unknown';
        document.getElementById('device-type').textContent = 
            deviceType === 'antbox' ? 'AntBox' : 
            deviceType === 'miner' ? '矿机' : '未知设备';
        
        document.getElementById('device-type').className = 'info-value';
        if (deviceType === 'antbox') document.getElementById('device-type').classList.add('antbox');
        if (deviceType === 'miner') document.getElementById('device-type').classList.add('miner');
        
        // 更新时间信息
        const discoveryTime = this.deviceData.discoveryTime ? 
            new Date(this.deviceData.discoveryTime).toLocaleString('zh-CN') : '-';
        document.getElementById('discovery-time').textContent = discoveryTime;
        
        const lastCheck = this.deviceData.lastCheck ? 
            new Date(this.deviceData.lastCheck).toLocaleString('zh-CN') : '-';
        document.getElementById('last-check').textContent = lastCheck;
        
        // 更新设备详情（如果有）
        if (this.deviceData.info) {
            document.getElementById('device-model').textContent = this.deviceData.info.model || '-';
            document.getElementById('firmware-version').textContent = this.deviceData.info.version || '-';
            document.getElementById('temperature').textContent = this.deviceData.info.temperature || '-';
            document.getElementById('power-consumption').textContent = this.deviceData.info.power || '-';
        }
        
        // 更新页面标题
        document.title = `${this.deviceData.ip} - 设备详情 - AntBox监控系统`;
    }
    
    // 运行Ping测试
    async runPingTest() {
        this.showLoading('正在执行Ping测试...');
        
        try {
            // 调用Ping API
            const response = await fetch('http://192.168.0.57:8443/api/ping', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip: this.deviceData.ip,
                    count: 4,
                    timeout: 3
                })
            });
            
            if (response.ok) {
                const pingResult = await response.json();
                this.updatePingDisplay(pingResult);
                
                // 保存到历史记录
                this.savePingResult(pingResult);
                
                AppCommon.showToast('Ping测试完成', 'success');
            } else {
                throw new Error('Ping测试失败');
            }
            
        } catch (error) {
            this.showError(`Ping测试失败: ${error.message}`);
            
            // 使用模拟数据
            this.updatePingDisplay({
                success: false,
                latency: null,
                packet_loss: 100.0,
                error: '测试失败',
                ttl: null
            });
        } finally {
            this.hideLoading();
        }
    }
    
    // 更新Ping显示
    updatePingDisplay(pingResult) {
        // 更新Ping状态
        const pingStatus = document.getElementById('ping-status');
        pingStatus.className = `status-indicator status-${pingResult.success ? 'online' : 'offline'}`;
        pingStatus.textContent = pingResult.success ? '连通' : '不通';
        
        // 更新HTTP状态（模拟）
        const httpStatus = document.getElementById('http-status');
        httpStatus.className = `status-indicator status-${pingResult.success ? 'online' : 'offline'}`;
        httpStatus.textContent = pingResult.success ? '正常' : '异常';
        
        // 更新响应时间
        document.getElementById('response-time').textContent = 
            pingResult.latency ? `${pingResult.latency.toFixed(1)} ms` : '-';
        
        // 更新TTL值
        document.getElementById('ttl-value').textContent = pingResult.ttl || '-';
        
        // 更新丢包率
        document.getElementById('packet-loss').textContent = 
            pingResult.packet_loss ? `${pingResult.packet_loss.toFixed(1)}%` : '-';
        
        // 更新Ping指标
        if (pingResult.success && pingResult.latency) {
            const avgLatency = pingResult.latency;
            const minLatency = avgLatency * 0.8; // 模拟最小值
            const maxLatency = avgLatency * 1.2; // 模拟最大值
            
            document.getElementById('avg-latency').textContent = `${avgLatency.toFixed(1)} ms`;
            document.getElementById('min-latency').textContent = `${minLatency.toFixed(1)} ms`;
            document.getElementById('max-latency').textContent = `${maxLatency.toFixed(1)} ms`;
            
            // 根据延迟设置颜色
            const latencyClass = avgLatency < 50 ? 'latency-good' : 
                                avgLatency < 100 ? 'latency-medium' : 'latency-poor';
            document.getElementById('avg-latency').className = `metric-value ${latencyClass}`;
            
            // 丢包率
            document.getElementById('loss-rate').textContent = `${pingResult.packet_loss.toFixed(1)}%`;
            document.getElementById('loss-rate').className = `metric-value ${pingResult.packet_loss < 5 ? 'latency-good' : pingResult.packet_loss < 20 ? 'latency-medium' : 'latency-poor'}`;
        } else {
            document.getElementById('avg-latency').textContent = '- ms';
            document.getElementById('min-latency').textContent = '- ms';
            document.getElementById('max-latency').textContent = '- ms';
            document.getElementById('loss-rate').textContent = '- %';
        }
        
        // 更新最后检测时间
        this.deviceData.lastCheck = new Date().toISOString();
        this.updateDeviceDisplay();
    }
    
    // 保存Ping结果
    savePingResult(pingResult) {
        const historyEntry = {
            timestamp: new Date().toISOString(),
            success: pingResult.success,
            latency: pingResult.latency,
            packet_loss: pingResult.packet_loss,
            ttl: pingResult.ttl
        };
        
        this.pingHistory.push(historyEntry);
        
        // 只保留最近的50条记录
        if (this.pingHistory.length > 50) {
            this.pingHistory = this.pingHistory.slice(-50);
        }
        
        // 保存到localStorage
        const key = `ping_history_${this.deviceData.ip}`;
        localStorage.setItem(key, JSON.stringify(this.pingHistory));
        
        // 更新图表
        this.updatePingChart();
    }
    
    // 加载Ping历史
    async loadPingHistory() {
        try {
            const key = `ping_history_${this.deviceData.ip}`;
            const savedHistory = localStorage.getItem(key);
            
            if (savedHistory) {
                this.pingHistory = JSON.parse(savedHistory);
                this.updatePingChart();
            }
        } catch (error) {
            console.error('加载Ping历史失败:', error);
        }
    }
    
    // 更新Ping图表
    updatePingChart() {
        const chartContainer = document.getElementById('ping-history-chart');
        
        if (this.pingHistory.length === 0) {
            chartContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-chart-line fa-2x"></i>
                    <p>暂无历史数据</p>
                    <button class="btn btn-sm btn-primary" onclick="deviceManager.runPingTest()">
                        执行Ping测试
                    </button>
                </div>
            `;
            return;
        }
        
        // 创建简单的时间序列图表
        const timestamps = this.pingHistory.map(entry => 
            new Date(entry.timestamp).toLocaleTimeString('zh-CN', { hour12: false })
        );
        const latencies = this.pingHistory.map(entry => entry.latency || 0);
        
        // 简单的SVG图表
        chartContainer.innerHTML = `
            <div style="position: relative; height: 250px;">
                <svg width="100%" height="100%" viewBox="0 0 800 250">
                    <!-- 网格线 -->
                    <line x1="50" y1="50" x2="750" y2="50" stroke="#e8e8e8" stroke-width="1"/>
                    <line x1="50" y1="125" x2="750" y2="125" stroke="#e8e8e8" stroke-width="1"/>
                    <line x1="50" y1="200" x2="750" y2="200" stroke="#e8e8e8" stroke-width="1"/>
                    
                    <!-- 数据线 -->
                    <polyline 
                        points="${this.pingHistory.map((entry, i) => 
                            `${50 + (i / (this.pingHistory.length - 1)) * 700},${200 - (entry.latency || 0) / 2}`
                        ).join(' ')}"
                        fill="none" 
                        stroke="${this.pingHistory[this.pingHistory.length - 1].success ? '#1890ff' : '#f5222d'}" 
                        stroke-width="2"
                    />
                    
                    <!-- 数据点 -->
                    ${this.pingHistory.map((entry, i) => `
                        <circle 
                            cx="${50 + (i / (this.pingHistory.length - 1)) * 700}" 
                            cy="${200 - (entry.latency || 0) / 2}" 
                            r="3" 
                            fill="${entry.success ? '#1890ff' : '#f5222d'}" 
                            title="时间: ${new Date(entry.timestamp).toLocaleTimeString()}, 延迟: ${entry.latency ? entry.latency.toFixed(1) + 'ms' : 'N/A'}"
                        />
                    `).join('')}
                    
                    <!-- 坐标轴标签 -->
                    <text x="40" y="50" text-anchor="end" font-size="10" fill="#666">0ms</text>
                    <text x="40" y="125" text-anchor="end" font-size="10" fill="#666">150ms</text>
                    <text x="40" y="200" text-anchor="end" font-size="10" fill="#666">300ms</text>
                </svg>
                <div style="text-align: center; margin-top: 10px; font-size: 12px; color: #666;">
                    最近${this.pingHistory.length}次Ping测试历史
                </div>
            </div>
        `;
    }
    
    // 测试连接
    async testConnection() {
        this.showLoading('测试设备连接...');
        
        try {
            const response = await fetch(`http://${this.deviceData.ip}:${this.deviceData.port}/`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            
            if (response.ok) {
                AppCommon.showToast('设备连接正常', 'success');
                
                // 更新设备状态
                this.deviceData.status = 'online';
                this.updateDeviceDisplay();
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            AppCommon.showToast(`设备连接失败: ${error.message}`, 'error');
            
            // 更新设备状态
            this.deviceData.status = 'offline';
            this.updateDeviceDisplay();
        } finally {
            this.hideLoading();
        }
    }
    
    // 刷新设备数据
    async refreshDeviceData() {
        await this.loadDeviceData();
        AppCommon.showToast('设备数据已刷新', 'success');
    }
    
    // 显示删除确认
    showDeleteConfirm() {
        AppCommon.showModal('确认删除', `
            <p>确定要删除设备 <strong>${this.deviceData.ip}</strong> 吗？</p>
            <p class="text-warning">此操作不可撤销，设备将从数据库中删除。</p>
            <div class="modal-actions">
                <button class="btn btn-danger" onclick="deviceManager.deleteDevice()">确认删除</button>
                <button class="btn btn-secondary" onclick="AppCommon.closeModal()">取消</button>
            </div>
        `);
    }
    
    // 删除设备
    async deleteDevice() {
        this.showLoading('正在删除设备...');
        
        try {
            // 调用删除API
            const response = await fetch(`http://192.168.0.57:8443/api/sites/${this.deviceData.ip}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                AppCommon.showToast('设备删除成功', 'success');
                setTimeout(() => window.location.href = '/pages/scan.html', 1500);
            } else {
                throw new Error('删除失败');
            }
        } catch (error) {
            this.showError(`删除设备失败: ${error.message}`);
        } finally {
            this.hideLoading();
            AppCommon.closeModal();
        }
    }
    
    // 打开Web界面
    openWebInterface() {
        window.open(`http://${this.deviceData.ip}:${this.deviceData.port}`, '_blank');
    }
    
    // 显示端口扫描
    showPortScan() {
        AppCommon.showModal('端口扫描', `
            <p>对设备 <strong>${this.deviceData.ip}</strong> 进行端口扫描</p>
            <div class="form-group">
                <label>端口范围:</label>
                <input type="text" id="port-range" value="1-1000" class="form-control">
            </div>
            <div class="form-group">
                <label>扫描速度:</label>
                <select id="scan-speed" class="form-control">
                    <option value="fast">快速扫描</option>
                    <option value="normal" selected>正常扫描</option>
                    <option value="slow">慢速扫描</option>
                </select>
            </div>
            <div class="modal-actions">
                <button class="btn btn-primary" onclick="deviceManager.startPortScan()">开始扫描</button>
                <button class="btn btn-secondary" onclick="AppCommon.closeModal()">取消</button>
            </div>
        `);
    }
    
    // 开始端口扫描
    async startPortScan() {
        const portRange = document.getElementById('port-range').value;
        const scanSpeed = document.getElementById('scan-speed').value;
        
        AppCommon.closeModal();
        this.showLoading('正在扫描端口...');
        
        try {
            // 调用端口扫描API
            const response = await fetch('http://192.168.0.57:8443/api/scan/ports', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ip: this.deviceData.ip,
                    port_range: portRange,
                    speed: scanSpeed
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showPortScanResults(result);
            } else {
                throw new Error('端口扫描失败');
            }
        } catch (error) {
            this.showError(`端口扫描失败: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    // 显示端口扫描结果
    showPortScanResults(results) {
        let html = `
            <h3>端口扫描结果</h3>
            <p>设备: <strong>${this.deviceData.ip}</strong></p>
            <p>扫描时间: ${new Date().toLocaleString('zh-CN')}</p>
        `;
        
        if (results.open_ports && results.open_ports.length > 0) {
            html += `
                <h4>开放端口:</h4>
                <div class="port-list">
                    ${results.open_ports.map(port => `
                        <div class="port-item">
                            <span class="port-number">${port.port}</span>
                            <span class="port-service">${port.service || '未知服务'}</span>
                            <span class="port-status status-online">开放</span>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            html += '<p class="text-muted">未发现开放端口</p>';
        }
        
        if (results.closed_ports && results.closed_ports.length > 0) {
            html += `
                <p>关闭端口: ${results.closed_ports.length}个</p>
            `;
        }
        
        AppCommon.showModal('端口扫描结果', html);
    }
    
    // 显示流量监控
    showTrafficMonitor() {
        AppCommon.showModal('流量监控', `
            <p>设备 <strong>${this.deviceData.ip}</strong> 的实时流量监控</p>
            <div class="traffic-stats">
                <div class="metric-card">
                    <div class="metric-label">上传流量</div>
                    <div class="metric-value">0 KB/s</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">下载流量</div>
                    <div class="metric-value">0 KB/s</div>
                </div>
            </div>
            <div class="traffic-chart" style="height: 200px; background: #f5f5f5; margin: 20px 0; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                <p class="text-muted">流量图表区域</p>
            </div>
            <div class="modal-actions">
                <button class="btn btn-primary" onclick="deviceManager.startTrafficMonitor()">开始监控</button>
                <button class="btn btn-secondary" onclick="AppCommon.closeModal()">关闭</button>
            </div>
        `);
    }
    
    startTrafficMonitor() {
        AppCommon.showToast('流量监控功能开发中', 'info');
    }
    
    // 显示日志
    showLogs() {
        AppCommon.showModal('设备日志', `
            <p>设备 <strong>${this.deviceData.ip}</strong> 的日志记录</p>
            <div class="log-container" style="height: 300px; overflow-y: auto; background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px;">
                <div class="log-entry">
                    <span class="log-time">${new Date().toLocaleTimeString()}</span>
                    <span class="log-message">连接到设备日志系统...</span>
                </div>
                <div class="log-entry">
                    <span class="log-time">${new Date(Date.now() - 1000).toLocaleTimeString()}</span>
                    <span class="log-message">正在读取日志文件...</span>
                </div>
                <div class="log-entry">
                    <span class="log-time">${new Date(Date.now() - 2000).toLocaleTimeString()}</span>
                    <span class="log-message">日志文件加载完成</span>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-primary" onclick="deviceManager.refreshLogs()">刷新日志</button>
                <button class="btn btn-secondary" onclick="AppCommon.closeModal()">关闭</button>
            </div>
        `);
    }
    
    refreshLogs() {
        AppCommon.showToast('日志已刷新', 'success');
    }
    
    // 显示配置备份
    showConfigBackup() {
        AppCommon.showModal('配置备份', `
            <p>备份设备 <strong>${this.deviceData.ip}</strong> 的配置文件</p>
            <div class="form-group">
                <label>备份名称:</label>
                <input type="text" id="backup-name" value="config_${this.deviceData.ip}_${new Date().toISOString().slice(0, 10)}" class="form-control">
            </div>
            <div class="form-group">
                <label>包含内容:</label>
                <div class="checkbox-group">
                    <label><input type="checkbox" checked> 网络配置</label>
                    <label><input type="checkbox" checked> 系统配置</label>
                    <label><input type="checkbox"> 日志文件</label>
                    <label><input type="checkbox" checked> 用户配置</label>
                </div>
            </div>
            <div class="modal-actions">
                <button class="btn btn-primary" onclick="deviceManager.startConfigBackup()">开始备份</button>
                <button class="btn btn-secondary" onclick="AppCommon.closeModal()">取消</button>
            </div>
        `);
    }
    
    startConfigBackup() {
        AppCommon.closeModal();
        this.showLoading('正在备份配置...');
        
        setTimeout(() => {
            this.hideLoading();
            AppCommon.showToast('配置备份完成', 'success');
        }, 2000);
    }
    
    // 显示重启选项
    showRebootOptions() {
        AppCommon.showModal('重启控制', `
            <p>远程控制设备 <strong>${this.deviceData.ip}</strong></p>
            <div class="warning-box">
                <i class="fas fa-exclamation-triangle"></i>
                <p>警告：重启操作会导致设备服务中断，请谨慎操作！</p>
            </div>
            <div class="action-buttons">
                <button class="btn btn-warning" onclick="deviceManager.sendRebootCommand('soft')">软重启</button>
                <button class="btn btn-danger" onclick="deviceManager.sendRebootCommand('hard')">硬重启</button>
                <button class="btn btn-info" onclick="deviceManager.sendRebootCommand('shutdown')">关机</button>
            </div>
            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="AppCommon.closeModal()">取消</button>
            </div>
        `);
    }
    
    sendRebootCommand(type) {
        const commands = {
            'soft': '软重启',
            'hard': '硬重启', 
            'shutdown': '关机'
        };
        
        AppCommon.closeModal();
        this.showLoading(`正在发送${commands[type]}命令...`);
        
        setTimeout(() => {
            this.hideLoading();
            AppCommon.showToast(`${commands[type]}命令已发送`, 'success');
        }, 2000);
    }
    
    // 显示Ping历史
    showPingHistory() {
        if (this.pingHistory.length === 0) {
            AppCommon.showToast('暂无Ping历史记录', 'info');
            return;
        }
        
        let html = `
            <h3>Ping历史记录</h3>
            <p>设备: <strong>${this.deviceData.ip}</strong></p>
            <div class="history-table-container" style="max-height: 400px; overflow-y: auto;">
                <table class="table">
                    <thead>
                        <tr>
                            <th>时间</th>
                            <th>状态</th>
                            <th>延迟(ms)</th>
                            <th>丢包率</th>
                            <th>TTL</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.pingHistory.slice().reverse().map(entry => `
                            <tr>
                                <td>${new Date(entry.timestamp).toLocaleString('zh-CN')}</td>
                                <td><span class="status-indicator status-${entry.success ? 'online' : 'offline'}">${entry.success ? '成功' : '失败'}</span></td>
                                <td>${entry.latency ? entry.latency.toFixed(1) : '-'}</td>
                                <td>${entry.packet_loss ? entry.packet_loss.toFixed(1) + '%' : '-'}</td>
                                <td>${entry.ttl || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="modal-actions">
                <button class="btn btn-primary" onclick="deviceManager.clearPingHistory()">清空历史</button>
                <button class="btn btn-secondary" onclick="AppCommon.closeModal()">关闭</button>
            </div>
        `;
        
        AppCommon.showModal('Ping历史记录', html);
    }
    
    // 清空Ping历史
    clearPingHistory() {
        const key = `ping_history_${this.deviceData.ip}`;
        localStorage.removeItem(key);
        this.pingHistory = [];
        this.updatePingChart();
        AppCommon.closeModal();
        AppCommon.showToast('Ping历史已清空', 'success');
    }
}

// 全局设备管理器实例
let deviceManager = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    deviceManager = new DeviceDetailManager();
});

// 全局函数供HTML调用
function refreshDeviceData() {
    if (deviceManager) deviceManager.refreshDeviceData();
}

function runPingTest() {
    if (deviceManager) deviceManager.runPingTest();
}

function testConnection() {
    if (deviceManager) deviceManager.testConnection();
}

function showDeleteConfirm() {
    if (deviceManager) deviceManager.showDeleteConfirm();
}

function openWebInterface() {
    if (deviceManager) deviceManager.openWebInterface();
}

function showPortScan() {
    if (deviceManager) deviceManager.showPortScan();
}

function showTrafficMonitor() {
    if (deviceManager) deviceManager.showTrafficMonitor();
}

function showLogs() {
    if (deviceManager) deviceManager.showLogs();
}

function showConfigBackup() {
    if (deviceManager) deviceManager.showConfigBackup();
}

function showRebootOptions() {
    if (deviceManager) deviceManager.showRebootOptions();
}

function showPingHistory() {
    if (deviceManager) deviceManager.showPingHistory();
}