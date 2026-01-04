import time
import requests
from pathlib import Path
from typing import Optional

class ComfyUIClient:
    def __init__(self, base_url: str, comfy_root: Optional[str] = None):
        """
        初始化 ComfyUI 客户端
        
        Args:
            base_url: ComfyUI 服务地址（如 "http://127.0.0.1:8188"）
            comfy_root: ComfyUI 根目录（已废弃，保留用于兼容性，不再使用）
        """
        self.base_url = base_url.rstrip('/')

    def submit(self, workflow):
        """
        提交 workflow 到 ComfyUI
        
        Args:
            workflow: workflow 对象，可以是完整对象（包含 "prompt" 键）或直接是 prompt 字典
            
        Returns:
            prompt_id
        """
        # 如果 workflow 包含 "prompt" 键，只发送 prompt 部分
        if isinstance(workflow, dict) and "prompt" in workflow:
            prompt_data = workflow["prompt"]
        else:
            prompt_data = workflow
        
        r = requests.post(
            f"{self.base_url}/prompt",
            json={"prompt": prompt_data},
            timeout=10
        )
        r.raise_for_status()
        return r.json()["prompt_id"]

    def collect_and_cleanup(
        self,
        prompt_id: str,
        target_dir: str,
        expected_filename: Optional[str] = None,
    ):
        """
        通过 HTTP API 收集图片（不依赖本地文件系统）
        
        Args:
            prompt_id: ComfyUI 任务 ID
            target_dir: 目标目录
            expected_filename: 期望的文件名（如 "shot_1.png"），如果提供则重命名
            
        Returns:
            收集到的文件路径列表
        """
        history_url = f"{self.base_url}/history/{prompt_id}"

        # 1. 等待任务完成
        while True:
            r = requests.get(history_url)
            if r.status_code == 200:
                history = r.json()
                if prompt_id in history:
                    break
            time.sleep(1)

        outputs = history[prompt_id]["outputs"]
        collected = []

        for node in outputs.values():
            for img in node.get("images", []):
                filename = img["filename"]
                subfolder = img.get("subfolder", "")
                image_type = img.get("type", "output")  # output, input, temp
                
                # 2. 通过 HTTP API 下载图片
                # ComfyUI 的图片查看 API: /view?filename=xxx&subfolder=xxx&type=output
                view_params = {
                    "filename": filename,
                    "type": image_type,
                }
                if subfolder:
                    view_params["subfolder"] = subfolder
                
                view_url = f"{self.base_url}/view"
                img_response = requests.get(view_url, params=view_params, stream=True)
                img_response.raise_for_status()
                
                # 3. 确定目标文件名
                if expected_filename:
                    dst = Path(target_dir) / expected_filename
                else:
                    dst = Path(target_dir) / filename
                
                # 确保目标目录存在
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # 4. 保存图片
                with open(dst, "wb") as f:
                    for chunk in img_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # 5. 验证文件已保存
                if not dst.exists() or dst.stat().st_size == 0:
                    raise RuntimeError(f"下载失败: {dst}")
                
                collected.append(dst)

        return collected
