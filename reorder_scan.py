import re

with open("/root/.openclaw/workspace/pages/scan.html", "r", encoding="utf-8") as f:
    html = f.read()

# Blocks:
# 1. scan-control-panel (IP范围扫描配置)
# 2. scan-progress (扫描进度)
# 3. scan-results (扫描结果)
# 4. scan-log (扫描日志) - leave at bottom

# Extract the blocks
def extract_block(text, start_comment, end_comment=None):
    if end_comment:
        pattern = re.compile(rf'({start_comment}.*?{end_comment})', re.DOTALL)
    else:
        pattern = re.compile(rf'({start_comment}.*?)(?=<!-- \w+ -->|</main>)', re.DOTALL)
    m = pattern.search(text)
    return m.group(1) if m else ""

b1 = extract_block(html, r"<!-- 扫描控制面板 -->")
b2 = extract_block(html, r"<!-- 扫描进度 -->")
b3 = extract_block(html, r"<!-- 扫描结果 -->")

# Find where to replace
start_idx = html.find("<!-- 扫描控制面板 -->")
end_idx = html.find("<!-- 扫描日志 -->")

if start_idx != -1 and end_idx != -1 and b1 and b2 and b3:
    # New order: 扫描结果 -> 扫描进度 -> 扫描控制面板
    new_content = b3 + "\n" + b2 + "\n" + b1 + "\n"
    new_html = html[:start_idx] + new_content + html[end_idx:]
    with open("/root/.openclaw/workspace/pages/scan.html", "w", encoding="utf-8") as f:
        f.write(new_html)
    print("Reordered successfully.")
else:
    print("Failed to find blocks.")
