"""Task 5: JWT auth tests — write BEFORE implementation."""
import uuid

import pytest


def test_password_hash_and_verify():
    """密码哈希和验证正确工作。"""
    from server.auth import hash_password, verify_password
    pw = "test123"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    """JWT 签发和验证往返正确。"""
    from server.auth import create_access_token, decode_access_token
    uid = uuid.uuid4()
    token = create_access_token(uid)
    payload = decode_access_token(token)
    assert payload["sub"] == str(uid)
    assert "exp" in payload


def test_jwt_invalid_token():
    """无效 token 抛出异常。"""
    from server.auth import decode_access_token
    import jose
    with pytest.raises(jose.exceptions.JWTError):
        decode_access_token("not.a.valid.token")


def test_get_current_user_missing_token():
    """缺少 token 返回 401。"""
    import pytest
    pytest.skip("需要完整 FastAPI 依赖注入环境，在集成测试中覆盖")
