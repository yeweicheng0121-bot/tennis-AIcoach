"""MediaPipe Pose landmark extraction — v2.0."""
import os
from typing import Optional

import cv2
import numpy as np
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from mediapipe import Image, ImageFormat

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker_lite.task")

_landmarker: Optional[vision.PoseLandmarker] = None


def get_landmarker() -> vision.PoseLandmarker:
    global _landmarker
    if _landmarker is None:
        options = vision.PoseLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=_MODEL_PATH),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        _landmarker = vision.PoseLandmarker.create_from_options(options)
    return _landmarker


def extract_landmarks(image_path: str) -> Optional[dict]:
    """Run MediaPipe Pose on a single frame image.

    Returns a dict with 33 keypoint entries, each:
        {"x": float, "y": float, "z": float, "visibility": float}
    Returns None if no pose detected.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = Image(image_format=ImageFormat.SRGB, data=img_rgb)

    landmarker = get_landmarker()
    result = landmarker.detect(mp_image)

    if not result.pose_landmarks or len(result.pose_landmarks) == 0:
        return None

    landmarks = result.pose_landmarks[0]
    out = {}
    for idx, lm in enumerate(landmarks):
        out[idx] = {
            "x": lm.x,
            "y": lm.y,
            "z": lm.z,
            "visibility": lm.visibility,
        }
    return out


def extract_landmarks_batch(frame_paths: list[str]) -> list[Optional[dict]]:
    """Run pose detection on a batch of frames."""
    return [extract_landmarks(p) for p in frame_paths]
