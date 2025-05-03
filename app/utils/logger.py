import logging
import sys
from typing import Any, Dict, List, Optional

from app.core.config import settings


class Logger:
    """自定义日志器"""
    
    def __init__(self, name: str = "api_gateway"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        self.logger.addHandler(console_handler)
    
    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self.logger.critical(msg, *args, **kwargs)


# 创建全局日志器实例
logger = Logger() 