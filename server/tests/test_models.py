"""Task 3-4: Data model tests — write BEFORE implementation."""
import uuid
import pytest


def test_user_model_fields():
    """User 模型包含所有必要字段。"""
    from server.models.user import User
    assert hasattr(User, "__tablename__")
    assert User.__tablename__ == "users"
    # 核心字段
    cols = User.__table__.columns
    col_names = {c.name for c in cols}
    required = {"id", "phone", "nickname", "gender", "birth_year",
                "playing_years", "self_rated_ntrp", "target_ntrp",
                "handedness", "injury_history", "created_at", "updated_at"}
    assert required.issubset(col_names), f"Missing: {required - col_names}"


def test_video_model_fields():
    """Video 模型包含所有必要字段。"""
    from server.models.video import Video
    cols = Video.__table__.columns
    col_names = {c.name for c in cols}
    required = {"id", "user_id", "duration_seconds", "file_size_bytes",
                "storage_path", "upload_status", "created_at"}
    assert required.issubset(col_names)


def test_health_workout_model_fields():
    """HealthWorkout 模型包含 OPPO 网球模式字段。"""
    from server.models.health import HealthWorkout
    cols = HealthWorkout.__table__.columns
    col_names = {c.name for c in cols}
    required = {"id", "user_id", "total_shots", "serve_count",
                "forehand_topspin", "forehand_slice", "backhand_topspin",
                "backhand_slice", "avg_swing_speed", "avg_heart_rate",
                "max_heart_rate", "total_distance", "total_calories", "raw_data"}
    assert required.issubset(col_names), f"Missing: {required - col_names}"


def test_assessment_model_fields():
    """Assessment 模型包含所有必要字段。"""
    from server.models.assessment import Assessment
    cols = Assessment.__table__.columns
    col_names = {c.name for c in cols}
    required = {"id", "user_id", "video_id", "health_workout_id",
                "overall_ntrp", "ntrp_confidence", "technique_breakdown",
                "fitness_breakdown", "strengths", "weaknesses",
                "key_frames", "report_markdown", "status", "created_at"}
    assert required.issubset(col_names)


def test_training_plan_model_fields():
    """TrainingPlan 模型包含所有必要字段。"""
    from server.models.assessment import TrainingPlan
    cols = TrainingPlan.__table__.columns
    col_names = {c.name for c in cols}
    required = {"id", "user_id", "assessment_id", "duration_weeks",
                "sessions_per_week", "primary_goals", "weekly_plans",
                "home_exercises", "status", "created_at"}
    assert required.issubset(col_names)


def test_ntrp_chunk_model_fields():
    """NtrpChunk 模型包含 pgvector 向量字段。"""
    from server.models.knowledge import NtrpChunk
    cols = NtrpChunk.__table__.columns
    col_names = {c.name for c in cols}
    required = {"id", "ntrp_level", "module", "category", "content", "embedding"}
    assert required.issubset(col_names)


def test_user_can_instantiate():
    """User 模型可以正常实例化。"""
    from server.models.user import User
    u = User(phone="13800000001", nickname="测试用户", birth_year=1995,
             playing_years=3.0, self_rated_ntrp=3.0, target_ntrp=3.5)
    assert u.phone == "13800000001"
    assert u.nickname == "测试用户"
    assert u.self_rated_ntrp == 3.0
    # id is generated on DB flush, not on __init__ — expected SQLAlchemy behavior
