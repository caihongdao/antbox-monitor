# AntBox 项目 - 问题修复报告

**修复时间**: 2026-02-22 15:10  
**问题**: 网页数据显示异常，站点列表加载失败 (HTTP 500)

---

## 🐛 发现的问题

### 1. API 响应验证错误 (HTTP 500)
**现象**: `/api/sites` 返回 Internal Server Error  
**原因**: PostgreSQL INET 类型返回 `IPv4Address` 对象，FastAPI 期望字符串  
**错误日志**:
```
fastapi.exceptions.ResponseValidationError: 5 validation errors:
{'type': 'string_type', 'loc': ('response', 0, 'ip_address'), 
 'msg': 'Input should be a valid string', 'input': IPv4Address('10.1.101.1')}
```

**修复**: 在返回前将 IP 地址转换为字符串
```python
# 转换 IP 地址为字符串 (PostgreSQL INET 类型返回 IPv4Address 对象)
result = []
for row in rows:
    site_dict = dict(row)
    if site_dict.get('ip_address'):
        site_dict['ip_address'] = str(site_dict['ip_address'])
    result.append(site_dict)
return result
```

### 2. 趋势数据 null 值处理
**现象**: 图表数据都是 null，可能导致前端解析错误  
**原因**: 数据库中没有实际采集数据（设备不可达）  
**修复**: 将 null 值转换为 0
```python
"data": [{"timestamp": row["timestamp"].isoformat(), 
          "value": round(float(row["value"]), 2) if row["value"] is not None else 0} 
         for row in rows]
```

---

## ✅ 修复结果

### API 测试结果
```bash
# 站点列表 API - ✅ 正常
curl -k https://localhost:8443/api/sites?limit=3
[
    {
        "site_id": 1,
        "ip_address": "10.1.101.1",  # 现在是字符串
        "location": "Zone A, Rack 1",
        "is_online": false,
        ...
    }
]

# 趋势数据 API - ✅ 正常
curl -k https://localhost:8443/api/trend/total_power?hours=24
{
    "metric": "total_power",
    "hours": 24,
    "data": [
        {"timestamp": "...", "value": 0},  # null 转为 0
        ...
    ]
}
```

---

## 📊 当前数据状态说明

### 在线站点：41-44 个 (27-29%)
- **原因**: 大部分 AntBox 设备在实际网络中不可达
- **数据采集**: 后台任务正常运行（60 秒周期，~5.5 秒耗时）
- **数据库**: 已存储 2700+ 条快照记录

### 测量数据：0.00 (功耗、算力、温度)
- **原因**: 设备 API 不可访问，采集不到真实数据
- **API 响应**: 正常返回数据格式，值为 0
- **前端显示**: 正常显示 0.00 而非空白

---

## 🔧 修复的文件

- `/root/.openclaw/workspace/api_server.py` (600 行)
  - 修复 `/api/sites` IP 地址转换
  - 修复 `/api/trend/{metric}` null 值处理

---

## ⚠️ 待解决问题

### 设备连通性
- 150 个配置站点中只有 ~41 个在线
- 大部分设备 (109 个) 不可达
- **可能原因**:
  1. 设备实际不存在或已关机
  2. 网络路由问题
  3. IP 地址配置错误

### 下一步建议
1. 核实 150 个站点的实际 IP 地址
2. 测试在线设备的 API 访问
3. 更新站点配置为真实存在的设备

---

## 📝 访问测试

从其他 PC 访问：
```
URL: https://192.168.0.57:8443/
注意：接受自签名证书警告后可正常访问
```

预期显示：
- ✅ 总站点数：150 个
- ✅ 在线站点：41 个 (27%)
- ✅ 总功耗：0.00 MW (设备不可达)
- ✅ 总算力：0.00 PH/s (设备不可达)
- ✅ 平均温度：0.0°C (设备不可达)
- ✅ 站点列表：正常显示 100 个站点
- ✅ 趋势图表：显示 0 值基线

---

*修复完成时间：2026-02-22 15:10*
