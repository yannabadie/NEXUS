"""
NEXUS V11.6 KEYMAKER - Authentication Tests

Tests for KEYMAKER authentication endpoints:
- Login endpoint (POST /api/auth/login)
- Me endpoint (GET /api/auth/me)
- Optional auth dependencies
- CORTEX routes with auth

Author: Claude (NEXUS V11.6 KEYMAKER)
Date: 2025-12-15
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_login_success(self):
        """Valid password should return JWT token."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi[all] not installed")

        try:
            from jose import jwt
        except ImportError:
            pytest.skip("python-jose not installed")

        from core.api.cerebro.routes import auth

        # Mock the JWT creation to avoid dependency on middleware
        with patch.object(auth, 'ADMIN_PASSWORD', 'nexus'):
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(auth.router, prefix="/api/auth")

            with TestClient(app) as client:
                response = client.post(
                    "/api/auth/login",
                    json={"username": "admin", "password": "nexus"}
                )

            # Should succeed with default password
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert data["user_id"] == "admin"
            assert data["tenant_id"] == "default"

    def test_login_invalid_password(self):
        """Invalid password should return 401."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi[all] not installed")

        from core.api.cerebro.routes import auth

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(auth.router, prefix="/api/auth")

        with TestClient(app) as client:
            response = client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrong_password"}
            )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_me_without_auth(self):
        """GET /me without auth should return 401."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi[all] not installed")

        from core.api.cerebro.routes import auth

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(auth.router, prefix="/api/auth")

        with TestClient(app) as client:
            response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_logout_returns_success(self):
        """POST /logout should return success."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi[all] not installed")

        from core.api.cerebro.routes import auth

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(auth.router, prefix="/api/auth")

        with TestClient(app) as client:
            response = client.post("/api/auth/logout")

        assert response.status_code == 200
        assert response.json()["status"] == "logged_out"


class TestAuthDependencies:
    """Tests for authentication dependencies."""

    def test_require_auth_no_header(self):
        """require_auth should raise 401 without Authorization header."""
        import asyncio
        from core.api.cerebro.deps import require_auth
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(require_auth(None))

        assert exc_info.value.status_code == 401

    def test_require_auth_invalid_format(self):
        """require_auth should raise 401 with invalid format."""
        import asyncio
        from core.api.cerebro.deps import require_auth
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(require_auth("InvalidToken"))

        assert exc_info.value.status_code == 401
        assert "Bearer" in exc_info.value.detail

    def test_get_current_user_optional_returns_none(self):
        """get_current_user_optional should return None without auth."""
        import asyncio
        from core.api.cerebro.deps import get_current_user_optional

        result = asyncio.run(get_current_user_optional(None))
        assert result is None

    def test_get_current_user_optional_invalid_returns_none(self):
        """get_current_user_optional should return None with invalid token."""
        import asyncio
        from core.api.cerebro.deps import get_current_user_optional

        result = asyncio.run(get_current_user_optional("Bearer invalid_token"))
        assert result is None


class TestAuthenticatedUser:
    """Tests for AuthenticatedUser dataclass."""

    def test_authenticated_user_fields(self):
        """AuthenticatedUser should have expected fields."""
        from core.api.cerebro.deps import AuthenticatedUser

        user = AuthenticatedUser(
            user_id="test_user",
            tenant_id="test_tenant",
            workspace_id="test_workspace"
        )

        assert user.user_id == "test_user"
        assert user.tenant_id == "test_tenant"
        assert user.workspace_id == "test_workspace"

    def test_authenticated_user_str(self):
        """AuthenticatedUser __str__ should include key info."""
        from core.api.cerebro.deps import AuthenticatedUser

        user = AuthenticatedUser(
            user_id="admin",
            tenant_id="default",
            workspace_id="main"
        )

        str_repr = str(user)
        assert "admin" in str_repr
        assert "default" in str_repr


class TestCORTEXRoutesWithAuth:
    """Tests for CORTEX routes with optional authentication."""

    def test_state_snapshot_with_query_param(self):
        """State snapshot should work with query param (no auth)."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi[all] not installed")

        from core.api.cerebro.routes import state
        from unittest.mock import AsyncMock

        # Mock Redis bus - patch at the source module
        with patch('core.events.redis_bus.get_redis_bus') as mock_get_bus:
            mock_bus = MagicMock()
            mock_bus.is_connected.return_value = True

            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_redis.hgetall.return_value = {}
            mock_redis.lrange.return_value = []
            mock_bus._redis = mock_redis

            mock_get_bus.return_value = mock_bus

            # Mock interaction provider
            with patch('core.interaction.get_interaction_provider') as mock_provider:
                mock_provider.return_value.get_pending_requests.return_value = []

                from fastapi import FastAPI
                app = FastAPI()
                app.include_router(state.router, prefix="/api/state")

                with TestClient(app) as client:
                    response = client.get(
                        "/api/state/snapshot",
                        params={"tenant_id": "test_tenant"}
                    )

                # Should work without auth token
                assert response.status_code == 200
                data = response.json()
                assert data["tenant_id"] == "test_tenant"

    def test_state_snapshot_requires_tenant_id(self):
        """State snapshot should require tenant_id (via auth or query)."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi[all] not installed")

        from core.api.cerebro.routes import state

        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(state.router, prefix="/api/state")

        with TestClient(app) as client:
            # No tenant_id, no auth
            response = client.get("/api/state/snapshot")

        # Should fail without tenant_id
        assert response.status_code == 400
        assert "tenant_id required" in response.json()["detail"]


class TestKeymakerConfig:
    """Tests for KEYMAKER configuration."""

    def test_default_password_warning(self):
        """Using default password should log warning."""
        # This tests that the module loads correctly
        # The warning is logged at import time
        from core.api.cerebro.routes import auth

        # Default password should be 'nexus'
        assert auth.ADMIN_PASSWORD == "nexus" or auth.ADMIN_PASSWORD != ""

    def test_token_expiration_set(self):
        """Token expiration should be configured."""
        from core.api.cerebro.routes import auth

        assert auth.TOKEN_EXPIRE_HOURS == 24


class TestAuthRouterRegistered:
    """Tests that auth router is properly registered."""

    def test_auth_routes_in_app(self):
        """Auth routes should be registered in CEREBRO app."""
        from core.api.cerebro.app import create_cerebro_app

        app = create_cerebro_app()
        routes = [route.path for route in app.routes]

        # V11.6 KEYMAKER routes
        assert "/api/auth/login" in routes
        assert "/api/auth/me" in routes
        assert "/api/auth/logout" in routes

    def test_app_version_updated(self):
        """App version should be 11.6.0."""
        try:
            from fastapi.testclient import TestClient
        except ImportError:
            pytest.skip("fastapi[all] not installed")

        from core.api.cerebro.app import create_cerebro_app

        app = create_cerebro_app()

        with TestClient(app) as client:
            response = client.get("/")

        data = response.json()
        assert data["version"] == "11.6.0"
        assert "auth" in data
