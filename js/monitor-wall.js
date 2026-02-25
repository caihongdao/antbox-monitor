/**
 * 大屏监控墙 JS 逻辑
 */

// 开启/退出全屏
function toggleFullScreen() {
    const doc = window.document;
    const docEl = doc.documentElement;
    const btn = document.getElementById('fs-btn');

    const requestFullScreen = docEl.requestFullscreen || docEl.mozRequestFullScreen || docEl.webkitRequestFullScreen || docEl.msRequestFullscreen;
    const cancelFullScreen = doc.exitFullscreen || doc.mozCancelFullScreen || doc.webkitExitFullscreen || doc.msExitFullscreen;

    if (!doc.fullscreenElement && !doc.mozFullScreenElement && !doc.webkitFullscreenElement && !doc.msFullscreenElement) {
        requestFullScreen.call(docEl);
        btn.innerHTML = '<i class="fas fa-compress"></i> 退出';
    } else {
        cancelFullScreen.call(doc);
        btn.innerHTML = '<i class="fas fa-expand"></i> 全屏';
    }
}

// 实时时钟更新
function updateClock() {
    const now = new Date();
    document.getElementById('clock').innerText = now.toLocaleString('zh-CN', { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();

// 数据抓取逻辑
class MonitorWall {
    constructor() {
        this.pollInterval = 10000; // 每 10 秒刷新一次
        this.init();
    }

    async init() {
        await this.fetchData();
        setInterval(() => this.fetchData(), this.pollInterval);
    }

    async fetchData() {
        try {
            // 获取全部站点
            const sitesRes = await fetch('/api/sites');
            const sites = await sitesRes.json();
            
            // 获取概览数据
            const overviewRes = await fetch('/api/dashboard/overview');
            const overview = await overviewRes.json();

            // 获取实时报警
            const alertsRes = await fetch('/api/alerts?status=active&limit=10');
            const alerts = await alertsRes.json();

            this.renderStats(overview);
            this.renderGrid(sites);
            this.renderAlerts(alerts);
        } catch (error) {
            console.error("无法获取监控数据:", error);
        }
    }

    renderStats(overview) {
        document.getElementById('total-sites').innerText = overview.total_sites || 0;
        document.getElementById('online-sites').innerText = overview.online_sites || 0;
        document.getElementById('offline-sites').innerText = overview.offline_sites || 0;
        document.getElementById('alarm-sites').innerText = overview.active_alerts || 0;
    }

    renderGrid(sites) {
        const grid = document.getElementById('wall-grid');
        grid.innerHTML = '';

        if (!sites || sites.length === 0) {
            grid.innerHTML = '<div style="color:var(--text-muted);">暂无站点数据</div>';
            return;
        }

        sites.forEach(site => {
            const isOnline = site.status === 'online';
            const hasAlarm = site.status === 'alarm'; // 假设如果有报警，status会是 alarm
            
            let cardClass = isOnline ? 'status-online' : 'status-offline';
            if (hasAlarm) cardClass = 'status-alarm';

            const temp = site.env_temp || site.in_water_temp || 0;
            const hashrate = site.hashrate || 0;
            
            // 阈值标红逻辑
            const tempClass = temp > 40 ? 'temp-high' : '';
            const hashClass = (isOnline && hashrate < 50) ? 'hashrate-low' : '';

            const cardHtml = `
                <div class="site-card ${cardClass}">
                    <div class="card-header">
                        <span>${site.name || site.ip_address}</span>
                        <i class="fas ${isOnline ? 'fa-check-circle' : 'fa-times-circle'}" 
                           style="color: var(--${isOnline ? 'success' : 'error'}-color);"></i>
                    </div>
                    <div class="card-metrics">
                        <div class="metric">
                            <span class="metric-label">类型</span>
                            <span class="metric-value" style="font-size: 14px;">${site.device_type || '未知'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">状态</span>
                            <span class="metric-value" style="font-size: 14px; color: var(--${isOnline ? 'success' : 'error'}-color);">
                                ${isOnline ? '在线' : '离线'}
                            </span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">温度</span>
                            <span class="metric-value ${tempClass}">${temp > 0 ? temp.toFixed(1) + ' °C' : '--'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">算力</span>
                            <span class="metric-value ${hashClass}">${hashrate > 0 ? hashrate.toFixed(1) + ' T' : '--'}</span>
                        </div>
                    </div>
                </div>
            `;
            grid.innerHTML += cardHtml;
        });
    }

    renderAlerts(alerts) {
        const list = document.getElementById('alert-list');
        list.innerHTML = '';

        if (!alerts || alerts.length === 0) {
            list.innerHTML = `
                <div style="color: var(--text-muted); text-align: center; margin-top: 50px;">
                    <i class="fas fa-shield-alt fa-3x" style="opacity: 0.5; margin-bottom: 10px;"></i>
                    <p>当前暂无活跃告警</p>
                </div>
            `;
            return;
        }

        alerts.forEach(alert => {
            const time = new Date(alert.triggered_at).toLocaleString('zh-CN', {
                month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
            const html = `
                <div class="alert-item">
                    <div class="alert-title">
                        <i class="fas fa-exclamation-triangle"></i> 
                        ${alert.site_name || ('Site ' + alert.site_id)} - ${alert.rule_name}
                    </div>
                    <div class="alert-desc">${alert.message}</div>
                    <div class="alert-time">${time}</div>
                </div>
            `;
            list.innerHTML += html;
        });
    }
}

// 页面加载完成后启动
document.addEventListener('DOMContentLoaded', () => {
    new MonitorWall();
});