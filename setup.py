#!/usr/bin/env python3
"""
项目环境配置脚本
"""

import os
import sys
import subprocess
import platform

def run_command(command, cwd=None, check=True):
    """执行命令"""
    print(f"执行: {command}")
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stderr:
            print(f"错误信息: {e.stderr}")
        return e

def main():
    print("🔧 订阅转换器环境配置")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    
    print(f"✅ Python版本: {sys.version}")
    
    # 创建虚拟环境
    venv_path = "venv"
    if not os.path.exists(venv_path):
        print("📦 创建虚拟环境...")
        result = run_command(f"{sys.executable} -m venv {venv_path}")
        if result.returncode != 0:
            print("❌ 虚拟环境创建失败")
            sys.exit(1)
        print("✅ 虚拟环境创建成功")
    else:
        print("✅ 虚拟环境已存在")
    
    # 设置虚拟环境路径
    if platform.system() == "Windows":
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        python_path = os.path.join(venv_path, "bin", "python")
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    # 升级pip
    print("📦 升级pip...")
    run_command(f"{python_path} -m pip install --upgrade pip")
    
    # 安装Python依赖
    print("📦 安装Python依赖...")
    if os.path.exists("requirements.txt"):
        result = run_command(f"{pip_path} install -r requirements.txt")
        if result.returncode != 0:
            print("❌ Python依赖安装失败")
            sys.exit(1)
        print("✅ Python依赖安装成功")
    else:
        print("⚠️ requirements.txt文件不存在")
    
    # 安装开发依赖
    if os.path.exists("requirements-dev.txt"):
        print("📦 安装开发依赖...")
        result = run_command(f"{pip_path} install -r requirements-dev.txt")
        if result.returncode == 0:
            print("✅ 开发依赖安装成功")
        else:
            print("⚠️ 开发依赖安装失败，但不影响基本功能")
    
    # 检查Node.js
    print("🔍 检查Node.js环境...")
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js版本: {result.stdout.strip()}")
            
            # 检查npm
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm版本: {result.stdout.strip()}")
                
                # 安装前端依赖
                frontend_path = "frontend"
                if os.path.exists(frontend_path):
                    print("📦 安装前端依赖...")
                    result = run_command("npm install", cwd=frontend_path)
                    if result.returncode == 0:
                        print("✅ 前端依赖安装成功")
                    else:
                        print("⚠️ 前端依赖安装失败，请手动运行: cd frontend && npm install")
                else:
                    print("⚠️ frontend目录不存在")
            else:
                print("❌ npm未安装")
        else:
            print("❌ Node.js未安装")
            print("请安装Node.js 18+版本")
    except FileNotFoundError:
        print("❌ Node.js未安装")
        print("请安装Node.js 18+版本")
    
    # 创建必要的目录
    print("📁 创建必要目录...")
    directories = ["data", "logs", "static"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ 创建目录: {directory}")
        else:
            print(f"✅ 目录已存在: {directory}")
    
    # 创建环境配置文件
    print("⚙️ 创建环境配置...")
    env_files = [
        (".env", """# 订阅转换器环境配置
DATABASE_URL=sqlite:///./subscription_converter.db
SECRET_KEY=dev-secret-key-change-in-production
HOST=0.0.0.0
PORT=8000
DEBUG=true
"""),
        ("frontend/.env", """# 前端环境配置
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=订阅转换器
VITE_APP_VERSION=1.0.0
""")
    ]
    
    for env_file, content in env_files:
        if not os.path.exists(env_file):
            # 创建目录（如果路径包含目录）
            try:
                dir_path = os.path.dirname(env_file)
                if dir_path and dir_path != '.':
                    os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                print(f"⚠️ 创建目录失败: {e}")
            
            # 创建文件
            try:
                with open(env_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ 创建配置文件: {env_file}")
            except Exception as e:
                print(f"❌ 创建配置文件失败: {env_file} - {e}")
        else:
            print(f"✅ 配置文件已存在: {env_file}")
    
    print("\n" + "=" * 50)
    print("🎉 环境配置完成！")
    print("=" * 50)
    print("📱 前端地址: http://localhost:3000")
    print("🔧 后端API: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("❤️ 健康检查: http://localhost:8000/health")
    print("=" * 50)
    print("运行以下命令启动系统:")
    print("python start-all.py")
    print("=" * 50)

if __name__ == "__main__":
    main()