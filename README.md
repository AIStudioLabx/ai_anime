# AI 漫剧生成项目

使用 ComfyUI 生成动画风格的视频剧集的 FastAPI 服务。

## 安装

### 推荐方式：安装为可编辑包

将项目安装为可编辑包（editable install），这样 Python 可以正确识别内部模块，避免 `ModuleNotFoundError`：

```bash
# 在项目根目录执行
pip install -e .
```

这会：
- 安装项目依赖（requests, fastapi, uvicorn 等）
- 将项目注册到 Python 环境中
- 允许直接导入所有模块
- 代码修改后无需重新安装

## 配置

设置环境变量（可选）：

```bash
export COMFY_URL="http://127.0.0.1:8188"  # ComfyUI 服务地址
```

**注意**：现在 ComfyUI 客户端通过 HTTP API 获取图片，不再需要本地文件系统访问，因此不需要设置 `COMFY_ROOT`。

## 启动服务

### 方式 1：使用 main.py（推荐）

```bash
python main.py
```

### 方式 2：使用 uvicorn 直接启动

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## API 接口

### 1. 健康检查

```bash
GET /health
```

### 2. 完整渲染 Episode

```bash
POST /api/v1/episodes/render
Content-Type: application/json

{
  "episode_id": 1
}
```

或者直接传入 episode 数据：

```bash
POST /api/v1/episodes/render
Content-Type: application/json

{
  "episode_data": {
    "episode_id": 1,
    "seed": 123456,
    "character": {...},
    "shots": [...]
  }
}
```

### 3. 生成图片

```bash
POST /api/v1/episodes/{episode_id}/images
```

### 4. 生成字幕

```bash
POST /api/v1/episodes/{episode_id}/srt
```

### 5. 渲染视频

```bash
POST /api/v1/episodes/{episode_id}/video
```

## 使用示例

### 使用 curl

```bash
# 完整渲染
curl -X POST "http://localhost:8000/api/v1/episodes/render" \
  -H "Content-Type: application/json" \
  -d '{"episode_id": 1}'

# 只生成图片
curl -X POST "http://localhost:8000/api/v1/episodes/1/images"

# 只生成字幕
curl -X POST "http://localhost:8000/api/v1/episodes/1/srt"

# 只渲染视频
curl -X POST "http://localhost:8000/api/v1/episodes/1/video"
```

### 使用 Python requests

```python
import requests

# 完整渲染
response = requests.post(
    "http://localhost:8000/api/v1/episodes/render",
    json={"episode_id": 1}
)
result = response.json()
print(result)
```

## 项目结构

```
ai_anime/
├── api/                    # FastAPI 应用
│   ├── main.py            # API 路由和端点
│   └── models.py          # Pydantic 数据模型
├── services/              # 业务逻辑服务层
│   ├── image_service.py   # 图片生成服务
│   ├── srt_service.py     # 字幕生成服务
│   ├── video_service.py   # 视频渲染服务
│   └── episode_service.py # Episode 完整流程服务
├── comfy/                 # ComfyUI 客户端和工具
│   ├── client.py
│   └── workflow.py
├── assets/
│   ├── images/            # 输出图片
│   └── episodes/          # episode JSON 文件
├── workflows/
│   └── image_gen.json     # ComfyUI workflow 模板
├── output/                # 输出目录
│   ├── *.srt             # 字幕文件
│   └── *.mp4             # 视频文件
└── main.py               # 服务入口
```

## 依赖

- Python >= 3.11.8
- requests >= 2.31.0
- fastapi >= 0.104.0
- uvicorn >= 0.24.0
- pydantic >= 2.5.0
- ffmpeg（用于视频渲染）

## 开发

### 运行开发服务器（自动重载）

```bash
python main.py
```

### 查看 API 文档

启动服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
