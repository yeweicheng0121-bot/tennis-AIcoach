"""Biomechanics calculations from MediaPipe landmarks — v2.0."""
import math
from typing import Optional

import numpy as np


# ── Landmark indices (MediaPipe Pose) ──────────────────────
# 11: left shoulder, 12: right shoulder
# 13: left elbow, 14: right elbow
# 15: left wrist, 16: right wrist
# 23: left hip, 24: right hip
# 25: left knee, 26: right knee
# 27: left ankle, 28: right ankle

def _pt(lm: dict) -> np.ndarray:
    return np.array([lm["x"], lm["y"], lm.get("z", 0)])


def joint_angle(a: dict, b: dict, c: dict) -> float:
    """Angle ABC in degrees (b is the vertex). e.g. elbow: shoulder-elbow-wrist."""
    ba = _pt(a) - _pt(b)
    bc = _pt(c) - _pt(b)
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-9:
        return 0.0
    cos = np.dot(ba, bc) / denom
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def shoulder_hip_angle(
    l_shoulder: dict, r_shoulder: dict, l_hip: dict, r_hip: dict
) -> float:
    """Angle between shoulder line and hip line (torso twist in degrees)."""
    sv = np.array([r_shoulder["x"] - l_shoulder["x"], r_shoulder["y"] - l_shoulder["y"]])
    hv = np.array([r_hip["x"] - l_hip["x"], r_hip["y"] - l_hip["y"]])
    denom = np.linalg.norm(sv) * np.linalg.norm(hv)
    if denom < 1e-9:
        return 0.0
    cos = np.dot(sv, hv) / denom
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def wrist_speed(
    wrist_positions: list[dict], fps: float, window: int = 3
) -> float:
    """Estimate wrist speed from consecutive frames (pixels/frame → km/h estimate)."""
    if len(wrist_positions) < window + 1:
        return 0.0
    speeds = []
    for i in range(window, len(wrist_positions)):
        a = wrist_positions[i - window]
        b = wrist_positions[i]
        dx = b["x"] - a["x"]
        dy = b["y"] - a["y"]
        dist = math.sqrt(dx * dx + dy * dy)
        speeds.append(dist * fps / window)
    return max(speeds) if speeds else 0.0


def hip_displacement(a: dict, b: dict) -> float:
    """Euclidean distance between two hip midpoints (for movement tracking)."""
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)


def hip_midpoint(l_hip: dict, r_hip: dict) -> dict:
    """Midpoint of left and right hips."""
    return {"x": (l_hip["x"] + r_hip["x"]) / 2, "y": (l_hip["y"] + r_hip["y"]) / 2}


def find_key_frames(
    landmarks_by_frame: list[Optional[dict]], fps: float, num_key: int = 3
) -> list[dict]:
    """Select key frames by biomechanical extremum.

    For each frame where pose is detected, compute:
    - shoulder_hip_angle (torso twist)
    - right_wrist_speed (contact detection)
    - left_wrist_y (toss height for serve)

    Returns top N frames across all metrics.
    """
    scored = []
    # Build a window of recent wrist positions for speed calc
    recent_rw: list[dict] = []
    recent_lw: list[dict] = []

    for idx, lms in enumerate(landmarks_by_frame):
        if lms is None:
            recent_rw = []
            recent_lw = []
            continue

        rw = lms.get(16, {})
        lw = lms.get(15, {})
        recent_rw.append(rw)
        recent_lw.append(lw)
        if len(recent_rw) > 5:
            recent_rw.pop(0)
            recent_lw.pop(0)

        sh = lms.get(11, {})
        rh = lms.get(12, {})
        lh = lms.get(23, {})
        rhp = lms.get(24, {})

        twist = shoulder_hip_angle(sh, rh, lh, rhp) if all(k in lms for k in [11, 12, 23, 24]) else 0
        rw_speed = wrist_speed(recent_rw, fps) if len(recent_rw) >= 3 else 0
        lw_y = lw.get("y", 0.5)

        scored.append({
            "frame_idx": idx,
            "twist": twist,
            "rw_speed": rw_speed,
            "lw_y": lw_y,
        })

    if not scored:
        return []

    # Pick extremum frames
    selected_indices = set()
    result = []

    # Top twist frames
    for s in sorted(scored, key=lambda x: x["twist"], reverse=True):
        if s["frame_idx"] not in selected_indices and len(result) < num_key:
            selected_indices.add(s["frame_idx"])
            result.append(s)

    # Top contact (wrist speed) frames
    for s in sorted(scored, key=lambda x: x["rw_speed"], reverse=True):
        if s["frame_idx"] not in selected_indices and len(result) < num_key * 2:
            selected_indices.add(s["frame_idx"])
            result.append(s)

    # Toss peak (lowest left wrist Y = highest toss)
    for s in sorted(scored, key=lambda x: x["lw_y"]):
        if s["frame_idx"] not in selected_indices and len(result) < num_key * 3:
            selected_indices.add(s["frame_idx"])
            result.append(s)

    return result[:num_key]


def classify_shot_types(
    landmarks_by_frame: list[Optional[dict]]
) -> dict[str, int]:
    """Rough shot type classification based on wrist trajectory patterns.

    Returns counts: {"forehand": N, "backhand": N, "serve": N, "volley": N}
    """
    counts = {"forehand": 0, "backhand": 0, "serve": 0, "volley": 0}

    for lms in landmarks_by_frame:
        if lms is None:
            continue
        rw = lms.get(16, {})
        lw = lms.get(15, {})
        rw_y = rw.get("y", 0.5)
        lw_y = lw.get("y", 0.5)

        # Simple heuristic:
        # Serve: either wrist above shoulder level (y < 0.4 in normalized coords)
        if rw_y < 0.35 or lw_y < 0.35:
            counts["serve"] += 1
        # Volley: wrist in upper-mid zone
        elif 0.35 <= rw_y < 0.5:
            counts["volley"] += 1
        # Forehand/backhand based on x position
        elif rw.get("x", 0.5) > 0.5:
            counts["forehand"] += 1
        else:
            counts["backhand"] += 1

    return counts


def compute_angle_stats(
    landmarks_by_frame: list[Optional[dict]]
) -> dict:
    """Compute aggregate angle statistics across all detected frames."""
    elbows_r, knees_r, shoulders, twists = [], [], [], []

    for lms in landmarks_by_frame:
        if lms is None or not all(k in lms for k in [11, 12, 14, 16, 23, 24, 26, 28]):
            continue

        elbows_r.append(round(joint_angle(lms[12], lms[14], lms[16]), 1))
        knees_r.append(round(joint_angle(lms[24], lms[26], lms[28]), 1))
        shoulders.append(round(joint_angle(lms[14], lms[12], lms[24]), 1))
        twists.append(round(shoulder_hip_angle(lms[11], lms[12], lms[23], lms[24]), 1))

    def _stats(vals):
        if not vals:
            return {"min": 0, "max": 0, "avg": 0}
        return {"min": round(min(vals), 1), "max": round(max(vals), 1), "avg": round(sum(vals) / len(vals), 1)}

    return {
        "elbow_right": _stats(elbows_r),
        "knee_right": _stats(knees_r),
        "shoulder": _stats(shoulders),
        "torso_twist": _stats(twists),
        "frames_detected": sum(1 for l in landmarks_by_frame if l is not None),
        "total_frames": len(landmarks_by_frame),
    }
