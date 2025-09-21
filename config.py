#!/usr/bin/env python3
"""
统一配置文件
"""

import os
from typing import Optional

class Config:
    """应用配置类"""
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "3000"))
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/subscription_converter.db")
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # 密码策略
    MIN_PASSWORD_LENGTH: int = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION: int = int(os.getenv("LOCKOUT_DURATION", "300"))  # 5分钟
    
    # 会话安全
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "1800"))  # 30分钟
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS配置 - 生产环境应该限制更严格
    CORS_ORIGINS: list = [
        f"http://localhost:{FRONTEND_PORT}",
        f"http://127.0.0.1:{FRONTEND_PORT}",
        f"http://{HOST}:{FRONTEND_PORT}",
        f"http://localhost:{PORT}",
        f"http://127.0.0.1:{PORT}",
        f"http://{HOST}:{PORT}",
        # 生产环境应该通过环境变量配置
        *os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
    ]
    
    # 开发环境额外允许的源
    if DEBUG:
        CORS_ORIGINS.extend([
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            # 安卓客户端可能使用的源
            "file://",
            "null",
            "capacitor://localhost",
            "ionic://localhost",
            "http://localhost",
            "http://127.0.0.1",
            # 局域网访问
            "http://192.168.0.0/16",
            "http://10.0.0.0/8",
            "http://172.16.0.0/12",
        ])
    
    # 调试模式
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # 订阅配置
    SUBSCRIPTION_BASE_URL: str = os.getenv("SUBSCRIPTION_BASE_URL", f"http://{HOST}:{PORT}")
    
    # 节点检测配置
    NODE_CHECK_TIMEOUT: int = int(os.getenv("NODE_CHECK_TIMEOUT", "10"))
    NODE_CHECK_INTERVAL: int = int(os.getenv("NODE_CHECK_INTERVAL", "600"))  # 10分钟
    
    # 缓存配置
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5分钟
    
    @classmethod
    def get_frontend_url(cls) -> str:
        """获取前端URL"""
        return f"http://localhost:{cls.FRONTEND_PORT}"
    
    @classmethod
    def get_backend_url(cls) -> str:
        """获取后端URL"""
        return f"http://{cls.HOST}:{cls.PORT}"
    
    @classmethod
    def get_subscription_url(cls, user_id: Optional[int] = None) -> str:
        """获取订阅URL"""
        base_url = cls.get_backend_url()
        if user_id:
            return f"{base_url}/api/output/subscription?user_id={user_id}"
        else:
            return f"{base_url}/api/output/subscription"
    
    @classmethod
    def get_public_subscription_url(cls, link_id: str) -> str:
        """获取公开订阅URL"""
        base_url = cls.get_backend_url()
        return f"{base_url}/api/subscription/{link_id}"

# 创建全局配置实例
config = Config()

# 导出常用配置
HOST = config.HOST
PORT = config.PORT
FRONTEND_PORT = config.FRONTEND_PORT
DATABASE_URL = config.DATABASE_URL
SECRET_KEY = config.SECRET_KEY
DEBUG = config.DEBUG
