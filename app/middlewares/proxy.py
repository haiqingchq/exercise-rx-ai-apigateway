import httpx
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.core.config import settings
from app.utils.logger import logger


class ProxyMiddleware(BaseHTTPMiddleware):
    """
    代理中间件，用于将请求转发到后端服务。
    路径格式: /api/[service_name]/[endpoint]
    例如: /api/user/profile 将被转发到 user服务的/profile端点
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 如果不是API请求或者没有遵循我们的格式，交给下一个中间件处理
        if not path.startswith("/api/") or path.count("/") < 3:
            return await call_next(request)
        
        # 解析服务名称
        _, _, service_name, *rest = path.split("/")
        
        # 跳过本地API路由 (auth)
        if service_name == "auth":
            return await call_next(request)
            
        endpoint = "/" + "/".join(rest)
        
        # 检查服务是否在配置中
        if service_name not in settings.BACKEND_SERVICES:
            return Response(
                content=f"Service '{service_name}' not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # 构建目标URL
        target_url = f"{settings.BACKEND_SERVICES[service_name]}{endpoint}"
        
        # 转发请求
        return await self._proxy_request(request, target_url)
    
    async def _proxy_request(self, request: Request, target_url: str):
        """转发请求到目标URL"""
        try:
            # 获取请求方法
            method = request.method
            
            # 获取请求头
            headers = dict(request.headers.items())
            # 移除主机相关头，避免冲突
            headers.pop("host", None)
            
            # 如果请求状态中有用户信息，添加到自定义请求头
            if hasattr(request.state, "user"):
                user = request.state.user
                # 将用户ID添加到自定义请求头
                if "sub" in user:
                    headers["X-User-ID"] = str(user["sub"])
                    logger.info(f"添加用户ID到请求头: {user['sub']}")
                
                # 可以添加更多用户信息到请求头
                # 例如，如果payload中有角色信息
                if "scopes" in user:
                    headers["X-User-Scopes"] = str(user["scopes"])
            
            # 获取查询参数
            params = dict(request.query_params)
            
            # 获取请求体
            body = await request.body()
            
            logger.info(f"Forwarding request to {target_url}")
            
            # 创建异步HTTP客户端并发送请求
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    params=params,
                    content=body,
                    timeout=30.0,  # 设置超时时间
                    follow_redirects=True
                )
                
                # 创建响应
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
                
        except httpx.RequestError as e:
            logger.error(f"Error forwarding request: {str(e)}")
            return Response(
                content=f"Error forwarding request: {str(e)}",
                status_code=status.HTTP_502_BAD_GATEWAY
            ) 