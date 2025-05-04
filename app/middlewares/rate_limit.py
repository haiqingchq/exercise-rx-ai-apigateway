import time
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple, Optional, Any
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.utils.logger import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    流量控制中间件，用于限制请求频率。
    可以根据IP、路径或用户ID进行限流。
    使用滑动窗口算法实现。
    """
    
    def __init__(self, app):
        """
        初始化流量控制中间件。
        从配置文件中读取设置。
        """
        super().__init__(app)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.window_size = settings.RATE_LIMIT_WINDOW_SIZE
        self.max_requests = settings.RATE_LIMIT_MAX_REQUESTS
        self.exclude_paths = settings.RATE_LIMIT_EXCLUDE_PATHS + settings.WHITELIST_PATHS
        
        # 存储每个限流键（如IP或路径）的请求时间戳
        self.request_records: Dict[str, Deque[float]] = defaultdict(lambda: deque())
        
        logger.info(f"流量控制中间件已初始化: 启用={self.enabled}, 窗口大小={self.window_size}秒, 最大请求数={self.max_requests}")
    
    def _generate_key(self, request: Request) -> str:
        """
        根据请求生成限流键。
        可以根据IP、路径或两者的组合生成。
        
        参数:
            request: 请求对象
            
        返回:
            限流键
        """
        client_ip = request.client.host if request.client else "unknown"
        
        # 使用仅根据IP限流，而不是IP+路径组合
        return f"ip:{client_ip}"
        
        # 原来的组合限流方式（按IP+路径）
        # path = request.url.path
        # return f"ip:{client_ip}:path:{path}"
    
    def _is_rate_limited(self, key: str) -> Tuple[bool, int]:
        """
        检查请求是否超过限流阈值。
        使用滑动窗口算法。
        
        参数:
            key: 限流键
            
        返回:
            (是否被限流, 剩余可用请求数)
        """
        current_time = time.time()
        records = self.request_records[key]
        
        # 移除时间窗口外的请求记录
        while records and current_time - records[0] > self.window_size:
            records.popleft()
        
        # 检查是否超过限额
        if len(records) >= self.max_requests:
            return True, 0
        
        # 添加当前请求的时间戳
        records.append(current_time)
        
        # 返回是否被限流和剩余可用请求数
        return False, self.max_requests - len(records)
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求并应用流量控制。
        
        参数:
            request: 请求对象
            call_next: 下一个处理函数
            
        返回:
            响应对象
        """
        # 如果流量控制未启用或请求路径在排除列表中，直接处理请求
        if not self.enabled or request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # 生成限流键
        key = self._generate_key(request)
        
        # 检查是否超出限流
        is_limited, remaining = self._is_rate_limited(key)
        
        if is_limited:
            logger.warning(f"请求被限流: {key}")
            return Response(
                content="请求频率过高，请稍后再试",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + self.window_size)),
                }
            )
        
        # 记录限流相关信息到请求状态中，以便后续中间件可以获取
        request.state.rate_limit_info = {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset": int(time.time() + self.window_size)
        }
        
        # 处理请求
        response = await call_next(request)
        
        # 获取响应头并添加限流相关信息
        headers = dict(response.headers)
        headers.update({
            "X-RateLimit-Limit": str(self.max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(time.time() + self.window_size)),
        })
        
        # 创建包含响应头的新响应
        return Response(
            content=response.body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type
        ) 