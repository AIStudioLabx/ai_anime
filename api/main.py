"""FastAPI 主应用"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from api.models import (
    EpisodeRequest,
    EpisodeResponse,
    ImageResponse,
    SRTResponse,
    VideoResponse,
    AudioResponse,
    HealthResponse,
)
from services.episode_service import EpisodeService
from services.image_service import ImageService
from services.srt_service import SRTService
from services.video_service import VideoService
from services.audio_service import AudioService

app = FastAPI(
    title="AI 漫剧生成 API",
    description="使用 ComfyUI 生成动画风格视频剧集的 API 服务",
    version="0.1.0",
)

# 静态文件目录
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 从环境变量读取配置
COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
# COMFY_ROOT 已不再需要，保留用于兼容性

# 延迟初始化服务（在需要时创建）
def get_episode_service():
    """获取 episode 服务实例"""
    return EpisodeService(COMFY_URL, None)

def get_image_service():
    """获取图片服务实例"""
    return ImageService(COMFY_URL, None)

# 初始化不需要 ComfyUI 的服务
srt_service = SRTService()
video_service = VideoService()
audio_service = AudioService()


@app.get("/")
async def root():
    """根路径，返回 HTML 页面"""
    from fastapi.responses import FileResponse
    html_path = static_dir / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    # 如果 HTML 文件不存在，返回健康检查响应
    return HealthResponse(status="ok", version="0.1.0")


@app.get("/favicon.ico")
async def favicon():
    """返回 favicon"""
    from fastapi.responses import Response
    # 返回一个简单的空响应，避免 404 错误
    return Response(content=b"", media_type="image/x-icon")


@app.get("/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/api/v1/episodes/render", response_model=EpisodeResponse)
async def render_episode(request: EpisodeRequest):
    """
    完整渲染 episode（图片 + 字幕 + 音频 + 视频）

    可以传入 episode_id 或完整的 episode_data
    """
    try:
        episode_service = get_episode_service()
        
        if request.episode_data:
            episode_data = request.episode_data
        elif request.episode_id:
            episode_data = episode_service.load_episode(request.episode_id)
        else:
            raise HTTPException(status_code=400, detail="必须提供 episode_id 或 episode_data")

        result = episode_service.render_full_episode(episode_data, request.episode_id)

        return EpisodeResponse(
            episode_id=result["episode_id"],
            images=result["images"],
            srt=result["srt"],
            audio=result.get("audio", []),
            video=result["video"],
            message="Episode 渲染完成",
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"渲染失败: {str(e)}")


@app.post("/api/v1/episodes/{episode_id}/images", response_model=ImageResponse)
async def generate_images(episode_id: int):
    """生成图片"""
    try:
        episode_service = get_episode_service()
        image_service = get_image_service()
        
        episode_data = episode_service.load_episode(episode_id)
        images = image_service.generate_images(episode_data)

        return ImageResponse(images=images, message=f"成功生成 {len(images)} 张图片")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片生成失败: {str(e)}")


@app.post("/api/v1/episodes/{episode_id}/srt", response_model=SRTResponse)
async def generate_srt(episode_id: int):
    """生成字幕"""
    try:
        episode_service = get_episode_service()
        episode_data = episode_service.load_episode(episode_id)
        srt_path = srt_service.generate_srt(episode_data, episode_id)

        return SRTResponse(srt_path=str(srt_path), message="字幕生成完成")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"字幕生成失败: {str(e)}")


@app.post("/api/v1/episodes/{episode_id}/audio", response_model=AudioResponse)
async def generate_audio(episode_id: int):
    """生成音频"""
    try:
        episode_service = get_episode_service()
        episode_data = episode_service.load_episode(episode_id)
        audio_files = audio_service.generate_audio(episode_data, episode_id)

        return AudioResponse(
            audio_files=[str(f) for f in audio_files],
            message=f"成功生成 {len(audio_files)} 个音频文件"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音频生成失败: {str(e)}")


@app.post("/api/v1/episodes/{episode_id}/video", response_model=VideoResponse)
async def render_video(episode_id: int):
    """渲染视频"""
    try:
        episode_service = get_episode_service()
        episode_data = episode_service.load_episode(episode_id)

        # 准备视频渲染参数
        # api/ -> 项目根目录（使用绝对路径）
        project_root = Path(__file__).resolve().parent.parent
        images = []
        durations = []
        for shot in episode_data["shots"]:
            # 使用 output 字段作为图片路径
            image_path = project_root / shot.get("image", shot.get("output", ""))
            if image_path.exists():
                images.append(image_path)
                durations.append(shot["duration"])

        if not images:
            raise HTTPException(status_code=400, detail="未找到图片文件，请先生成图片")

        # 生成字幕（如果不存在）
        srt_path = project_root / "output" / f"episode_{episode_id:03d}.srt"
        if not srt_path.exists():
            srt_path = srt_service.generate_srt(episode_data, episode_id)

        # 检查是否有音频文件（如果存在则使用）
        audio_files = None
        audio_dir = project_root / "assets" / "audio"
        if audio_dir.exists():
            # 查找该 episode 的音频文件，按 shot_id 排序
            episode_audio_files = sorted(
                audio_dir.glob(f"episode_{episode_id:03d}_shot_*.mp3"),
                key=lambda x: int(x.stem.split("_shot_")[1])  # 按 shot_id 排序
            )
            if episode_audio_files and len(episode_audio_files) == len(images):
                audio_files = episode_audio_files
                print(f"找到 {len(audio_files)} 个音频文件用于视频渲染")
            elif episode_audio_files:
                print(f"警告: 音频文件数量 ({len(episode_audio_files)}) 与图片数量 ({len(images)}) 不匹配")

        # 渲染视频
        video_path = project_root / "output" / f"episode_{episode_id:03d}.mp4"
        video_path = video_service.render_video(images, durations, srt_path, video_path, audio_files=audio_files)

        return VideoResponse(video_path=str(video_path), message="视频渲染完成")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频渲染失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

