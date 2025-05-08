from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    return {"message": "欢迎使用API网关"}

@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # 打印所有路由

    import uvicorn
    logger.info(f"Starting {settings.APP_NAME}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=10001, reload=True) 