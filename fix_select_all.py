with open('/root/.openclaw/workspace/js/scan_backend.js', 'r') as f:
    js = f.read()

# Modify toggleSelectAll to only select visible rows (filtered rows)
old_func = """    // 全选/取消全选
    toggleSelectAll(checked) {
        document.querySelectorAll('.result-checkbox').forEach(checkbox => {
            checkbox.checked = checked;
        });"""

new_func = """    // 全选/取消全选
    toggleSelectAll(checked) {
        document.querySelectorAll('.result-row').forEach(row => {
            if (row.style.display !== 'none') {
                const checkbox = row.querySelector('.result-checkbox');
                if (checkbox) checkbox.checked = checked;
            }
        });"""

js = js.replace(old_func, new_func)

with open('/root/.openclaw/workspace/js/scan_backend.js', 'w') as f:
    f.write(js)
