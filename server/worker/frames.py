"""Frame extraction via OpenCV — v2.0 replacement for ffmpeg-based extraction."""
import os
import cv2
from typing import Optional


def extract_all_frames(video_path: str, output_dir: str) -> tuple[list[str], float]:
    """Extract every frame from a video using OpenCV.

    Returns:
        (frame_paths, fps) — list of saved JPEG paths and the video FPS.
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0  # fallback

    frames = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        path = os.path.join(output_dir, f"frame_{idx:06d}.jpg")
        cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frames.append(path)
        idx += 1

    cap.release()
    return frames, fps


def read_frame_image(path: str):
    """Read a frame as BGR numpy array (for MediaPipe)."""
    img = cv2.imread(path)
    if img is None:
        raise RuntimeError(f"Cannot read frame: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


# Keep backward-compatible signature for analyze.py migration
def extract_keyframes(
    video_path: str,
    output_dir: str,
    interval_seconds: int = 15,
) -> list[str]:
    """Legacy stub — calls extract_all_frames and subsamples. Remove after migration."""
    all_frames, _ = extract_all_frames(video_path, output_dir)
    return all_frames[::interval_seconds * 2]  # rough subsample
