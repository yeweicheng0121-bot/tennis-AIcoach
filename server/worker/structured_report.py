"""Generate structured JSON from MediaPipe biomechanics data — v2.0."""
from typing import Optional

from server.worker.biomechanics import (
    compute_angle_stats,
    classify_shot_types,
    find_key_frames,
)


def build_structured_data(
    landmarks_by_frame: list[Optional[dict]],
    all_frame_paths: list[str],
    fps: float,
    video_duration: float,
    focus_module: Optional[str] = None,
) -> dict:
    """Build a ~5KB structured JSON that replaces the old image-based frame analysis.

    This is the primary input to Claude for report generation.
    """
    angle_stats = compute_angle_stats(landmarks_by_frame)
    shot_types = classify_shot_types(landmarks_by_frame)
    key_frames = find_key_frames(landmarks_by_frame, fps, num_key=3)

    # Determine covered modules from shot type distribution
    covered = []
    total_frames_with_pose = angle_stats["frames_detected"]
    if total_frames_with_pose > 0:
        for st in ["forehand", "backhand", "serve", "volley"]:
            pct = shot_types.get(st, 0) / total_frames_with_pose * 100
            if pct > 5:  # at least 5% of frames
                covered.append(st)
    if not covered:
        covered = ["unknown"]
    if "footwork" not in covered and total_frames_with_pose > 20:
        covered.append("footwork")

    return {
        "video": {
            "duration_sec": round(video_duration, 1),
            "fps": round(fps, 1),
            "total_frames": len(landmarks_by_frame),
            "frames_with_pose": total_frames_with_pose,
            "detection_rate": round(total_frames_with_pose / max(len(landmarks_by_frame), 1) * 100, 1)
        },
        "focus_module": focus_module,
        "covered_modules": covered,
        "shot_type_distribution": shot_types,
        "angle_statistics": angle_stats,
        "key_frames": [
            {
                "frame_idx": kf["frame_idx"],
                "frame_path": all_frame_paths[kf["frame_idx"]] if kf["frame_idx"] < len(all_frame_paths) else "",
                "twist_deg": round(kf["twist"], 1),
                "wrist_speed": round(kf["rw_speed"], 3),
                "why_selected": _explain_keyframe(kf),
            }
            for kf in key_frames
        ],
    }


def _explain_keyframe(kf: dict) -> str:
    """Human-readable reason for keyframe selection."""
    reasons = []
    if kf["twist"] > 30:
        reasons.append("torso twist peak")
    if kf["rw_speed"] > 0.01:
        reasons.append("contact moment (wrist speed peak)")
    if kf["lw_y"] < 0.3:
        reasons.append("toss peak (non-dominant hand highest)")
    return ", ".join(reasons) if reasons else "biomechanical extremum"
