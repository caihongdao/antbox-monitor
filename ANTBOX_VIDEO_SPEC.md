# AntBox 监控视频技术方案

## 📹 监控视频规格信息

### 视频编码格式
| 编码 | 说明 | 带宽占用 | 兼容性 |
|------|------|---------|--------|
| **H.264** | 最广泛支持 | 中等 | ✅ 所有浏览器原生支持 |
| **H.265 (HEVC)** | 高效压缩 | 比 H.264 少 50% | ⚠️ 部分浏览器支持 (Safari/Edge) |

### 分辨率规格
| 分辨率 | 名称 | 像素 | 适用场景 |
|--------|------|------|---------|
| **720P** | HD | 1280×720 | 基础监控，带宽受限 |
| **1080P** | Full HD | 1920×1080 | 标准监控，清晰度好 |
| **2K/4MP** | 2K | 2560×1440 | 高清监控 |
| **4K** | Ultra HD | 3840×2160 | 超高清，带宽要求高 |

### 码率参考
| 分辨率 | H.264 码率 | H.265 码率 |
|--------|-----------|-----------|
| 720P | 2-4 Mbps | 1-2 Mbps |
| 1080P | 4-8 Mbps | 2-4 Mbps |
| 2K | 8-12 Mbps | 4-6 Mbps |
| 4K | 15-25 Mbps | 8-12 Mbps |

### 流量计算 (单路视频)
```
1080P @ H.264 @ 6Mbps:
- 每小时：6Mbps × 3600s ÷ 8 = 2.7 GB/小时
- 每天：2.7 × 24 = 64.8 GB/天
- 每月：64.8 × 30 = 1.94 TB/月

1080P @ H.265 @ 3Mbps:
- 每小时：3Mbps × 3600s ÷ 8 = 1.35 GB/小时
- 每天：1.35 × 24 = 32.4 GB/天
- 每月：32.4 × 30 = 0.97 TB/月
```

---

## 🔄 方案对比

### 方案 A: 客户端 Web 页面直连 AntBox 设备

```
用户浏览器 → AntBox 设备 (RTSP/HTTP-FLV)
```

**优点**:
- ✅ 服务器零带宽压力
- ✅ 低延迟（直连设备）
- ✅ 服务器无需存储/转发
- ✅ 扩展性好（156 个站点不影响服务器）

**缺点**:
- ❌ 需要 AntBox 设备支持 Web 视频流
- ❌ 跨域问题 (CORS) 需要解决
- ❌ 浏览器需要支持对应编码
- ❌ 客户端带宽压力大（多路同时观看时）
- ❌ 设备 IP 暴露给客户端（安全风险）

**技术实现**:
```html
<!-- 方式 1: video 标签 (HLS) -->
<video src="http://10.1.101.1/stream.m3u8" autoplay></video>

<!-- 方式 2: flv.js (HTTP-FLV) -->
<script src="flv.min.js"></script>
<video id="video"></video>
<script>
  const flvPlayer = flvjs.createPlayer({
    type: 'flv',
    url: 'http://10.1.101.1/live.flv'
  });
  flvPlayer.attachMediaElement(document.getElementById('video'));
  flvPlayer.play();
</script>

<!-- 方式 3: WebRTC (低延迟) -->
<video id="video" autoplay></video>
<script>
  const pc = new RTCPeerConnection();
  // WebRTC 连接逻辑
</script>
```

**浏览器兼容性**:
| 协议 | Chrome | Firefox | Safari | Edge |
|------|--------|---------|--------|------|
| HLS (.m3u8) | ✅ | ✅ | ✅ 原生 | ✅ |
| HTTP-FLV | ⚠️ (需 flv.js) | ⚠️ (需 flv.js) | ❌ | ⚠️ (需 flv.js) |
| WebRTC | ✅ | ✅ | ✅ | ✅ |
| RTSP | ❌ | ❌ | ❌ | ❌ (需转码) |

---

### 方案 B: 服务器中转

```
用户浏览器 → 监控服务器 (192.168.0.57) → AntBox 设备
```

**优点**:
- ✅ 设备 IP 不暴露（安全）
- ✅ 统一认证授权
- ✅ 可转码适配不同客户端
- ✅ 可录制存储
- ✅ 跨域问题易解决

**缺点**:
- ❌ 服务器带宽压力大
- ❌ 服务器需要 GPU 解码/转码
- ❌ 延迟增加（中转）
- ❌ 单点故障风险

**带宽需求计算** (156 个站点):
```
假设 10% 站点同时观看 (16 路):
- H.264 1080P @ 6Mbps × 16 = 96 Mbps
- H.265 1080P @ 3Mbps × 16 = 48 Mbps

假设 100% 站点同时观看 (156 路):
- H.264 1080P @ 6Mbps × 156 = 936 Mbps (接近 1Gbps)
- H.265 1080P @ 3Mbps × 156 = 468 Mbps
```

**技术实现**:
```python
# FFmpeg 转码示例
ffmpeg -i rtsp://10.1.101.1/stream \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -f flv rtmp://localhost/live/stream1
```

---

## 🖥️ GPU 解码方案

### 浏览器 GPU 解码能力

**WebCodecs API** (Chrome 94+, Edge 94+):
```javascript
// 检查 GPU 解码支持
if ('VideoDecoder' in window) {
  console.log('✅ 支持 WebCodecs GPU 解码');
} else {
  console.log('❌ 不支持 WebCodecs');
}

// H.265 支持检测
const supportHEVC = await navigator.mediaCapabilities.decodingInfo({
  type: 'file',
  video: {
    contentType: 'video/mp4; codecs="hvc1.1.6.L93.B0"',
    width: 1920,
    height: 1080,
    bitrate: 3000000,
    framerate: 30
  }
});
console.log('H.265 支持:', supportHEVC.supported);
```

**浏览器支持情况**:
| 浏览器 | H.264 | H.265 | VP9 | AV1 |
|--------|-------|-------|-----|-----|
| Chrome | ✅ | ⚠️ (硬件) | ✅ | ✅ |
| Firefox | ✅ | ❌ | ✅ | ✅ |
| Safari | ✅ | ✅ | ✅ | ✅ |
| Edge | ✅ | ✅ | ✅ | ✅ |

### GPU 解码方案对比

| 方案 | 位置 | 优点 | 缺点 |
|------|------|------|------|
| **浏览器 GPU** | 客户端 | 服务器零负载，扩展性好 | 依赖客户端硬件 |
| **服务器 GPU** | 服务器 | 统一转码，兼容性好 | 服务器成本高 |
| **混合方案** | 两者 | 灵活适配 | 实现复杂 |

---

## 📊 推荐方案

### 针对 156 个站点的监控墙

**推荐：方案 A (客户端直连) + HLS 协议**

**理由**:
1. **带宽**: 156 个站点，服务器中转需要近 1Gbps 带宽，成本太高
2. **延迟**: 直连延迟 < 1 秒，中转延迟 2-5 秒
3. **扩展性**: 客户端直连无服务器瓶颈
4. **兼容性**: HLS 所有浏览器支持

**架构**:
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ 用户浏览器   │────▶│ 监控服务器    │────▶│ AntBox 设备  │
│ (Web 页面)   │◀────│ (API 管理)    │◀────│ (视频流)    │
└─────────────┘     └──────────────┘     └─────────────┘
      │                                         │
      └─────────────────────────────────────────┘
                    直连视频流 (HLS)
```

**实现步骤**:

1. **AntBox 设备端**:
   - 确认是否支持 HLS 输出
   - 如不支持，部署 mini-ffmpeg 转码

2. **服务器端**:
   - 提供设备列表 API（包含视频流 URL）
   - 处理认证授权
   - 不转发视频流

3. **客户端**:
   ```html
   <video 
     id="video" 
     autoplay 
     muted 
     playsinline
     style="width: 100%; height: 100%;">
   </video>
   <script>
     // HLS.js (Chrome/Firefox/Edge)
     if (Hls.isSupported()) {
       const hls = new Hls();
       hls.loadSource('http://10.1.101.1/stream.m3u8');
       hls.attachMedia(document.getElementById('video'));
     }
     // Safari 原生支持
     else if (video.canPlayType('application/vnd.apple.mpegurl')) {
       video.src = 'http://10.1.101.1/stream.m3u8';
     }
   </script>
   ```

---

## ⚠️ 注意事项

### 1. 跨域问题 (CORS)
```
AntBox 设备需要设置响应头:
Access-Control-Allow-Origin: *
```

### 2. 混合内容 (Mixed Content)
```
如果监控页面是 HTTPS，视频流也必须是 HTTPS
解决方案:
- AntBox 设备启用 HTTPS
- 或使用反向代理 (Nginx)
```

### 3. 网络隔离
```
如果 AntBox 设备在内网 (10.1.x.x):
- 用户浏览器需要能访问内网
- 或通过 VPN/跳板机
```

### 4. 并发连接数
```
AntBox 设备通常限制并发连接数 (4-10 路)
解决方案:
- 使用流媒体服务器中转
- 或限制同时观看人数
```

---

## 📋 待确认信息

请确认以下 AntBox 设备信息:

1. **视频输出接口**:
   - [ ] 是否支持 RTSP?
   - [ ] 是否支持 HTTP-FLV?
   - [ ] 是否支持 HLS (.m3u8)?
   - [ ] 是否支持 WebRTC?

2. **视频规格**:
   - [ ] 编码格式：H.264 / H.265 / 其他？
   - [ ] 分辨率：720P / 1080P / 2K / 4K?
   - [ ] 码率：____ Mbps
   - [ ] 帧率：____ fps

3. **访问方式**:
   - [ ] 视频流 URL 格式：_________________
   - [ ] 是否需要认证？是/否
   - [ ] 并发连接数限制：____ 路

4. **网络环境**:
   - [ ] AntBox 设备 IP 是否可被客户端直接访问？
   - [ ] 是否需要经过 NAT/防火墙？

---

*Created: 2026-02-23 15:40 (Asia/Muscat)*
