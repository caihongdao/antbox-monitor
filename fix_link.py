with open("/root/.openclaw/workspace/pages/scan.html", "r") as f:
    html = f.read()

html = html.replace('href="../dashboard.html"', 'href="/"')

with open("/root/.openclaw/workspace/pages/scan.html", "w") as f:
    f.write(html)
