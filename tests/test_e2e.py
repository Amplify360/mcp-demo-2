"""
End-to-end tests for the MCP server.
"""

from unittest.mock import MagicMock, patch

from starlette.testclient import TestClient

from src.mcp_tools import MCPServer, register_tools


class TestE2EIntegration:
    """End-to-end integration tests."""

    def test_sse_endpoint_requires_api_key(self):
        """Test SSE endpoint requires valid API key for authentication."""
        test_api_key = "test_sse_key"

        # Create MCP server and app
        server = MCPServer(api_key=test_api_key)
        app = server.create_app()

        client = TestClient(app)

        # Request without API key should be rejected
        response = client.get("/sse")
        assert response.status_code == 401
        assert response.json() == {"error": "Unauthorized"}

        # Request with wrong API key should be rejected
        response = client.get("/sse", headers={"X-API-Key": "wrong_key"})
        assert response.status_code == 401
        assert response.json() == {"error": "Unauthorized"}

    def test_sse_endpoint_accepts_valid_api_key(self):
        """Test SSE endpoint accepts requests with valid API key."""
        test_api_key = "test_sse_key"

        # Create MCP server and app
        server = MCPServer(api_key=test_api_key)
        app = server.create_app()

        client = TestClient(app)

        # Request with valid API key should be accepted (but may fail at SSE level)
        # We're just testing the middleware authentication, not the SSE implementation
        response = client.head("/sse", headers={"X-API-Key": test_api_key})

        # Should not be 401 Unauthorized (auth passed)
        # Might be 400, 500, or other error related to SSE, but not 401
        assert response.status_code != 401

    def test_messages_endpoint_requires_api_key(self):
        """Test messages endpoint requires valid API key."""
        test_api_key = "test_messages_key"

        # Create MCP server and app
        server = MCPServer(api_key=test_api_key)
        app = server.create_app()

        client = TestClient(app)

        # Request without API key should be rejected
        response = client.post("/messages/test")
        assert response.status_code == 401
        assert response.json() == {"error": "Unauthorized"}

