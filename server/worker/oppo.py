from datetime import datetime
from typing import Any


def parse_oppo_tennis_workout(raw: dict[str, Any]) -> dict[str, Any]:
    """将 OPPO Health SDK 返回的网球模式数据解析为标准化字段。"""
    parsed = {
        "workout_type": raw.get("workout_type", "tennis"),
        "start_time": _parse_timestamp(raw.get("start_time")),
        "end_time": _parse_timestamp(raw.get("end_time")),
        "duration_seconds": raw.get("duration_seconds"),
        "total_shots": raw.get("total_shots"),
        "serve_count": raw.get("serve_count"),
        "forehand_topspin": raw.get("forehand_topspin"),
        "forehand_slice": raw.get("forehand_slice"),
        "backhand_topspin": raw.get("backhand_topspin"),
        "backhand_slice": raw.get("backhand_slice"),
        "avg_swing_speed": raw.get("avg_swing_speed"),
        "avg_heart_rate": raw.get("avg_heart_rate"),
        "max_heart_rate": raw.get("max_heart_rate"),
        "total_distance": raw.get("total_distance"),
        "total_calories": raw.get("total_calories"),
    }
    return parsed


def compute_fitness_breakdown(workout: dict[str, Any], user_birth_year: int | None) -> dict[str, Any]:
    """基于 OPPO 数据和用户年龄，计算体能评分。"""
    age = 2026 - user_birth_year if user_birth_year else 30
    max_hr_est = 220 - age

    avg_hr = workout.get("avg_heart_rate") or 0
    max_hr = workout.get("max_heart_rate") or 0
    distance = workout.get("total_distance") or 0
    duration_min = (workout.get("duration_seconds") or 3600) / 60
    calories = workout.get("total_calories") or 0

    # 心肺评分
    hr_ratio = avg_hr / max_hr_est if max_hr_est > 0 else 0
    if hr_ratio < 0.60:
        cardio_score = 50
    elif hr_ratio < 0.70:
        cardio_score = 70
    elif hr_ratio < 0.78:
        cardio_score = 80
    else:
        cardio_score = 90

    # 移动评分
    distance_per_min = distance / duration_min if duration_min > 0 else 0
    if distance_per_min < 30:
        movement_score = 50
    elif distance_per_min < 45:
        movement_score = 65
    elif distance_per_min < 55:
        movement_score = 75
    elif distance_per_min < 70:
        movement_score = 85
    else:
        movement_score = 95

    # 负荷评分
    cal_per_min = calories / duration_min if duration_min > 0 else 0
    if cal_per_min < 5:
        load_score = 50
    elif cal_per_min < 8:
        load_score = 65
    elif cal_per_min < 12:
        load_score = 75
    else:
        load_score = 90

    # 综合体能等级估算
    fitness_ntrp = round(1.5 + (cardio_score * 0.35 + movement_score * 0.40 + load_score * 0.25) / 40, 1)

    return {
        "fitness_ntrp_equivalent": min(fitness_ntrp, 7.0),
        "cardiovascular_endurance": {"score": cardio_score, "avg_hr": avg_hr, "max_hr": max_hr},
        "movement": {"score": movement_score, "total_distance_m": distance, "distance_per_min": round(distance_per_min, 1)},
        "training_load": {"score": load_score, "total_calories": calories, "calories_per_min": round(cal_per_min, 1)},
    }


def _parse_timestamp(ts: Any) -> datetime | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts / 1000)
    if isinstance(ts, str):
        return datetime.fromisoformat(ts)
    return None
