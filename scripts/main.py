from pathlib import Path
from generate_srt import generate_srt
from render_video import render_video
import json

EPISODE = Path("../episodes/episode_001.json")
SRT = Path("../output/episode_001.srt")
OUT = Path("../output/episode_001.mp4")

data = json.loads(EPISODE.read_text(encoding="utf-8"))

images = []
durations = []

for shot in data["shots"]:
    images.append(Path("../") / shot["image"])
    durations.append(shot["duration"])

generate_srt(EPISODE, SRT)
render_video(images, durations, SRT, OUT)

print("✅ Episode rendered:", OUT)