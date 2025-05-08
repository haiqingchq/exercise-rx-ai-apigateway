from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError

from app.core.config import settings
from app.core.auth import decode_access_token
from app.utils.logger import logger


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件，用于验证请求的JWT令牌。
    白名单路径将被跳过认证检查。
    """
    
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # 检查路径是否在白名单中
        path = request.url.path
        if path in settings.WHITELIST_PATHS:
            return await call_next(request)
            
        # 从请求头中获取Authorization
        authorization = request.headers.get("Authorization")
        logger.info(f"Authorization: {authorization}")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "未提供有效的认证凭证"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 提取并验证JWT令牌
        token = authorization.replace("Bearer ", "")
        try:
            # 解码JWT获取用户数据
            payload = decode_access_token(token)
            
            # 将用户信息添加到请求状态中，以便后续使用
            request.state.user = payload
            logger.info(f"Authenticated user: {payload.get('sub')}")
            
            # 继续处理请求
            return await call_next(request)
            
        except JWTError as e:
            logger.error(f"JWT验证失败: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "无效的认证凭证"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"认证过程中出现错误: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "认证过程中出现错误"}
            ) 