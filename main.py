"""FastAPI 服务入口"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",  # 使用导入字符串以支持 reload
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式，代码变更自动重载
    )

