from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from app.database import init_database, get_db
from app.auth import get_current_active_user, User
from app.routers import auth, nodes, input_records, output, monitoring, subscription_links, short_url, redirect
from app.scheduler import scheduler_manager
from config import config
from app.cache import cleanup_cache_task
import os
import sys
import asyncio
import logging

# 设置编码环境
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log', encoding='utf-8') if os.path.exists('logs') else logging.StreamHandler(sys.stdout)
    ]
)

# 配置日志过滤器，减少健康检查日志
class HealthCheckFilter(logging.Filter):
    """过滤健康检查的访问日志"""
    def filter(self, record):
        # 过滤掉健康检查的访问日志
        if hasattr(record, 'getMessage'):
            message = record.getMessage()
            if '/health' in message and 'GET' in message and '200' in message:
                return False
        return True

# 配置uvicorn访问日志
logging.getLogger("uvicorn.access").addFilter(HealthCheckFilter())

# Create FastAPI application
app = FastAPI(
    title="Subscription Converter",
    description="A powerful subscription link conversion and management system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS if not config.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and create default admin user
init_database()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger = logging.getLogger(__name__)
    try:
        # 确保日志目录存在
        os.makedirs('logs', exist_ok=True)
        
        # Start scheduled task manager
        scheduler_manager.start()
        logger.info("定时任务管理器启动成功")
        
        # Start cache cleanup task
        asyncio.create_task(cleanup_cache_task())
        logger.info("缓存清理任务启动成功")
        
        logger.info("应用启动完成")
        print("[INFO] 应用启动完成")
    except Exception as e:
        logger.error(f"启动时出现错误: {e}", exc_info=True)
        print(f"[ERROR] 启动时出现错误: {e}")
        # 不阻止应用启动

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger = logging.getLogger(__name__)
    try:
        # Stop scheduled task manager
        scheduler_manager.stop()
        logger.info("定时任务管理器关闭成功")
        
        logger.info("应用关闭完成")
        print("[INFO] 应用关闭完成")
    except Exception as e:
        logger.error(f"关闭时出现错误: {e}", exc_info=True)
        print(f"[ERROR] 关闭时出现错误: {e}")

# Static file service
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 全局异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    logger = logging.getLogger(__name__)
    logger.warning(f"请求验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求参数验证失败",
            "errors": exc.errors()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理HTTP异常"""
    logger = logging.getLogger(__name__)
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理一般异常"""
    logger = logging.getLogger(__name__)
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"}
    )

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(input_records.router, prefix="/api/input", tags=["Input Management"])
app.include_router(nodes.router, prefix="/api/nodes", tags=["Node Management"])
app.include_router(output.router, prefix="/api/output", tags=["Output Format"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])
app.include_router(subscription_links.router, prefix="/api/subscription-links", tags=["Subscription Links"])
app.include_router(short_url.router, prefix="/api/short-url", tags=["Short URL"])
app.include_router(redirect.router, tags=["Redirect"])

@app.get("/")
async def root():
    """Root path, returns frontend page"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Subscription Converter</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }
            .header p {
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 1.1em;
            }
            .content {
                padding: 40px;
            }
            .cta {
                text-align: center;
                margin: 40px 0;
            }
            .btn {
                display: inline-block;
                padding: 15px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: 500;
                transition: transform 0.3s ease;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Subscription Converter</h1>
                <p>Powerful subscription link conversion and management system</p>
            </div>
            <div class="content">
                <div class="cta">
                    <a href="/docs" class="btn">View API Documentation</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Subscription converter is running normally"}

@app.get("/api/subscription/{link_id}")
async def get_public_subscription(
    link_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """公开访问订阅内容"""
    from app.routers.subscription_links import get_subscription_content
    return await get_subscription_content(link_id, request, db)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)