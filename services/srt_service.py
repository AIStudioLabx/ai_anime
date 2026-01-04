"""字幕生成服务"""
import json
from pathlib import Path
from typing import Dict, Any


class SRTService:
    """字幕生成服务"""

    def __init__(self):
        # services/ -> 项目根目录（使用绝对路径）
        self.project_root = Path(__file__).resolve().parent.parent

    def generate_srt(self, episode_data: Dict[str, Any], episode_id: int = None) -> Path:
        """
        生成字幕文件

        Args:
            episode_data: episode JSON 数据
            episode_id: episode ID，如果不提供则从 episode_data 中读取

        Returns:
            生成的 SRT 文件路径
        """
        if episode_id is None:
            episode_id = episode_data.get("episode_id", 1)

        out_srt = self.project_root / "output" / f"episode_{episode_id:03d}.srt"
        out_srt.parent.mkdir(parents=True, exist_ok=True)

        index = 1
        current_time = 0.0
        lines = []

        def fmt(t):
            ms = int((t - int(t)) * 1000)
            s = int(t) % 60
            m = int(t) // 60
            return f"00:{m:02d}:{s:02d},{ms:03d}"

        for shot in episode_data["shots"]:
            duration = shot["duration"]
            subtitles = shot["subtitles"]
            per_line = duration / max(len(subtitles), 1)

            for text in subtitles:
                start = current_time
                end = start + per_line * 0.9

                lines.append(f"{index}")
                lines.append(f"{fmt(start)} --> {fmt(end)}")
                lines.append(text)
                lines.append("")
                index += 1

                current_time += per_line

        out_srt.write_text("\n".join(lines), encoding="utf-8")
        return out_srt

