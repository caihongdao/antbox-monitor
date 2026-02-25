#!/bin/bash
# 飞牛 OS 照片去重工具 - 快速启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/fn_dedup_photos.py"

echo "=========================================="
echo "  飞牛 OS 照片/视频去重工具"
echo "=========================================="
echo ""

# 检查 Python 脚本
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ 脚本不存在：$PYTHON_SCRIPT"
    exit 1
fi

# 运行去重脚本
python3 "$PYTHON_SCRIPT"

echo ""
echo "=========================================="
