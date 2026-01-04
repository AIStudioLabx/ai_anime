#!/bin/bash
# 启动 FastAPI 服务

# 设置环境变量（根据实际情况修改）
export COMFY_URL="${COMFY_URL:-http://127.0.0.1:8188}"
# 注意：不再需要 COMFY_ROOT，ComfyUI 客户端通过 HTTP API 获取图片

# 启动服务
python main.py

