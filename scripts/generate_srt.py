import json
from pathlib import Path

def generate_srt(episode_json: Path, out_srt: Path):
    data = json.loads(episode_json.read_text(encoding="utf-8"))

    index = 1
    current_time = 0.0
    lines = []

    def fmt(t):
        ms = int((t - int(t)) * 1000)
        s = int(t) % 60
        m = int(t) // 60
        return f"00:{m:02d}:{s:02d},{ms:03d}"

    for shot in data["shots"]:
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

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    generate_srt(
        project_root / "assets" / "episodes" / "episode_001.json",
        project_root / "output" / "episode_001.srt"
    )
