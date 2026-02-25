with open("/root/.openclaw/workspace/dashboard.html", "r") as f:
    html = f.read()

html = html.replace('href="pages/', 'href="/pages/')
html = html.replace('href="/" class="logo-link"', 'href="/" class="logo-link"')

with open("/root/.openclaw/workspace/dashboard.html", "w") as f:
    f.write(html)
