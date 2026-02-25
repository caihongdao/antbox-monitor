#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞牛 OS 照片/视频去重工具 - 自动模式
直接删除重复文件，无需确认
"""

import sys
sys.argv.append('--auto')

exec(open('/root/.openclaw/workspace/fn_dedup_photos.py').read().replace(
    'response = input("Delete these duplicate files? (y/n): ").strip().lower()',
    'response = "y"  # Auto mode'
).replace(
    'confirm = input("Type \'YES\' to confirm: ").strip()',
    'confirm = "YES"  # Auto mode'
))
