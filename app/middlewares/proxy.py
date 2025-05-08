import httpx
import platform
import traceback
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
            logger.error(f"未找到服务配置: '{service_name}'")
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
            
            # 记录系统信息和完整的请求信息，帮助调试
            system_info = f"平台: {platform.system()}, 版本: {platform.version()}"
            logger.info(f"系统信息: {system_info}")
            logger.info(f"转发请求到: {target_url}, 方法: {method}, 参数: {params}")
            
            # 创建异步HTTP客户端并发送请求
            timeout = httpx.Timeout(30.0, connect=10.0)  # 增加连接超时时间
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=target_url,
                    headers=headers,
                    params=params,
                    content=body,
                    follow_redirects=True
                )
                
                logger.info(f"请求成功, 状态码: {response.status_code}")
                
                # 创建响应
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
                
        except httpx.ConnectError as e:
            error_msg = f"连接错误 ({target_url}): {str(e)}"
            logger.error(error_msg)
            logger.error(f"目标服务可能未运行或不可达。系统: {platform.system()}")
            return Response(
                content=error_msg,
                status_code=status.HTTP_502_BAD_GATEWAY
            )
        except httpx.TimeoutException as e:
            error_msg = f"请求超时 ({target_url}): {str(e)}"
            logger.error(error_msg)
            return Response(
                content=error_msg,
                status_code=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except httpx.RequestError as e:
            error_msg = f"转发请求错误 ({target_url}): {str(e)}"
            logger.error(error_msg)
            logger.error(f"详细错误: {traceback.format_exc()}")
            return Response(
                content=error_msg,
                status_code=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            error_msg = f"未知错误 ({target_url}): {str(e)}"
            logger.error(error_msg)
            logger.error(f"详细错误: {traceback.format_exc()}")
            return Response(
                content=error_msg,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 