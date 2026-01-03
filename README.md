# AI 漫剧生成项目

使用 ComfyUI 生成动画风格的视频剧集。

## 安装

### 推荐方式：安装为可编辑包

将项目安装为可编辑包（editable install），这样 Python 可以正确识别内部模块，避免 `ModuleNotFoundError`：

```bash
# 在项目根目录执行
pip install -e .
```

这会：
- 安装项目依赖（requests 等）
- 将项目注册到 Python 环境中
- 允许直接导入 `comfy` 和 `scripts` 模块
- 代码修改后无需重新安装

安装后，你就可以在任何地方运行：

```bash
python scripts/render_episode.py
```

### 替代方式：仅安装依赖

如果不想安装为包，可以只安装依赖：

```bash
pip install -r requirements.txt
```

但这种方式需要手动处理导入路径问题（不推荐）。

## 使用方法

### 1. 启动 ComfyUI 服务

确保 ComfyUI 在本地运行（默认地址：`http://127.0.0.1:8188`）：

```bash
# 在另一个终端窗口启动 ComfyUI
cd /path/to/ComfyUI
python main.py --port 8188
```

### 2. 生成图片

```bash
python scripts/render_episode.py
```

脚本会读取 `assets/episodes/episode_001.json`，为每个 shot 生成图片并保存到 `assets/images/`。

### 3. 生成字幕和视频（可选）

```bash
# 生成字幕
python scripts/generate_srt.py

# 渲染视频（需要安装 ffmpeg）
python scripts/render_video.py
```

## 项目结构

```
ai_anime/
├── assets/
│   ├── images/            # 输出图片
│   └── episodes/          # episode JSON 文件
├── workflows/
│   └── image_gen.json     # ComfyUI workflow 模板
├── comfy/                 # ComfyUI 客户端和工具
│   ├── client.py
│   └── workflow.py
├── scripts/               # 脚本文件
│   ├── render_episode.py  # 主入口
│   ├── generate_srt.py
│   └── render_video.py
└── output/                # 输出目录
```

## 依赖

- Python >= 3.11.8
- requests >= 2.31.0
- ffmpeg（用于视频渲染）
