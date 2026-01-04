"""视频渲染服务"""
import subprocess
from pathlib import Path
from typing import List, Union, Optional


class VideoService:
    """视频渲染服务"""

    TARGET_W = 720
    TARGET_H = 1280

    def __init__(self):
        # services/ -> 项目根目录（使用绝对路径）
        self.project_root = Path(__file__).resolve().parent.parent

    def render_video(
        self,
        images: List[Union[str, Path]],
        durations: List[float],
        srt_path: Union[str, Path],
        output_path: Union[str, Path],
        audio_files: Optional[List[Union[str, Path]]] = None,
    ) -> Path:
        """
        渲染视频

        Args:
            images: 图片路径列表
            durations: 每个图片的时长列表
            srt_path: 字幕文件路径
            output_path: 输出视频路径
            audio_files: 音频文件路径列表（可选），如果提供则合并到视频中

        Returns:
            生成的视频文件路径
        """
        # 转换为 Path 对象
        images = [Path(img) for img in images]
        srt_path = Path(srt_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        inputs = []
        filter_parts = []

        # 添加视频输入
        for i, (img, dur) in enumerate(zip(images, durations)):
            inputs += ["-loop", "1", "-t", str(dur), "-i", str(img)]
            # 关键：统一 scale + pad
            filter_parts.append(
                f"[{i}:v]scale={self.TARGET_W}:{self.TARGET_H}:force_original_aspect_ratio=decrease,"
                f"pad={self.TARGET_W}:{self.TARGET_H}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]"
            )

        # 添加音频输入（如果有）
        audio_input_count = 0
        if audio_files:
            audio_files = [Path(audio) for audio in audio_files]
            # 确保音频文件数量与图片数量匹配
            if len(audio_files) != len(images):
                # 如果数量不匹配，只使用前 N 个音频文件
                audio_files = audio_files[:len(images)]
            
            for i, (audio_file, dur) in enumerate(zip(audio_files, durations)):
                if audio_file.exists():
                    inputs += ["-i", str(audio_file)]
                    audio_input_count += 1

        # 构建视频 concat
        video_input_count = len(images)
        concat_video_inputs = "".join(f"[v{i}]" for i in range(video_input_count))
        
        # 构建 filter_complex
        if audio_input_count > 0:
            # 有音频：合并视频和音频
            # 音频输入索引从 video_input_count 开始
            audio_streams = [f"[{video_input_count + i}:a]" for i in range(audio_input_count)]
            concat_audio_inputs = "".join(audio_streams)
            
            # 构建字幕滤镜，指定中文字体
            # 使用 force_style 参数指定字体，避免字体查找错误
            # 注意：路径中的特殊字符需要转义
            srt_path_escaped = str(srt_path).replace(":", "\\:").replace("'", "\\'")
            subtitle_filter = f"subtitles='{srt_path_escaped}':force_style='FontName=PingFang SC,FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Shadow=1'"
            
            filter_complex = (
                ";".join(filter_parts)
                + f";{concat_video_inputs}concat=n={video_input_count}:v=1:a=0[outv]"
                + f";{concat_audio_inputs}concat=n={audio_input_count}:v=0:a=1[outa]"
                + f";[outv]{subtitle_filter}[vsub]"
            )
            
            cmd = [
                "ffmpeg",
                "-y",
                *inputs,
                "-filter_complex",
                filter_complex,
                "-map", "[vsub]",
                "-map", "[outa]",
                "-r", "30",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "128k",  # 降低比特率，避免 "Too many bits" 错误
                "-ar", "44100",  # 设置采样率
                str(output_path),
            ]
        else:
            # 无音频：只处理视频
            # 构建字幕滤镜，指定中文字体
            srt_path_escaped = str(srt_path).replace(":", "\\:").replace("'", "\\'")
            subtitle_filter = f"subtitles='{srt_path_escaped}':force_style='FontName=PingFang SC,FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Shadow=1'"
            
            filter_complex = (
                ";".join(filter_parts)
                + f";{concat_video_inputs}concat=n={video_input_count}:v=1:a=0,{subtitle_filter}"
            )
            
            cmd = [
                "ffmpeg",
                "-y",
                *inputs,
                "-filter_complex",
                filter_complex,
                "-r", "30",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]

        subprocess.run(cmd, check=True)
        return output_path

