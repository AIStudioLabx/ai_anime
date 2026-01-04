from typing import Dict, Any
import copy
from pathlib import Path


def inject(
    workflow: Dict[str, Any],
    prompt: str,
    seed: int,
    output: str,
) -> Dict[str, Any]:
    """
    将 prompt、seed 和 output 注入到 workflow 中

    Args:
        workflow: workflow JSON 对象
        prompt: 提示词文本
        seed: 随机种子
        output: 输出文件路径前缀

    Returns:
        注入后的 workflow
    """
    # 深拷贝避免修改原始对象
    workflow = copy.deepcopy(workflow)

    for node in workflow["prompt"].values():
        inputs = node.get("inputs", {})

        # 检查并替换 prompt
        if inputs.get("text") == "__PROMPT__":
            inputs["text"] = prompt

        # 检查并替换 seed（检查值而不是键）
        if inputs.get("seed") == "__SEED__":
            inputs["seed"] = seed

        # 检查并替换 output（检查值而不是键）
        if inputs.get("filename_prefix") == "__OUTPUT__":
            # 移除扩展名，ComfyUI 会自动添加序号和扩展名
            output_path = Path(output)
            inputs["filename_prefix"] = str(output_path.with_suffix(''))

    return workflow

