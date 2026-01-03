import time
import requests
import shutil
from pathlib import Path

class ComfyUIClient:
    def __init__(self, base_url="http://127.0.0.1:8188", comfy_root=None):
        self.base_url = base_url
        self.comfy_root = Path(comfy_root) if comfy_root else None

    def submit(self, workflow):
        # 如果 workflow 包含 "prompt" 键，只发送 prompt 部分
        if isinstance(workflow, dict) and "prompt" in workflow:
            prompt_data = workflow["prompt"]
        else:
            prompt_data = workflow
        
        r = requests.post(f"{self.base_url}/prompt", json={"prompt": prompt_data})
        r.raise_for_status()
        return r.json()["prompt_id"]

    def wait_and_collect_images(self, prompt_id, target_dir):
        history_url = f"{self.base_url}/history/{prompt_id}"

        while True:
            r = requests.get(history_url)
            if r.status_code == 200 and r.json():
                break
            time.sleep(1)

        outputs = r.json()[prompt_id]["outputs"]
        collected = []

        for node in outputs.values():
            for img in node.get("images", []):
                if self.comfy_root:
                    # 如果指定了 comfy_root，从 ComfyUI 输出目录复制
                    src = (
                        self.comfy_root
                        / "output"
                        / img.get("subfolder", "")
                        / img["filename"]
                    )
                    dst = Path(target_dir) / img["filename"]
                    shutil.copy(src, dst)
                    collected.append(dst)
                else:
                    # 如果没有指定 comfy_root，假设图片已经在目标目录
                    # 或者通过其他方式处理
                    img_path = Path(target_dir) / img["filename"]
                    if img_path.exists():
                        collected.append(img_path)

        return collected

