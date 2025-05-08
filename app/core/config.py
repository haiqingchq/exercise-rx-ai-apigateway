from typing import Dict, List, Optional
import platform
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    APP_NAME: str = "ExercisesRxAI API Gateway"
    DEBUG: bool = True  # 开启调试模式以获取更多日志信息
    
    # JWT配置
    SECRET_KEY: str = "chenhaiqing"  # 在生产环境中应当使用环境变量设置
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 后端服务配置 - 根据操作系统选择不同配置
    @property
    def BACKEND_SERVICES(self) -> Dict[str, str]:
        # 在Windows系统上使用IP地址而不是localhost
        if platform.system() == "Windows":
            return {
                "backend": "http://127.0.0.1:8000",
                # 备用地址，如果主地址无法连接，可以尝试这些地址
                "backend_alt1": "http://localhost:8000",
                "backend_alt2": "http://[::1]:8000",  # IPv6 本地地址
            }
        else:
            return {
                "backend": "http://localhost:8000",
                "backend_alt1": "http://127.0.0.1:8000",
            }
    
    # 白名单路径（不需要认证的路径）
    WHITELIST_PATHS: List[str] = [
        "/api/backend/v1/auth/login",
        "/api/backend_alt1/v1/auth/login",  # 添加备用服务的路径
        "/api/backend_alt2/v1/auth/login",  # 添加备用服务的路径
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",  # 添加健康检查路径
        "/",  # 添加根路径
    ]
    
    # 流量控制配置
    RATE_LIMIT_ENABLED: bool = True  # 是否启用流量控制
    RATE_LIMIT_WINDOW_SIZE: int = 60  # 时间窗口大小（秒）
    RATE_LIMIT_MAX_REQUESTS: int = 20  # 时间窗口内允许的最大请求数 (减小为20便于测试)
    # 不进行流量控制的路径
    RATE_LIMIT_EXCLUDE_PATHS: List[str] = [
        "/health",
        "/metrics",
        "/",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 