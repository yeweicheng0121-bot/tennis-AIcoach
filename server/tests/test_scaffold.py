import pytest


def test_settings_load():
    """配置对象可正常加载。"""
    from server.config import settings
    assert settings.app_title == "Tennis AI Coach"
    assert settings.database_url is not None
    assert settings.redis_url is not None


def test_app_creates():
    """FastAPI app 可创建，health endpoint 返回 ok。"""
    from server.main import app
    assert app.title == "Tennis AI Coach"
    assert app.version == "0.1.0"


@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /health 返回 200 OK。"""
    from httpx import AsyncClient, ASGITransport
    from server.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
