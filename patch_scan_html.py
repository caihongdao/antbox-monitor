import re

with open("/root/.openclaw/workspace/pages/scan.html", "r") as f:
    html = f.read()

# Add CSS for modular navigation
css = """
    <style>
        /* 独立模块化导航条样式 */
        .app-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #ffffff;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            margin-bottom: 24px;
            flex-wrap: wrap;
            gap: 16px;
        }
        .header-left {
            display: flex;
            align-items: center;
            gap: 32px;
            flex-wrap: wrap;
        }
        .logo-link {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: #262626;
            font-size: 20px;
            font-weight: bold;
        }
        .logo-link i {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #1890ff, #52c41a);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
        }
        .main-nav {
            display: flex;
            gap: 12px;
            align-items: center;
        }
        .main-nav a {
            text-decoration: none;
            color: #595959;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 6px;
            background: #f0f2f5;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 15px;
            border: 1px solid transparent;
        }
        .main-nav a:hover {
            color: #1890ff;
            background: #e6f7ff;
            border-color: #91d5ff;
        }
        .main-nav a.active {
            color: white;
            background: #1890ff;
            border-color: #1890ff;
            box-shadow: 0 2px 6px rgba(24, 144, 255, 0.4);
        }
        .header-right {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .header-right .user-info {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: bold;
            color: #595959;
        }
        .header-right .btn-icon {
            background: #f0f2f5;
            border: none;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            cursor: pointer;
            color: #595959;
            transition: 0.3s;
        }
        .header-right .btn-icon:hover {
            background: #e6f7ff;
            color: #1890ff;
        }
        .btn-logout {
            background: #fff1f0;
            color: #f5222d;
            border: 1px solid #ffa39e;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn-logout:hover {
            background: #ffccc7;
        }
    </style>
</head>
"""

html = html.replace("</head>", css)

# Fix JS include if not using AppCommon directly or fix AppCommon issue
# We will just ensure the UI looks correct first
with open("/root/.openclaw/workspace/pages/scan.html", "w") as f:
    f.write(html)
