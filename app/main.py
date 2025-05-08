from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import platform
import json

from app.core.config import settings
from app.middlewares.auth import AuthMiddleware
from app.middlewares.proxy import ProxyMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.utils.logger import logger

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="API网关服务，用于请求拦截、认证和转发",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加流量控制中间件（最后添加，最先执行）
app.add_middleware(RateLimitMiddleware)

# 添加代理中间件 (最后添加的先执行)
app.add_middleware(ProxyMiddleware)

# 添加认证中间件
app.add_middleware(AuthMiddleware)

@app.get("/")
async def root():
    """API网关根路径"""
    system_info = f"平台: {platform.system()}, 版本: {platform.version()}"
    return {
        "message": "欢迎使用API网关",
        "system": system_info,
        "services": list(settings.BACKEND_SERVICES.keys())
    }

@app.get("/health")
async def health():
    """健康检查端点"""
    health_status = {
        "gateway": "healthy",
        "system": f"{platform.system()} {platform.version()}",
        "backends": {}
    }
    
    # 检查所有后端服务的健康状态
    for service_name, service_url in settings.BACKEND_SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{service_url}/health", timeout=3.0)
                if response.status_code == 200:
                    health_status["backends"][service_name] = "healthy"
                else:
                    health_status["backends"][service_name] = f"unhealthy - status code: {response.status_code}"
        except Exception as e:
            health_status["backends"][service_name] = f"unhealthy - error: {str(e)}"
    
    # 如果任何后端服务不健康，设置响应状态码为503
    if any("unhealthy" in status for status in health_status["backends"].values()):
        return JSONResponse(
            content=health_status,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    return health_status

if __name__ == "__main__":
    # 打印所有路由

    import uvicorn
    logger.info(f"Starting {settings.APP_NAME}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=10001, reload=True) 