from typing import Dict, List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    APP_NAME: str = "ExercisesRxAI API Gateway"
    DEBUG: bool = False
    
    # JWT配置
    SECRET_KEY: str = "chenhaiqing"  # 在生产环境中应当使用环境变量设置
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 后端服务配置
    BACKEND_SERVICES: Dict[str, str] = {
        "backend": "http://localhost:8000",
    }
    
    # 白名单路径（不需要认证的路径）
    WHITELIST_PATHS: List[str] = [
        "/api/backend/v1/auth/login",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]
    
    # 流量控制配置
    RATE_LIMIT_ENABLED: bool = True  # 是否启用流量控制
    RATE_LIMIT_WINDOW_SIZE: int = 60  # 时间窗口大小（秒）
    RATE_LIMIT_MAX_REQUESTS: int = 20  # 时间窗口内允许的最大请求数 (减小为20便于测试)
    # 不进行流量控制的路径
    RATE_LIMIT_EXCLUDE_PATHS: List[str] = [
        "/health",
        "/metrics",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 