"""Episode 完整流程服务"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

from .image_service import ImageService
from .srt_service import SRTService
from .video_service import VideoService
from .audio_service import AudioService


class EpisodeService:
    """Episode 完整流程服务"""

    def __init__(self, comfy_url: str = "http://127.0.0.1:8188", comfy_root: str = None):
        """
        初始化服务

        Args:
            comfy_url: ComfyUI 服务地址
            comfy_root: ComfyUI 根目录（已废弃，保留用于兼容性，不再使用）
        """
        self.image_service = ImageService(comfy_url, comfy_root)
        self.srt_service = SRTService()
        self.video_service = VideoService()
        self.audio_service = AudioService()
        # services/ -> 项目根目录（使用绝对路径）
        self.project_root = Path(__file__).resolve().parent.parent

    def render_full_episode(
        self,
        episode_data: Dict[str, Any],
        episode_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        完整渲染 episode（图片 + 字幕 + 音频 + 视频）

        Args:
            episode_data: episode JSON 数据
            episode_id: episode ID，如果不提供则从 episode_data 中读取

        Returns:
            渲染结果字典，包含图片、字幕、音频、视频路径
        """
        if episode_id is None:
            episode_id = episode_data.get("episode_id", 1)

        # 1. 生成图片
        image_paths = self.image_service.generate_images(episode_data)

        # 2. 生成字幕
        srt_path = self.srt_service.generate_srt(episode_data, episode_id)

        # 3. 生成音频
        try:
            audio_paths = self.audio_service.generate_audio(episode_data, episode_id)
        except Exception as e:
            # 如果音频生成失败，记录错误但继续处理
            print(f"警告: 音频生成失败: {e}")
            audio_paths = []

        # 4. 准备视频渲染参数
        images = []
        durations = []
        for shot in episode_data["shots"]:
            # 使用 output 字段作为图片路径
            image_path = self.project_root / shot.get("image", shot.get("output", ""))
            if image_path.exists():
                images.append(image_path)
                durations.append(shot["duration"])

        # 5. 渲染视频（如果生成了音频，则合并音频轨道）
        video_path = self.project_root / "output" / f"episode_{episode_id:03d}.mp4"
        video_path = self.video_service.render_video(
            images, durations, srt_path, video_path,
            audio_files=audio_paths if audio_paths else None
        )

        return {
            "episode_id": episode_id,
            "images": [str(p) for p in image_paths],
            "srt": str(srt_path),
            "audio": [str(p) for p in audio_paths] if audio_paths else [],
            "video": str(video_path),
        }

    def load_episode(self, episode_id: int) -> Dict[str, Any]:
        """
        加载 episode JSON 文件

        Args:
            episode_id: episode ID

        Returns:
            episode 数据字典
        """
        episode_path = (
            self.project_root / "assets" / "episodes" / f"episode_{episode_id:03d}.json"
        )
        if not episode_path.exists():
            raise FileNotFoundError(f"Episode {episode_id} not found: {episode_path}")

        with open(episode_path, "r", encoding="utf-8") as f:
            return json.load(f)

