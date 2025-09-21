#!/usr/bin/env python3
"""
订阅转换器运行脚本
"""

import uvicorn
import os
from app.main import app
from config import config

if __name__ == "__main__":
    # 使用配置文件
    host = config.HOST
    port = config.PORT
    debug = config.DEBUG
    
    print(f"[INFO] 启动后端服务: {host}:{port}")
    print(f"[INFO] 调试模式: {debug}")
    
    # 启动应用
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=config.LOG_LEVEL,
        access_log=True  # 启用访问日志，但通过过滤器控制
    )