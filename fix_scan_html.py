with open("/root/.openclaw/workspace/pages/scan.html.broken", "r", encoding="utf-8") as f:
    html = f.read()

# I want to extract the three parts properly:
# We know the original blocks from scan.html.broken are mangled.
# Let's just find the parts and fix them.

import re

# We need the top part until "<!-- 扫描结果 -->"
top_part = html[:html.find("<!-- 扫描结果 -->")]

# Now extract block 1 (scan control panel)
# It starts at <!-- 扫描控制面板 --> and goes to <!-- 扫描日志 -->
p_control = html.find("<!-- 扫描控制面板 -->")
p_log = html.find("<!-- 扫描日志 -->")
control_panel = html[p_control:p_log]

# Block 2 (scan progress)
p_progress = html.find("<!-- 扫描进度 -->")
progress_panel = html[p_progress:p_control]

# Block 3 (scan results)
results_panel = html[html.find("<!-- 扫描结果 -->"):p_progress]

# Now FIX results_panel!
fixed_results = results_panel + """
                                <tr class="no-results" id="no-results-row">
                                    <td colspan="8" style="text-align: center; padding: 20px;">
                                        <div class="empty-state">
                                            <i class="fas fa-search fa-3x" style="color: #ccc; margin-bottom: 10px;"></i>
                                            <p style="color: #888;">暂无扫描数据，请先配置并开始扫描</p>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="result-summary" id="result-summary" style="display: none;">
                        <h3><i class="fas fa-chart-pie"></i> 扫描统计摘要</h3>
                        <div class="summary-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 15px;">
                            <div class="summary-item"><div class="summary-label">扫描IP范围</div><div class="summary-value" id="summary-range">-</div></div>
                            <div class="summary-item"><div class="summary-label">总IP数量</div><div class="summary-value" id="summary-total-ips">0</div></div>
                            <div class="summary-item"><div class="summary-label">已扫描IP</div><div class="summary-value" id="summary-scanned-ips">0</div></div>
                            <div class="summary-item"><div class="summary-label">在线设备</div><div class="summary-value" id="summary-online">0</div></div>
                            <div class="summary-item"><div class="summary-label">AntBox设备</div><div class="summary-value" id="summary-antbox">0</div></div>
                            <div class="summary-item"><div class="summary-label">矿机设备</div><div class="summary-value" id="summary-miner">0</div></div>
                            <div class="summary-item"><div class="summary-label">成功率</div><div class="summary-value" id="summary-success-rate">0%</div></div>
                            <div class="summary-item"><div class="summary-label">总用时</div><div class="summary-value" id="summary-total-time">00:00</div></div>
                        </div>
                    </div>
                </div>
                <div class="card-footer" style="padding: 15px; border-top: 1px solid #eaeaea; display: flex; gap: 10px;">
                    <button class="btn btn-primary" id="import-selected" disabled><i class="fas fa-upload"></i> 导入选中设备</button>
                    <button class="btn btn-secondary" id="clear-results"><i class="fas fa-trash"></i> 清空结果</button>
                </div>
            </div>
"""

# Now assemble them in the right order!
# User requested: 扫描结果 -> 扫描进度 -> 扫描控制面板
# Wait, user said: "把 扫描结果 和IP范围扫描配置 位置互换 扫描进度放在 扫描结果 和IP范围扫描配置中间"
# which means:
# 1. IP Range Scan Config (Top? Or Bottom?)
# Original: 1. Config, 2. Progress, 3. Results.
# They said "Swap Results and Config. Progress stays between them."
# So: 1. Results, 2. Progress, 3. Config.

# But wait, they also want to embed this in dashboard.html! 
# "把此页面作为主页 https://192.168.0.57:8443/ 然后参考图片 把继续完善 功能模块... 按照此页面造型嵌入到主页中"
# This means I should copy the `app-header` module styling to `dashboard.html`!
# And they want `dashboard.html` to have the exact same navigation look as `scan.html`!

# Let's fix scan.html first.
bottom_part = html[p_log:]

new_html = top_part + "\n" + fixed_results + "\n" + progress_panel + "\n" + control_panel + "\n" + bottom_part

with open("/root/.openclaw/workspace/pages/scan.html", "w", encoding="utf-8") as f:
    f.write(new_html)

print("scan.html fixed")
