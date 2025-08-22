"""
Unit tests for mcp_tools.py
"""

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient

from src.mcp_tools import APIKeyMiddleware


class TestAPIKeyMiddleware:
    """Test the API key authentication middleware."""

    def test_api_key_middleware_allows_valid_key(self):
        """Test middleware allows requests with valid API key."""
        test_api_key = "valid_test_key"

        async def dummy_endpoint(request):
            return Response("OK", status_code=200)

        app = Starlette(
            middleware=[Middleware(APIKeyMiddleware, api_key=test_api_key)],
            routes=[Route("/test", endpoint=dummy_endpoint, methods=["GET"])],
        )

        client = TestClient(app)

        # Request with valid API key should succeed
        response = client.get("/test", headers={"X-API-Key": test_api_key})
        assert response.status_code == 200
        assert response.text == "OK"

    def test_api_key_middleware_blocks_invalid_key(self):
        """Test middleware blocks requests with invalid or missing API key."""
        test_api_key = "valid_test_key"

        async def dummy_endpoint(request):
            return Response("OK", status_code=200)

        app = Starlette(
            middleware=[Middleware(APIKeyMiddleware, api_key=test_api_key)],
            routes=[Route("/test", endpoint=dummy_endpoint, methods=["GET"])],
        )

        client = TestClient(app)

        # Request without API key should be rejected
        response = client.get("/test")
        assert response.status_code == 401
        assert response.json() == {"error": "Unauthorized"}

        # Request with wrong API key should be rejected
        response = client.get("/test", headers={"X-API-Key": "wrong_key"})
        assert response.status_code == 401
        assert response.json() == {"error": "Unauthorized"}


