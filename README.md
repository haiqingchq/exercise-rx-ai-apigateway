# API网关服务

一个基于FastAPI的轻量级API网关服务，用于请求拦截、认证和转发。

## 功能特点

- 请求拦截与路由转发
- JWT认证与授权
- 跨域资源共享(CORS)支持
- 灵活的服务配置

## 安装与设置

### 环境要求

- Python 3.8+
- 依赖包管理工具(pip)

### 安装依赖

```bash
# 安装项目依赖
pip install -e .
```

## 配置

配置文件位于`app/core/config.py`，您可以通过环境变量或`.env`文件修改配置项：

- `SECRET_KEY`: JWT签名密钥，在生产环境中应当更改为强密钥
- `BACKEND_SERVICES`: 后端服务地址配置
- `WHITELIST_PATHS`: 无需认证的路径白名单

## 使用方法

### 启动服务

```bash
# 直接启动
python main.py

# 或者使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

启动后服务将运行在`http://localhost:8080`

### API路由格式

API网关将根据以下格式的URL转发请求到对应的后端服务：

```
/api/{service_name}/{endpoint}
```

例如，请求`/api/user/profile`将被转发到配置文件中`user`服务的`/profile`端点。

### 认证

使用基于JWT的认证机制：

1. 调用`/api/auth/login`接口获取访问令牌：

```bash
curl -X POST "http://localhost:8080/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpassword"
```

响应示例：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

2. 在后续请求中使用令牌：

```bash
curl -X GET "http://localhost:8080/api/user/profile" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 扩展与自定义

### 添加新的后端服务

在`app/core/config.py`中的`BACKEND_SERVICES`字典中添加新的服务配置：

```python
BACKEND_SERVICES: Dict[str, str] = {
    "user": "http://localhost:8001",
    "product": "http://localhost:8002",
    "order": "http://localhost:8003",
    "new_service": "http://localhost:8004",  # 添加新服务
}
```

### 自定义认证逻辑

修改`app/middlewares/auth.py`中的`AuthMiddleware`类以实现自定义的认证逻辑。

### 自定义代理行为

修改`app/middlewares/proxy.py`中的`ProxyMiddleware`类以自定义请求转发行为。

## API文档

启动服务后访问以下地址查看API文档：

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
