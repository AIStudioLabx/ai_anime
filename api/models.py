"""API 数据模型"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class EpisodeRequest(BaseModel):
    """Episode 请求模型"""
    episode_id: Optional[int] = Field(None, description="Episode ID，如果不提供则从 JSON 中读取")
    episode_data: Optional[Dict[str, Any]] = Field(None, description="Episode JSON 数据")


class EpisodeResponse(BaseModel):
    """Episode 响应模型"""
    episode_id: int
    images: List[str] = Field(description="生成的图片路径列表")
    srt: Optional[str] = Field(None, description="字幕文件路径")
    audio: List[str] = Field(default_factory=list, description="生成的音频文件路径列表")
    video: Optional[str] = Field(None, description="视频文件路径")
    message: str = Field(description="处理结果消息")


class ImageResponse(BaseModel):
    """图片生成响应模型"""
    images: List[str] = Field(description="生成的图片路径列表")
    message: str = Field(description="处理结果消息")


class SRTResponse(BaseModel):
    """字幕生成响应模型"""
    srt_path: str = Field(description="字幕文件路径")
    message: str = Field(description="处理结果消息")


class VideoResponse(BaseModel):
    """视频渲染响应模型"""
    video_path: str = Field(description="视频文件路径")
    message: str = Field(description="处理结果消息")


class AudioResponse(BaseModel):
    """音频生成响应模型"""
    audio_files: List[str] = Field(description="生成的音频文件路径列表")
    message: str = Field(description="处理结果消息")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(description="服务状态")
    version: str = Field(description="服务版本")

