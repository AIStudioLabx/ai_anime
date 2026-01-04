"""图片生成服务"""
import json
import random
from pathlib import Path
from typing import Dict, Any, List

from comfy.client import ComfyUIClient
from comfy.workflow import inject


def build_prompt(character: Dict[str, Any], shot: Dict[str, Any]) -> str:
    """
    构建 prompt 文本

    Args:
        character: 角色信息字典
        shot: 镜头信息字典

    Returns:
        构建好的 prompt 文本
    """
    EMOTION = {
        "suppressed": "calm expression, head slightly down",
        "cold": "cold eyes, head raised",
        "confident": "confident posture",
    }
    FRAMING = {
        "medium": "medium shot",
        "close": "close-up",
        "side": "side view",
    }

    return (
        f"2D anime style, {character['fingerprint']}, "
        f"{shot['scene']}, "
        f"{EMOTION[shot['emotion']]}, "
        f"{FRAMING[shot['framing']]}, "
        "vibrant colors"
    )


class ImageService:
    """图片生成服务"""

    def __init__(self, comfy_url: str = "http://127.0.0.1:8188", comfy_root: str = None):
        """
        初始化服务

        Args:
            comfy_url: ComfyUI 服务地址
            comfy_root: ComfyUI 根目录（已废弃，保留用于兼容性，不再使用）
        """
        self.client = ComfyUIClient(comfy_url, comfy_root)
        # services/ -> 项目根目录（使用绝对路径）
        self.project_root = Path(__file__).resolve().parent.parent

    def generate_images(self, episode_data: Dict[str, Any]) -> List[str]:
        """
        生成图片

        Args:
            episode_data: episode JSON 数据

        Returns:
            生成的图片路径列表
        """
        workflow_path = self.project_root / "workflows" / "image_gen.json"
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow_tpl = json.load(f)

        generated_images = []
        base_seed = episode_data.get("seed", 123456)
        use_random_seed = (base_seed == -1)

        for shot in episode_data["shots"]:
            prompt = build_prompt(episode_data["character"], shot)
            
            # 为每个 shot 生成不同的 seed，确保生成的图片有变化
            shot_id = shot.get("id", len(generated_images) + 1)
            if use_random_seed:
                # 如果 seed 为 -1，每个 shot 都生成完全随机的 seed
                shot_seed = random.randint(0, 2**31 - 1)
            else:
                # 否则基于基础 seed 生成不同的 seed
                shot_seed = base_seed + shot_id * 1000  # 每个 shot 的 seed 相差 1000
            
            workflow = inject(
                workflow_tpl,
                prompt,
                shot_seed,  # 使用不同的 seed
                shot["output"],
            )
            prompt_id = self.client.submit(workflow)

            # 从 output 路径中提取文件名
            expected_filename = Path(shot["output"]).name

            images = self.client.collect_and_cleanup(
                prompt_id,
                target_dir=str(self.project_root / "assets" / "images"),
                expected_filename=expected_filename,
            )

            generated_images.extend([str(img) for img in images])

        return generated_images

