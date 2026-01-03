import subprocess
from pathlib import Path

TARGET_W = 720
TARGET_H = 1280

def render_video(images, durations, srt_path, output_path):
    inputs = []
    filter_parts = []

    for i, (img, dur) in enumerate(zip(images, durations)):
        inputs += ["-loop", "1", "-t", str(dur), "-i", str(img)]
        # 关键：统一 scale + pad
        filter_parts.append(
            f"[{i}:v]scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease,"
            f"pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]"
        )

    concat_inputs = "".join(f"[v{i}]" for i in range(len(images)))
    filter_complex = (
        ";".join(filter_parts)
        + f";{concat_inputs}concat=n={len(images)}:v=1:a=0,subtitles={srt_path}"
    )

    cmd = [
        "ffmpeg",
        *inputs,
        "-filter_complex", filter_complex,
        "-r", "30",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]

    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    render_video(
        images=[
            project_root / "assets" / "images" / "shot_1.png",
            project_root / "assets" / "images" / "shot_2.png",
            project_root / "assets" / "images" / "shot_3.png",
        ],
        durations=[9, 9, 17],
        srt_path=project_root / "output" / "episode_001.srt",
        output_path=project_root / "output" / "episode_001.mp4"
    )
