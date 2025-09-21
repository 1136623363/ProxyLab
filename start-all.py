#!/usr/bin/env python3
"""
订阅转换项目启动脚本 - 同时启动后端和前端
优化版本：提供更好的错误处理、健康检查和日志记录
"""

import os
import sys
import subprocess
import time
import threading
import signal
import atexit
import platform
import requests
import json
from datetime import datetime, timezone, timedelta
from config import config

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

# 全局变量
backend_process = None
frontend_process = None
backend_url = config.get_backend_url()
frontend_url = config.get_frontend_url()

def log_with_timestamp(message, level="INFO"):
    """带时间戳的日志输出"""
    timestamp = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def check_backend_health():
    """检查后端健康状态"""
    import time
    
    # 添加时间控制，避免过于频繁的检查
    current_time = time.time()
    if hasattr(check_backend_health, 'last_check_time'):
        # 如果距离上次检查不到30秒，跳过检查
        if current_time - check_backend_health.last_check_time < 30:
            return getattr(check_backend_health, 'last_status', False) == 'healthy'
    
    check_backend_health.last_check_time = current_time
    
    try:
        response = requests.get(f"{backend_url}/health", timeout=3)
        if response.status_code == 200:
            # 只在第一次成功或状态变化时打印
            if not hasattr(check_backend_health, 'last_status') or check_backend_health.last_status != 'healthy':
                log_with_timestamp("✅ 后端健康检查通过")
                check_backend_health.last_status = 'healthy'
            return True
    except requests.exceptions.RequestException:
        # 只在状态变化时打印错误
        if not hasattr(check_backend_health, 'last_status') or check_backend_health.last_status != 'unhealthy':
            log_with_timestamp("⚠️ 后端健康检查失败", "WARN")
            check_backend_health.last_status = 'unhealthy'
    
    return False

def get_backend_logs():
    """获取后端日志"""
    if backend_process and backend_process.poll() is not None:
        try:
            stdout, stderr = backend_process.communicate(timeout=1)
            return stdout, stderr
        except:
            return "", ""
    return "", ""

def start_backend(python_path):
    """启动后端服务"""
    global backend_process
    
    log_with_timestamp("🔧 启动后端服务...")
    
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['HOST'] = config.HOST
        env['PORT'] = str(config.PORT)
        env['DEBUG'] = str(config.DEBUG).lower()
        
        # 启动后端进程
        backend_process = subprocess.Popen(
            [python_path, "run.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 将stderr重定向到stdout
            text=True,
            encoding='utf-8',
            errors='replace',
            shell=False,
            env=env,
            bufsize=1,  # 行缓冲
            universal_newlines=True
        )
        
        # 等待进程启动
        time.sleep(3)
        
        # 检查进程是否还在运行
        if backend_process.poll() is not None:
            stdout, stderr = get_backend_logs()
            log_with_timestamp("❌ 后端启动失败:", "ERROR")
            log_with_timestamp(f"STDOUT: {stdout}", "ERROR")
            log_with_timestamp(f"STDERR: {stderr}", "ERROR")
            return False
        else:
            log_with_timestamp("✅ 后端进程已启动")
            return True
                        
    except Exception as e:
        log_with_timestamp(f"❌ 后端启动异常: {e}", "ERROR")
        return False


def show_help():
    """显示帮助信息"""
    print("订阅转换器启动脚本")
    print("="*50)
    print("用法: python start-all.py")
    print("")
    print("功能:")
    print("  - 自动启动后端和前端服务")
    print("  - 监控服务状态")
    print("  - 显示错误日志")
    print("")
    print("按 Ctrl+C 停止服务")

def main():
    # 检查帮助选项
    if "--help" in sys.argv or "-h" in sys.argv:
        show_help()
        sys.exit(0)
    
    log_with_timestamp("🚀 启动订阅转换器系统...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        log_with_timestamp("❌ 需要Python 3.8或更高版本", "ERROR")
        sys.exit(1)
    
    log_with_timestamp(f"✅ Python版本: {sys.version}")
    
    # 检查虚拟环境
    venv_path = ".venv"
    if not os.path.exists(venv_path):
        log_with_timestamp("❌ 虚拟环境不存在，请先运行 setup.py", "ERROR")
        sys.exit(1)
    
    # 设置虚拟环境路径
    if platform.system() == "Windows":
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        python_path = os.path.join(venv_path, "bin", "python")
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    # 检查依赖
    log_with_timestamp("🔍 检查依赖...")
    try:
        result = subprocess.run([python_path, "-c", "import fastapi, uvicorn"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            log_with_timestamp("❌ 后端依赖未安装，正在安装...", "WARN")
            subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
            log_with_timestamp("✅ 后端依赖安装完成")
    except Exception as e:
        log_with_timestamp(f"❌ 依赖检查失败: {e}", "ERROR")
        sys.exit(1)
    
    # 检查前端依赖
    frontend_path = "frontend"
    if os.path.exists(frontend_path):
        # 检查npm是否可用（在系统PATH中查找）
        npm_available = False
        try:
            # 首先尝试直接运行npm
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
            npm_available = True
            log_with_timestamp("✅ npm可用")
        except:
            # 如果直接运行失败，尝试在系统PATH中查找
            try:
                if platform.system() == "Windows":
                    # Windows下查找npm
                    result = subprocess.run(["where", "npm"], capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        npm_available = True
                        log_with_timestamp("✅ 在系统PATH中找到npm")
                else:
                    # Linux/Mac下查找npm
                    result = subprocess.run(["which", "npm"], capture_output=True, text=True)
                    if result.returncode == 0 and result.stdout.strip():
                        npm_available = True
                        log_with_timestamp("✅ 在系统PATH中找到npm")
            except:
                pass
        
        if not npm_available:
            log_with_timestamp("❌ npm未安装或不在PATH中", "WARN")
            log_with_timestamp("请安装Node.js和npm，或跳过前端启动", "WARN")
            frontend_path = None
        
        if frontend_path:
            # 创建前端环境变量文件
            env_file = os.path.join(frontend_path, ".env.development")
            if not os.path.exists(env_file):
                log_with_timestamp("📝 创建前端环境配置文件...")
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.write("# 开发环境配置\n")
                    f.write("VITE_API_BASE_URL=http://localhost:8001\n")
                    f.write("VITE_APP_TITLE=订阅转换器\n")
                    f.write("VITE_APP_VERSION=1.0.0\n")
                log_with_timestamp("✅ 前端环境配置文件创建成功")
            
            node_modules = os.path.join(frontend_path, "node_modules")
            if not os.path.exists(node_modules):
                log_with_timestamp("❌ 前端依赖未安装，正在安装...", "WARN")
                try:
                    subprocess.run(["npm", "install"], cwd=frontend_path, check=True)
                    log_with_timestamp("✅ 前端依赖安装成功")
                except Exception as e:
                    log_with_timestamp(f"❌ 前端依赖安装失败: {e}", "ERROR")
                    log_with_timestamp("请手动运行: cd frontend && npm install", "WARN")
                    frontend_path = None
    else:
        log_with_timestamp("⚠️ frontend目录不存在，跳过前端启动", "WARN")
        frontend_path = None
    
    # 启动后端
    if not start_backend(python_path):
        log_with_timestamp("❌ 后端启动失败，退出程序", "ERROR")
        sys.exit(1)
    
    # 启动前端
    if frontend_path and os.path.exists(frontend_path):
        log_with_timestamp("🎨 启动前端服务...")
        try:
            # 设置前端环境变量
            frontend_env = os.environ.copy()
            frontend_env['VITE_DEV_SERVER_PORT'] = str(config.FRONTEND_PORT)
            frontend_env['VITE_BACKEND_PORT'] = str(config.PORT)
            frontend_env['VITE_BACKEND_HOST'] = config.HOST
            
            # 在Windows上使用shell=True来确保能找到npm
            frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=frontend_env,
                shell=True
            )
            log_with_timestamp("✅ 前端服务已启动")
        except Exception as e:
            log_with_timestamp(f"❌ 前端启动失败: {e}", "ERROR")
            log_with_timestamp("请手动运行: cd frontend && npm run dev", "WARN")
    else:
        log_with_timestamp("⚠️ 跳过前端启动", "WARN")
    
    # 显示访问地址
    log_with_timestamp("\n" + "="*50)
    log_with_timestamp("🎉 系统启动完成！")
    log_with_timestamp("="*50)
    log_with_timestamp("📱 前端地址: http://localhost:3000")
    log_with_timestamp("🔧 后端API: http://localhost:8001")
    log_with_timestamp("📚 API文档: http://localhost:8001/docs")
    log_with_timestamp("❤️ 健康检查: http://localhost:8001/health")
    log_with_timestamp("="*50)
    log_with_timestamp("按 Ctrl+C 停止服务")
    log_with_timestamp("="*50)
    
    # 启动日志监控线程
    def monitor_backend_logs():
        """监控后端日志"""
        while backend_process and backend_process.poll() is None:
            try:
                # 非阻塞读取输出
                if backend_process.stdout.readable():
                    line = backend_process.stdout.readline()
                    if line:
                        line_str = line.strip()
                        # 过滤掉健康检查的访问日志
                        if not ('/health' in line_str and 'GET' in line_str and '200' in line_str):
                            log_with_timestamp(f"[后端] {line_str}")
            except Exception as e:
                # 记录具体的异常信息，而不是忽略
                log_with_timestamp(f"[后端日志监控] 异常: {e}", "WARN")
            time.sleep(0.1)
    
    def monitor_frontend_logs():
        """监控前端日志"""
        while frontend_process and frontend_process.poll() is None:
            try:
                # 非阻塞读取输出
                if frontend_process.stdout.readable():
                    line = frontend_process.stdout.readline()
                    if line:
                        log_with_timestamp(f"[前端] {line.strip()}")
            except Exception as e:
                # 记录具体的异常信息，而不是忽略
                log_with_timestamp(f"[前端日志监控] 异常: {e}", "WARN")
            time.sleep(0.1)
    
    # 启动日志监控线程
    import threading
    backend_log_thread = threading.Thread(target=monitor_backend_logs, daemon=True)
    frontend_log_thread = threading.Thread(target=monitor_frontend_logs, daemon=True)
    
    backend_log_thread.start()
    if frontend_process:
        frontend_log_thread.start()
    
    # 清理函数
    def cleanup():
        log_with_timestamp("🛑 正在停止服务...")
        if backend_process and backend_process.poll() is None:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        if frontend_process and frontend_process.poll() is None:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        log_with_timestamp("✅ 服务已停止")
    
    # 注册清理函数
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda s, f: cleanup())
    signal.signal(signal.SIGTERM, lambda s, f: cleanup())
    
    try:
        # 监控进程
        log_with_timestamp("🔍 开始监控服务状态...")
        while True:
            # 检查后端状态
            if backend_process and backend_process.poll() is not None:
                stdout, stderr = get_backend_logs()
                log_with_timestamp("❌ 后端服务意外停止", "ERROR")
                if stdout:
                    log_with_timestamp(f"后端输出: {stdout}", "ERROR")
                if stderr:
                    log_with_timestamp(f"后端错误: {stderr}", "ERROR")
                break
            
            # 检查前端状态
            if frontend_process and frontend_process.poll() is not None:
                log_with_timestamp("❌ 前端服务意外停止", "ERROR")
                # 获取前端日志
                try:
                    frontend_stdout, frontend_stderr = frontend_process.communicate(timeout=1)
                    if frontend_stdout:
                        log_with_timestamp(f"前端输出: {frontend_stdout}", "ERROR")
                    if frontend_stderr:
                        log_with_timestamp(f"前端错误: {frontend_stderr}", "ERROR")
                except:
                    pass
                break
            
            # 定期健康检查（函数内部已处理状态变化时的日志打印）
            check_backend_health()
            
            time.sleep(30)  # 每30秒检查一次，减少日志频率
            
    except KeyboardInterrupt:
        log_with_timestamp("🛑 收到停止信号")
        cleanup()
    except Exception as e:
        log_with_timestamp(f"❌ 监控进程出错: {e}", "ERROR")
        cleanup()

if __name__ == "__main__":
    main()