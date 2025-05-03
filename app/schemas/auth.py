from typing import Optional
from pydantic import BaseModel


class TokenData(BaseModel):
    """令牌数据"""
    sub: str
    exp: int


class Token(BaseModel):
    """访问令牌"""
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True 