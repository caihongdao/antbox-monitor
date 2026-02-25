import re

with open("/root/.openclaw/workspace/js/scan_backend.js", "r") as f:
    js = f.read()

# Replace AppCommon.showToast with simple alert or local UI toast if possible, 
# or just console.log for now so it doesn't break the thread.
# Actually, let's create a global AppCommon if missing, with static methods.
patch = """
// 确保 AppCommon 存在
if (typeof AppCommon === 'undefined' || typeof AppCommon.showToast !== 'function') {
    window.AppCommon = {
        showToast: function(msg, type) {
            console.log('[' + type + '] ' + msg);
            // 简单的原生弹窗替代，如果是重要信息
            if (type === 'error') {
                alert(msg);
            }
        },
        showModal: function(title, html) {
            alert(title + "\\n" + html.replace(/<[^>]*>?/gm, ''));
        }
    };
}
"""

if "window.AppCommon = {" not in js:
    js = patch + js

with open("/root/.openclaw/workspace/js/scan_backend.js", "w") as f:
    f.write(js)
