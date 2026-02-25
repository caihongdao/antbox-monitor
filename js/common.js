// 通用JavaScript函数和工具
class AppCommon {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.applyResolutionSettings();
        this.setupNavigation();
        this.checkAuth();
    }
    
    // 应用分辨率设置
    applyResolutionSettings() {
        const width = window.innerWidth;
        const scaleElement = document.getElementById('resolution-scale');
        
        if (width >= 2560) {
            document.documentElement.style.setProperty('--resolution-scale', '1.3');
            if (scaleElement) scaleElement.textContent = '2560×1440';
        } else if (width >= 1920) {
            document.documentElement.style.setProperty('--resolution-scale', '1.1');
            if (scaleElement) scaleElement.textContent = '1920×1080';
        } else {
            document.documentElement.style.setProperty('--resolution-scale', '1');
            if (scaleElement) scaleElement.textContent = '自适应';
        }
    }
    
    // 设置事件监听器
    setupEventListeners() {
        // 切换侧边栏
        const toggleSidebar = document.getElementById('toggle-sidebar');
        if (toggleSidebar) {
            toggleSidebar.addEventListener('click', () => {
                document.querySelector('.sidebar').classList.toggle('active');
            });
        }
        
        // 响应窗口大小变化
        window.addEventListener('resize', () => {
            this.applyResolutionSettings();
        });
        
        // 表单提交
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });
    }
    
    // 设置导航
    setupNavigation() {
        // 高亮当前页面链接
        const currentPage = window.location.pathname.split('/').pop();
        document.querySelectorAll('.nav-link, .sidebar-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPage || (currentPage === '' && href === 'index.html')) {
                link.classList.add('active');
            }
        });
        
        // 处理内部链接点击
        document.querySelectorAll('a[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                this.loadPage(page);
            });
        });
    }
    
    // 加载页面（SPA风格）
    loadPage(pageName) {
        const contentArea = document.getElementById('main-content');
        if (!contentArea) return;
        
        // 显示加载状态
        contentArea.innerHTML = '<div class="loading-spinner">加载中...</div>';
        
        // 模拟页面加载（实际应使用fetch）
        setTimeout(() => {
            switch(pageName) {
                case 'dashboard':
                    contentArea.innerHTML = this.getDashboardContent();
                    break;
                case 'site-detail':
                    contentArea.innerHTML = this.getSiteDetailContent();
                    break;
                case 'monitoring-wall':
                    contentArea.innerHTML = this.getMonitoringWallContent();
                    break;
                default:
                    contentArea.innerHTML = '<h1>页面未找到</h1>';
            }
            
            // 更新URL和标题
            history.pushState({ page: pageName }, '', `?page=${pageName}`);
            document.title = `${this.getPageTitle(pageName)} - 矿机冷却系统监控平台`;
            
            // 重新初始化组件
            this.initCharts();
            this.initTables();
        }, 300);
    }
    
    // 检查认证状态
    checkAuth() {
        const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
        const userRole = localStorage.getItem('userRole') || 'viewer';
        const currentPage = window.location.pathname.split('/').pop();
        
        // 需要认证的页面
        const protectedPages = ['admin.html', 'water-usage.html'];
        const controlPages = ['monitoring-wall.html', 'site-detail.html?action=control'];
        
        if (!isLoggedIn && protectedPages.includes(currentPage)) {
            window.location.href = 'login.html';
            return;
        }
        
        if (userRole === 'viewer' && controlPages.some(page => window.location.href.includes(page))) {
            this.showToast('游客无法访问控制功能，请登录管理员账号', 'warning');
        }
    }
    
    // 处理表单提交
    handleFormSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formId = form.id;
        
        switch(formId) {
            case 'login-form':
                this.handleLogin(form);
                break;
            case 'scan-form':
                this.handleSiteScan(form);
                break;
            case 'water-usage-form':
                this.handleWaterUsage(form);
                break;
            default:
                console.log('表单提交:', formId);
        }
    }
    
    // 处理登录
    handleLogin(form) {
        const username = form.querySelector('#username').value;
        const password = form.querySelector('#password').value;
        
        // 模拟登录验证（实际应使用API）
        if (username === 'admin' && password === 'admin123') {
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('userRole', 'admin');
            localStorage.setItem('username', username);
            
            this.showToast('登录成功！', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);
        } else if (username === 'viewer' && password === 'viewer123') {
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('userRole', 'viewer');
            localStorage.setItem('username', username);
            
            this.showToast('登录成功！', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);
        } else {
            this.showToast('用户名或密码错误', 'error');
        }
    }
    
    // 处理站点扫描
    handleSiteScan(form) {
        const ipRange = form.querySelector('#ip-range').value;
        const startPort = form.querySelector('#start-port').value || 80;
        const endPort = form.querySelector('#end-port').value || 443;
        
        this.showToast(`开始扫描IP范围: ${ipRange}`, 'info');
        
        // 模拟扫描过程
        const progressBar = document.getElementById('scan-progress');
        const resultsContainer = document.getElementById('scan-results');
        
        if (progressBar) {
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                progressBar.style.width = `${progress}%`;
                progressBar.textContent = `${progress}%`;
                
                if (progress >= 100) {
                    clearInterval(interval);
                    
                    // 显示模拟结果
                    if (resultsContainer) {
                        resultsContainer.innerHTML = `
                            <div class="card">
                                <div class="card-header">
                                    <h3 class="card-title">扫描结果</h3>
                                </div>
                                <div class="card-body">
                                    <p>扫描完成！在范围 ${ipRange} 中发现以下设备：</p>
                                    <div class="table-responsive">
                                        <table class="table">
                                            <thead>
                                                <tr>
                                                    <th>IP地址</th>
                                                    <th>类型</th>
                                                    <th>状态</th>
                                                    <th>响应时间</th>
                                                    <th>操作</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr>
                                                    <td>10.1.101.1</td>
                                                    <td>AntBox站点</td>
                                                    <td><span class="status-badge status-online">在线</span></td>
                                                    <td>42ms</td>
                                                    <td><button class="btn btn-sm btn-primary" onclick="addSite('10.1.101.1')">添加</button></td>
                                                </tr>
                                                <tr>
                                                    <td>10.1.102.1</td>
                                                    <td>AntBox站点</td>
                                                    <td><span class="status-badge status-online">在线</span></td>
                                                    <td>38ms</td>
                                                    <td><button class="btn btn-sm btn-primary" onclick="addSite('10.1.102.1')">添加</button></td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    this.showToast('扫描完成！', 'success');
                }
            }, 200);
        }
    }
    
    // 处理用水量数据
    handleWaterUsage(form) {
        const date = form.querySelector('#water-date').value;
        const time = form.querySelector('#water-time').value;
        const usage = form.querySelector('#water-usage').value;
        
        // 模拟数据保存
        const waterData = {
            dateTime: `${date} ${time}`,
            usage: parseFloat(usage),
            timestamp: new Date().toISOString()
        };
        
        // 保存到localStorage（实际应使用API）
        const existingData = JSON.parse(localStorage.getItem('waterUsageData') || '[]');
        existingData.push(waterData);
        localStorage.setItem('waterUsageData', JSON.stringify(existingData));
        
        this.showToast('用水量数据已保存', 'success');
        form.reset();
        
        // 更新用水量显示
        this.updateWaterUsageDisplay();
    }
    
    // 更新用水量显示
    updateWaterUsageDisplay() {
        const displayElement = document.getElementById('water-usage-display');
        if (!displayElement) return;
        
        const data = JSON.parse(localStorage.getItem('waterUsageData') || '[]');
        if (data.length === 0) {
            displayElement.innerHTML = '<p>暂无用水量数据</p>';
            return;
        }
        
        // 计算统计信息
        const totalUsage = data.reduce((sum, item) => sum + item.usage, 0);
        const avgUsage = totalUsage / data.length;
        
        displayElement.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">用水量统计</h3>
                </div>
                <div class="card-body">
                    <div class="grid grid-3">
                        <div class="stat-card">
                            <h4>总记录数</h4>
                            <p class="stat-value">${data.length}</p>
                        </div>
                        <div class="stat-card">
                            <h4>总用水量</h4>
                            <p class="stat-value">${totalUsage.toFixed(2)} m³</p>
                        </div>
                        <div class="stat-card">
                            <h4>平均用量</h4>
                            <p class="stat-value">${avgUsage.toFixed(2)} m³/次</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // 显示Toast通知
    showToast(message, type = 'info') {
        // 移除现有toast
        const existingToast = document.querySelector('.toast');
        if (existingToast) existingToast.remove();
        
        // 创建新toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="toast-icon ${this.getToastIcon(type)}"></i>
                <span class="toast-message">${message}</span>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        // 添加到页面
        document.body.appendChild(toast);
        
        // 自动移除
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 3000);
    }
    
    getToastIcon(type) {
        switch(type) {
            case 'success': return 'fas fa-check-circle';
            case 'error': return 'fas fa-exclamation-circle';
            case 'warning': return 'fas fa-exclamation-triangle';
            default: return 'fas fa-info-circle';
        }
    }
    
    // 初始化图表
    initCharts() {
        // 如果页面中有ECharts容器，初始化它们
        const chartElements = document.querySelectorAll('.echarts-container');
        chartElements.forEach(element => {
            const chartType = element.getAttribute('data-chart-type');
            const chartId = element.id;
            
            if (chartId) {
                this.initChart(chartId, chartType);
            }
        });
    }
    
    // 初始化单个图表
    initChart(chartId, chartType) {
        const chart = echarts.init(document.getElementById(chartId));
        
        // 根据图表类型设置选项
        let option;
        switch(chartType) {
            case 'temperature':
                option = this.getTemperatureChartOption();
                break;
            case 'power':
                option = this.getPowerChartOption();
                break;
            case 'water':
                option = this.getWaterChartOption();
                break;
            default:
                option = this.getDefaultChartOption();
        }
        
        chart.setOption(option);
        
        // 响应窗口大小变化
        window.addEventListener('resize', () => {
            chart.resize();
        });
    }
    
    // 获取温度图表选项
    getTemperatureChartOption() {
        return {
            tooltip: {
                trigger: 'axis'
            },
            legend: {
                data: ['供液温度', '回液温度', '设定温度']
            },
            xAxis: {
                type: 'category',
                data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
            },
            yAxis: {
                type: 'value',
                name: '温度 (°C)'
            },
            series: [
                {
                    name: '供液温度',
                    type: 'line',
                    data: [25.3, 24.8, 26.1, 25.7, 25.9, 25.5],
                    smooth: true,
                    lineStyle: { color: '#1890ff' }
                },
                {
                    name: '回液温度',
                    type: 'line',
                    data: [28.5, 27.9, 29.2, 28.8, 29.1, 28.7],
                    smooth: true,
                    lineStyle: { color: '#52c41a' }
                },
                {
                    name: '设定温度',
                    type: 'line',
                    data: [25.0, 25.0, 25.0, 25.0, 25.0, 25.0],
                    smooth: true,
                    lineStyle: { color: '#faad14', type: 'dashed' }
                }
            ]
        };
    }
    
    // 获取页面标题
    getPageTitle(pageName) {
        const titles = {
            'dashboard': '仪表盘',
            'site-detail': '站点详情',
            'monitoring-wall': '实时监控墙',
            'all-sites': '全部站点',
            'site-scan': '站点扫描',
            'water-usage': '用水量管理',
            'admin': '账号管理',
            'login': '登录'
        };
        
        return titles[pageName] || '未知页面';
    }
    
    // 模拟页面内容
    getDashboardContent() {
        return '<h1>仪表盘</h1><p>这是仪表盘内容...</p>';
    }
    
    getSiteDetailContent() {
        return '<h1>站点详情</h1><p>这是站点详情内容...</p>';
    }
    
    getMonitoringWallContent() {
        return '<h1>实时监控墙</h1><p>这是监控墙内容...</p>';
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AppCommon();
});

// 全局辅助函数
function formatDate(date) {
    return new Date(date).toLocaleString('zh-CN');
}

function formatNumber(num, decimals = 2) {
    return parseFloat(num).toFixed(decimals);
}

function addSite(ipAddress) {
    if (window.app) {
        window.app.showToast(`已添加站点: ${ipAddress}`, 'success');
        // 这里可以调用API添加站点
    }
}

function toggleMonitoring(siteId) {
    const button = document.getElementById(`monitor-btn-${siteId}`);
    if (button) {
        const isActive = button.classList.contains('active');
        if (isActive) {
            button.classList.remove('active');
            button.innerHTML = '<i class="fas fa-play"></i> 开启监控';
            // 停止视频流
        } else {
            button.classList.add('active');
            button.innerHTML = '<i class="fas fa-stop"></i> 停止监控';
            // 开始视频流
        }
    }
}

// 视频播放器管理
class VideoPlayerManager {
    constructor() {
        this.players = new Map();
        this.maxSimultaneousStreams = 4; // 同时最多4个视频流
        this.activeStreams = 0;
    }
    
    createPlayer(containerId, streamUrl, options = {}) {
        if (this.activeStreams >= this.maxSimultaneousStreams) {
            console.warn('已达到最大同时视频流数量');
            return null;
        }
        
        // 使用HLS.js或video.js等（实际应集成具体播放器）
        const container = document.getElementById(containerId);
        if (!container) return null;
        
        const video = document.createElement('video');
        video.className = 'video-player';
        video.controls = true;
        video.autoplay = options.autoplay || false;
        video.muted = options.muted || true; // 默认静音
        
        const source = document.createElement('source');
        source.src = streamUrl;
        source.type = 'application/x-mpegURL'; // HLS流
        
        video.appendChild(source);
        container.appendChild(video);
        
        const player = {
            element: video,
            url: streamUrl,
            isPlaying: false,
            startTime: Date.now()
        };
        
        this.players.set(containerId, player);
        this.activeStreams++;
        
        // 监听结束事件清理资源
        video.addEventListener('ended', () => {
            this.destroyPlayer(containerId);
        });
        
        return player;
    }
    
    destroyPlayer(containerId) {
        const player = this.players.get(containerId);
        if (player) {
            player.element.pause();
            player.element.remove();
            this.players.delete(containerId);
            this.activeStreams = Math.max(0, this.activeStreams - 1);
        }
    }
    
    destroyAll() {
        this.players.forEach((player, containerId) => {
            this.destroyPlayer(containerId);
        });
    }
}

// 全局视频播放器实例
window.videoPlayerManager = new VideoPlayerManager();