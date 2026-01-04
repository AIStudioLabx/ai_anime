import json
from pathlib import Path
from typing import Dict, Any

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


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    episode_path = project_root / "assets" / "episodes" / "episode_001.json"
    workflow_path = project_root / "workflows" / "image_gen.json"

    with open(episode_path, "r", encoding="utf-8") as f:
        episode = json.load(f)
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow_tpl = json.load(f)

    client = ComfyUIClient()

    for shot in episode["shots"]:
        prompt = build_prompt(episode["character"], shot)
        workflow = inject(
            workflow_tpl,
            prompt,
            episode["seed"],
            shot["output"],
        )
        prompt_id = client.submit(workflow)

        # 从 output 路径中提取文件名（如 "assets/images/shot_1.png" -> "shot_1.png"）
        expected_filename = Path(shot["output"]).name

        images = client.collect_and_cleanup(
            prompt_id,
            target_dir="assets/images",
            expected_filename=expected_filename,
        )
        
        print(f"✅ 生成完成: {shot['output']}")
