#!/usr/bin/env python3
"""
一键启动脚本 - 自动配置环境并启动项目
"""

import os
import sys
import subprocess
import platform

def main():
    print("🚀 订阅转换器一键启动")
    print("=" * 50)
    
    # 检查是否已有虚拟环境
    venv_path = "venv"
    if not os.path.exists(venv_path):
        print("❌ 首次运行，正在配置环境...")
        result = subprocess.run([sys.executable, "setup.py"], check=False)
        if result.returncode != 0:
            print("❌ 环境配置失败")
            sys.exit(1)
    
    # 启动完整系统
    print("✅ 环境配置完成，启动系统...")
    subprocess.run([sys.executable, "start-all.py"], check=True)

if __name__ == "__main__":
    main()