import subprocess
import os
from pathlib import Path

from server.config import settings


def extract_keyframes(video_path: str, output_dir: str, interval_seconds: int = 15) -> list[str]:
    """从视频中每隔 interval_seconds 秒抽取一帧，返回帧文件路径列表。"""
    os.makedirs(output_dir, exist_ok=True)

    output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps=1/{interval_seconds},scale=512:-1",
        "-q:v", "3",
        "-y",
        output_pattern,
    ]

    subprocess.run(cmd, check=True, capture_output=True, text=True)

    frame_files = sorted(Path(output_dir).glob("frame_*.jpg"))
    return [str(f) for f in frame_files]
