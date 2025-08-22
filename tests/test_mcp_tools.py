"""
Unit tests for mcp_tools.py
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient

from src.mcp_tools import APIKeyMiddleware, MCPServer, register_tools


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


class TestMCPServer:
    """Test the MCPServer class."""

    def test_mcp_server_initialization(self):
        """Test MCPServer initializes correctly."""
        api_key = "test_api_key"
        service_name = "test-service"

        server = MCPServer(api_key=api_key, service_name=service_name)

        assert server.api_key == api_key
        assert server.mcp is not None

    def test_create_app_returns_starlette_app(self):
        """Test create_app returns a Starlette application."""
        server = MCPServer(api_key="test_key")

        app = server.create_app(debug=True)

        assert isinstance(app, Starlette)
        assert app.debug is True

    def test_create_app_has_routes(self):
        """Test created app has routes."""
        server = MCPServer(api_key="test_key")
        app = server.create_app()

        # Just verify that routes exist - the exact structure doesn't matter for this test
        assert len(app.routes) > 0


class TestRegisterTools:
    """Test the register_tools function."""

    @patch("src.mcp_tools.pkgutil.iter_modules")
    @patch("src.mcp_tools.importlib.import_module")
    def test_register_tools_discovers_status_action(self, mock_import, mock_iter):
        """Test register_tools discovers and registers status_action."""
        # Mock the module discovery
        mock_iter.return_value = [("", "status", "")]

        # Create a mock action function
        mock_status_action = AsyncMock()
        mock_status_action.__name__ = "status_action"
        mock_status_action.__doc__ = "Status action"
        mock_status_action.__annotations__ = {}

        # Mock the status module
        mock_status_module = MagicMock()
        setattr(mock_status_module, "status_action", mock_status_action)

        # Mock inspect.getmembers to return our action function
        with patch("src.mcp_tools.inspect.getmembers") as mock_getmembers:
            mock_getmembers.return_value = [
                ("status_action", mock_status_action)
            ]
            mock_import.return_value = mock_status_module

            # Create a mock MCP server
            mock_mcp_server = MagicMock()

            # Call register_tools
            register_tools(
                mcp_server=mock_mcp_server,
            )

            # Verify register_tool was called once for status action
            assert mock_mcp_server.register_tool.call_count == 1

    @patch("src.mcp_tools.pkgutil.iter_modules")
    @patch("src.mcp_tools.importlib.import_module")
    def test_register_tools_handles_module_load_failure(self, mock_import, mock_iter):
        """Test register_tools handles module loading failures gracefully."""
        # Mock the module discovery
        mock_iter.return_value = [("", "broken_module", "")]

        # Mock import_module to raise an exception
        mock_import.side_effect = ImportError("Module not found")

        mock_mcp_server = MagicMock()

        # Should raise the exception (not handle it silently)
        with pytest.raises(ImportError):
            register_tools(
                mcp_server=mock_mcp_server,
            )
