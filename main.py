import uvicorn
from app.main import app

def main():
    """
    启动API网关服务
    """
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    print("所有路由:")
    for route in app.routes:
        print(f"Path: {route.path}, Name: {route.name}")
    main()
