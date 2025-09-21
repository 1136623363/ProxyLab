"""
统一错误处理工具
"""
import logging
import traceback
from typing import Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import requests.exceptions

logger = logging.getLogger(__name__)

class ErrorHandler:
    """统一错误处理器"""
    
    @staticmethod
    def handle_database_error(error: SQLAlchemyError, operation: str = "数据库操作") -> HTTPException:
        """处理数据库错误"""
        logger.error(f"{operation}失败: {str(error)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        
        if "UNIQUE constraint failed" in str(error):
            return HTTPException(status_code=400, detail="数据已存在，违反唯一性约束")
        elif "FOREIGN KEY constraint failed" in str(error):
            return HTTPException(status_code=400, detail="关联数据不存在")
        elif "NOT NULL constraint failed" in str(error):
            return HTTPException(status_code=400, detail="必填字段不能为空")
        else:
            return HTTPException(status_code=500, detail=f"{operation}失败，请稍后重试")
    
    @staticmethod
    def handle_network_error(error: requests.exceptions.RequestException, operation: str = "网络请求") -> HTTPException:
        """处理网络错误"""
        logger.error(f"{operation}失败: {str(error)}")
        
        if isinstance(error, requests.exceptions.Timeout):
            return HTTPException(status_code=408, detail="请求超时，请检查网络连接")
        elif isinstance(error, requests.exceptions.ConnectionError):
            return HTTPException(status_code=503, detail="网络连接失败，请检查网络状态")
        elif isinstance(error, requests.exceptions.SSLError):
            return HTTPException(status_code=400, detail="SSL证书验证失败")
        else:
            return HTTPException(status_code=500, detail=f"{operation}失败: {str(error)}")
    
    @staticmethod
    def handle_validation_error(error: ValueError, operation: str = "数据验证") -> HTTPException:
        """处理数据验证错误"""
        logger.error(f"{operation}失败: {str(error)}")
        return HTTPException(status_code=400, detail=f"数据验证失败: {str(error)}")
    
    @staticmethod
    def handle_general_error(error: Exception, operation: str = "操作") -> HTTPException:
        """处理一般错误"""
        logger.error(f"{operation}失败: {str(error)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return HTTPException(status_code=500, detail=f"{operation}失败，请稍后重试")
    
    @staticmethod
    def log_operation(operation: str, user_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        """记录操作日志"""
        log_data = {
            "operation": operation,
            "user_id": user_id,
            "details": details or {}
        }
        logger.info(f"操作记录: {log_data}")
    
    @staticmethod
    def log_security_event(event: str, user_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        """记录安全事件"""
        log_data = {
            "event": event,
            "user_id": user_id,
            "details": details or {}
        }
        logger.warning(f"安全事件: {log_data}")

def safe_execute(func, *args, **kwargs):
    """安全执行函数，自动处理异常"""
    try:
        return func(*args, **kwargs)
    except SQLAlchemyError as e:
        raise ErrorHandler.handle_database_error(e, func.__name__)
    except requests.exceptions.RequestException as e:
        raise ErrorHandler.handle_network_error(e, func.__name__)
    except ValueError as e:
        raise ErrorHandler.handle_validation_error(e, func.__name__)
    except Exception as e:
        raise ErrorHandler.handle_general_error(e, func.__name__)