# API网关使用指南

本文档详细介绍如何部署、配置和使用API网关系统。

## 1. 系统架构

我们的API网关系统由以下组件组成：
- API网关服务 (8080端口)
- 模拟用户服务 (8001端口)
- 模拟产品服务 (8002端口)
- 模拟订单服务 (8003端口)

API网关负责拦截请求，进行权限验证，然后将请求转发到相应的后端服务。

## 2. 安装依赖

首先，确保安装了所有必要的依赖：

```bash
pip install -e .
```

## 3. 测试环境准备

我们提供了模拟后端服务用于测试。需要先启动这些模拟服务，然后再启动API网关。

### 3.1 启动模拟后端服务

需要打开三个终端窗口，分别启动三个服务：

终端1 (用户服务):
```bash
python mock_services.py user
```

终端2 (产品服务):
```bash
python mock_services.py product
```

终端3 (订单服务):
```bash
python mock_services.py order
```

### 3.2 启动API网关

在第四个终端窗口中启动API网关服务：

```bash
python main.py
```

或者使用uvicorn直接启动：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 4. 使用API网关

API网关现在正在端口8080上运行，您可以通过以下URL访问它：`http://localhost:8080`

### 4.1 API文档

API网关提供了自动生成的API文档：
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### 4.2 认证流程

大多数API需要认证才能访问。认证流程如下：

1. 获取访问令牌
2. 使用访问令牌发送后续请求

#### 4.2.1 获取访问令牌

使用以下API获取访问令牌：

```bash
curl -X POST "http://localhost:8080/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpassword"
```

或者使用Swagger UI通过浏览器发送请求。

响应示例：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 4.2.2 使用访问令牌

在后续所有请求中，将访问令牌添加到`Authorization`头中：

```bash
curl -X GET "http://localhost:8080/api/user/profile" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4.3 访问后端服务

API网关使用以下路由格式将请求转发到后端服务：

```
/api/{service_name}/{endpoint}
```

#### 例子:

1. 获取用户资料：
```bash
curl -X GET "http://localhost:8080/api/user/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. 获取产品列表：
```bash
curl -X GET "http://localhost:8080/api/product/products" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

3. 获取订单列表：
```bash
curl -X GET "http://localhost:8080/api/order/orders" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. 创建新订单：
```bash
curl -X POST "http://localhost:8080/api/order/orders" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product_id": 2, "quantity": 3}'
```

## 5. 自定义配置

### 5.1 配置后端服务

您可以在`app/core/config.py`文件中修改`BACKEND_SERVICES`字典来配置后端服务地址：

```python
BACKEND_SERVICES: Dict[str, str] = {
    "user": "http://localhost:8001",
    "product": "http://localhost:8002",
    "order": "http://localhost:8003",
    # 添加更多服务...
}
```

### 5.2 配置认证白名单

在`app/core/config.py`文件中修改`WHITELIST_PATHS`列表来配置不需要认证的路径：

```python
WHITELIST_PATHS: List[str] = [
    "/api/auth/login",
    "/docs",
    "/redoc",
    "/openapi.json",
    # 添加更多路径...
]
```

### 5.3 配置JWT认证

在`app/core/config.py`文件中修改JWT相关配置：

```python
SECRET_KEY: str = "your-secret-key"  # 在生产环境中应使用环境变量
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

## 6. 生产环境部署

在生产环境中部署时，建议：

1. 使用环境变量设置敏感配置，如`SECRET_KEY`
2. 限制CORS的`allow_origins`为特定域名
3. 配置HTTPS
4. 使用生产级别的WSGI服务器，如Gunicorn搭配Uvicorn

生产环境启动示例：

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080
```

## 7. 常见问题排查

### 7.1 认证失败

检查：
- 令牌是否过期
- `Authorization`头格式是否正确 (必须是`Bearer YOUR_TOKEN`)
- JWT签名密钥是否正确

### 7.2 服务转发失败

检查：
- 后端服务是否在运行
- 后端服务配置是否正确
- URL格式是否符合`/api/{service_name}/{endpoint}`

### 7.3 CORS问题

如果在浏览器中调用API时遇到CORS问题，确保设置了正确的CORS头部，并在API网关的CORS中间件中配置了允许的源。

## 8. 扩展API网关

要扩展API网关功能，可以：

1. 添加新的中间件处理特定逻辑
2. 修改现有中间件自定义行为
3. 添加新的API路由

例如，添加请求日志中间件：

```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 请求处理前的日志
        logger.info(f"请求开始: {request.method} {request.url.path}")
        start_time = time.time()
        
        # 处理请求
        response = await call_next(request)
        
        # 请求处理后的日志
        process_time = time.time() - start_time
        logger.info(f"请求完成: {request.method} {request.url.path} - 响应状态: {response.status_code}, 处理时间: {process_time:.3f}s")
        
        return response
```

然后在`app/main.py`中注册：

```python
app.add_middleware(LoggingMiddleware)
``` 