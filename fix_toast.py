import re

with open("/root/.openclaw/workspace/js/scan_backend.js", "r") as f:
    js = f.read()

# remove the bad overwrite
js = re.sub(r'// 确保 AppCommon 存在.*?};[\s\n]*\}', '', js, flags=re.DOTALL)

# replace AppCommon.showToast -> (window.app ? window.app.showToast.bind(window.app) : console.log)
js = js.replace("AppCommon.showToast", "(window.app ? window.app.showToast.bind(window.app) : console.log)")
js = js.replace("AppCommon.showModal", "(window.app ? window.app.showModal.bind(window.app) : alert)")
js = js.replace("AppCommon.closeModal", "(window.app ? window.app.closeModal.bind(window.app) : console.log)")

with open("/root/.openclaw/workspace/js/scan_backend.js", "w") as f:
    f.write(js)
