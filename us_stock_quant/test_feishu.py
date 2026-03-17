#!/usr/bin/env python3
"""测试Feishu推送功能"""
import subprocess
import sys

message = "**测试消息**\n\n定时任务测试 - 选股报告推送功能正常"
cmd = ["openclaw", "message", "send", "--target", "feishu", "--message", message]
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')

if result.returncode == 0:
    print("[OK] Feishu推送测试成功")
    sys.exit(0)
else:
    print(f"[ERROR] Feishu推送测试失败: {result.stderr}")
    sys.exit(1)
