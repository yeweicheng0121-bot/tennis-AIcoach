"""Task 12: ffmpeg keyframe extraction from uploaded videos."""
import subprocess
import os
from pathlib import Path


def extract_keyframes(video_path: str, output_dir: str, interval_seconds: int = 15) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    output_pattern = os.path.join(output_dir, "frame_%04d.jpg")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{interval_seconds},scale=512:-1",
        "-q:v", "3", "-y", output_pattern,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    frame_files = sorted(Path(output_dir).glob("frame_*.jpg"))
    return [str(f) for f in frame_files]
