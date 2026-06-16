"""Tasks 6-9: API endpoint tests — write BEFORE implementation."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from server.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_register_and_login(client):
    """注册 → 登录 返回 token。"""
    resp = await client.post("/auth/register", json={"phone": "13800000001", "password": "test123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # 重复注册
    resp = await client.post("/auth/register", json={"phone": "13800000001", "password": "test123"})
    assert resp.status_code == 400

    # 登录
    resp = await client.post("/auth/login", json={"phone": "13800000001", "password": "test123"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """错误密码返回 401。"""
    await client.post("/auth/register", json={"phone": "13800000002", "password": "right"})
    resp = await client.post("/auth/login", json={"phone": "13800000002", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_and_update_profile(client):
    """认证后获取和更新个人信息。"""
    resp = await client.post("/auth/register", json={"phone": "13800000003", "password": "test"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # GET /users/me
    resp = await client.get("/users/me", headers=headers)
    assert resp.status_code == 200
    profile = resp.json()
    assert profile["phone"] == "13800000003"

    # PATCH /users/me
    resp = await client.patch("/users/me", headers=headers, json={"nickname": "球友", "self_rated_ntrp": 3.0})
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "球友"
    assert resp.json()["self_rated_ntrp"] == 3.0


@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """无 token 访问受保护端点返回 401。"""
    resp = await client.get("/users/me")
    assert resp.status_code == 401 or resp.status_code == 403


@pytest.mark.asyncio
async def test_submit_oppo_workout(client):
    """提交 OPPO 运动数据并验证返回。"""
    resp = await client.post("/auth/register", json={"phone": "13800000004", "password": "test"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/health/workouts", headers=headers, json={"raw_data": {
        "workout_type": "tennis",
        "start_time": 1718500000000,
        "end_time": 1718503600000,
        "duration_seconds": 3600,
        "total_shots": 300,
        "serve_count": 60,
        "forehand_topspin": 120,
        "forehand_slice": 30,
        "backhand_topspin": 60,
        "backhand_slice": 30,
        "avg_swing_speed": 45.5,
        "avg_heart_rate": 135,
        "max_heart_rate": 172,
        "total_distance": 1500,
        "total_calories": 480,
    }})
    assert resp.status_code == 200
    data = resp.json()
    assert "workout_id" in data
    assert "fitness_preview" in data
    assert "cardiovascular_endurance" in data["fitness_preview"]


@pytest.mark.asyncio
async def test_list_workouts(client):
    """获取运动记录列表。"""
    resp = await client.post("/auth/register", json={"phone": "13800000005", "password": "test"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 先提交一条
    await client.post("/health/workouts", headers=headers, json={"raw_data": {
        "workout_type": "tennis", "duration_seconds": 1800,
        "total_shots": 150, "avg_heart_rate": 130,
    }})

    resp = await client.get("/health/workouts", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
