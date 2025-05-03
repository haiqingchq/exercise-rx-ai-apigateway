import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
import json
from typing import Dict, List, Optional, Any

# 创建模拟服务
def create_mock_service(name: str, port: int):
    app = FastAPI(title=f"Mock {name.capitalize()} Service")
    
    @app.get("/")
    async def root():
        return {"message": f"这是模拟的{name}服务"}
    
    @app.get("/info")
    async def info():
        return {"service": name, "version": "1.0.0"}
    
    @app.get("/echo")
    async def echo(request: Request, authorization: Optional[str] = Header(None)):
        # 打印所有请求数据
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        
        try:
            body = await request.json()
        except:
            body = await request.body()
            if body:
                try:
                    body = body.decode("utf-8")
                except:
                    body = str(body)
            else:
                body = None
        
        return {
            "service": name,
            "received": {
                "method": request.method,
                "url": str(request.url),
                "headers": headers,
                "query_params": query_params,
                "body": body
            }
        }
    
    return app

# 用户服务 (8001端口)
user_app = create_mock_service("user", 8001)

@user_app.get("/profile")
async def user_profile(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="需要认证")
    
    return {
        "id": 1,
        "username": "testuser",
        "email": "testuser@example.com",
        "full_name": "Test User"
    }

@user_app.get("/users")
async def list_users(skip: int = 0, limit: int = 10):
    return [
        {"id": 1, "username": "user1"},
        {"id": 2, "username": "user2"},
        {"id": 3, "username": "user3"},
    ][skip:skip+limit]

# 产品服务 (8002端口)
product_app = create_mock_service("product", 8002)

@product_app.get("/products")
async def list_products(skip: int = 0, limit: int = 10):
    return [
        {"id": 1, "name": "产品1", "price": 100},
        {"id": 2, "name": "产品2", "price": 200},
        {"id": 3, "name": "产品3", "price": 300},
    ][skip:skip+limit]

@product_app.get("/products/{product_id}")
async def get_product(product_id: int):
    products = {
        1: {"id": 1, "name": "产品1", "price": 100},
        2: {"id": 2, "name": "产品2", "price": 200},
        3: {"id": 3, "name": "产品3", "price": 300},
    }
    if product_id not in products:
        raise HTTPException(status_code=404, detail="产品不存在")
    return products[product_id]

# 订单服务 (8003端口)
order_app = create_mock_service("order", 8003)

@order_app.get("/orders")
async def list_orders(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="需要认证")
    
    return [
        {"id": 1, "user_id": 1, "product_id": 1, "quantity": 2, "total": 200},
        {"id": 2, "user_id": 1, "product_id": 2, "quantity": 1, "total": 200},
    ]

@order_app.post("/orders")
async def create_order(request: Request, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="需要认证")
    
    try:
        order_data = await request.json()
        return {
            "id": 3,
            "user_id": order_data.get("user_id"),
            "product_id": order_data.get("product_id"),
            "quantity": order_data.get("quantity", 1),
            "total": 100 * order_data.get("quantity", 1),
            "status": "created"
        }
    except:
        raise HTTPException(status_code=400, detail="无效的订单数据")

# 启动函数
def start_user_service():
    uvicorn.run(user_app, host="0.0.0.0", port=8001)

def start_product_service():
    uvicorn.run(product_app, host="0.0.0.0", port=8002)

def start_order_service():
    uvicorn.run(order_app, host="0.0.0.0", port=8003)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("请指定要启动的服务: user, product, order")
        sys.exit(1)
    
    service = sys.argv[1].lower()
    if service == "user":
        start_user_service()
    elif service == "product":
        start_product_service()
    elif service == "order":
        start_order_service()
    else:
        print(f"未知的服务: {service}")
        print("可用服务: user, product, order")
        sys.exit(1) 