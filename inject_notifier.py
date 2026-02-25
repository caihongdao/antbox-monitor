import sys

def inject_alert_notifier(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Import statement
    if "from alert_notifier import notify_all" not in content:
        content = content.replace("import logging", "import logging\nfrom alert_notifier import notify_all")

    # The exact block to replace
    old_log = "logger.info(f\"触发报警：{rule['name']} - 站点 {latest['site_id']}\")"
    new_log = """logger.info(f"触发报警：{rule['name']} - 站点 {latest['site_id']}")
                    import asyncio
                    asyncio.create_task(notify_all(
                        latest['site_id'], 
                        rule['name'], 
                        f"检测到异常值 {latest['value']} (阈值 {rule['threshold_value']})", 
                        float(latest['value'])
                    ))"""

    if "notify_all(" not in content and old_log in content:
        content = content.replace(old_log, new_log)
        
    with open(filepath, 'w') as f:
        f.write(content)
    
    print("Injected alert_notifier into", filepath)

if __name__ == "__main__":
    inject_alert_notifier("api_server.py")