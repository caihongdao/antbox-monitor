import aiohttp
import logging
import json
import os

logger = logging.getLogger("alert_notifier")

# 报警配置
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "alert_config.json")

def load_config():
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载报警配置失败: {e}")
    
    # 默认配置 (预置用户的 Telegram)
    return {
        "enable_telegram": True,
        "telegram_bot_token": "", # 请填入Bot Token
        "telegram_chat_id": "5943009645",
        "enable_wechat": False,
        "wechat_webhook": "" # 企业微信机器人Webhook
    }

async def send_telegram_alert(message: str, config: dict):
    token = config.get("telegram_bot_token")
    chat_id = config.get("telegram_chat_id")
    
    if not token or not chat_id:
        logger.warning("Telegram 未配置 Bot Token，跳过推送")
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"🚨 **AntBox 报警通知** 🚨\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=5) as resp:
                if resp.status == 200:
                    logger.info("Telegram 报警推送成功")
                    return True
                else:
                    logger.error(f"Telegram 推送失败: {await resp.text()}")
                    return False
    except Exception as e:
        logger.error(f"Telegram 网络请求错误: {e}")
        return False

async def send_wechat_alert(message: str, config: dict):
    webhook = config.get("wechat_webhook")
    if not webhook:
        logger.warning("WeChat 未配置 Webhook，跳过推送")
        return False
        
    payload = {
        "msgtype": "text",
        "text": {
            "content": f"🚨 AntBox 报警通知 🚨\n\n{message}"
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook, json=payload, timeout=5) as resp:
                if resp.status == 200:
                    logger.info("微信报警推送成功")
                    return True
                else:
                    logger.error(f"微信推送失败: {await resp.text()}")
                    return False
    except Exception as e:
        logger.error(f"微信网络请求错误: {e}")
        return False

async def notify_all(site_id: int, rule_name: str, message: str, value: float):
    config = load_config()
    
    alert_text = (
        f"**站点**: {site_id}\n"
        f"**规则**: {rule_name}\n"
        f"**当前值**: {value}\n"
        f"**详情**: {message}\n"
        f"请及时登录控制台处理！"
    )
    
    if config.get("enable_telegram"):
        await send_telegram_alert(alert_text, config)
        
    if config.get("enable_wechat"):
        await send_wechat_alert(alert_text, config)

# 用于本地测试
if __name__ == "__main__":
    import asyncio
    asyncio.run(notify_all(101, "高温报警", "温度超过阈值", 42.5))
