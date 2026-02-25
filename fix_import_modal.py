import re

with open("/root/.openclaw/workspace/js/scan_backend.js", "r") as f:
    js = f.read()

old_code = """    showImportModal() {
        const selectedIPs = Array.from(document.querySelectorAll('.result-checkbox:checked'))
            .map(cb => cb.value);"""

new_code = """    showImportModal() {
        // Only select checked boxes that are in VISIBLE rows
        const selectedIPs = Array.from(document.querySelectorAll('.result-row'))
            .filter(row => row.style.display !== 'none')
            .map(row => row.querySelector('.result-checkbox'))
            .filter(cb => cb && cb.checked)
            .map(cb => cb.value);"""

js = js.replace(old_code, new_code)

old_confirm = """    async confirmImport() {
        const selectedIPs = Array.from(document.querySelectorAll('.result-checkbox:checked'))
            .map(cb => cb.value);"""

new_confirm = """    async confirmImport() {
        const selectedIPs = Array.from(document.querySelectorAll('.result-row'))
            .filter(row => row.style.display !== 'none')
            .map(row => row.querySelector('.result-checkbox'))
            .filter(cb => cb && cb.checked)
            .map(cb => cb.value);"""

js = js.replace(old_confirm, new_confirm)

with open("/root/.openclaw/workspace/js/scan_backend.js", "w") as f:
    f.write(js)
