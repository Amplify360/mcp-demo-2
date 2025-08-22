# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a minimal MCP (Model Context Protocol) server implementation using Server-Sent Events (SSE) transport. It serves as a reference implementation for building deployable MCP servers that can be hosted remotely via Docker on any cloud platform.

## Development Commands

### Setup and Installation
```bash
# Install uv first (see https://github.com/astral-sh/uv#installation)
# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On macOS/Linux
uv sync
```

### Running the Server
```bash
# Run the MCP server locally
uv run python mcp_server.py

# Run with custom host/port
uv run python mcp_server.py --host 0.0.0.0 --port 8080 --log-level DEBUG
```

### Testing
```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test files
uv run python -m pytest tests/test_mcp_tools.py -v

# Test action registration specifically
uv run python -m pytest tests/test_mcp_tools.py::TestRegisterTools -v
```

### Docker Commands
```bash
# Build Docker image
docker build -f deployment/Dockerfile -t mcp-sse-server .

# Run Docker container
docker run -d --name mcp-sse-server -p 8080:8080 --env-file .env mcp-sse-server
```

### Azure Deployment
```bash
# Deploy to Azure Container Apps
cd deployment/bicep
chmod +x deploy.sh
./deploy.sh

# Update code only (no infrastructure changes)
./deploy.sh --update
```

## Architecture

### Core Components

1. **MCP Server** (`mcp_server.py`): Entry point that initializes logging, loads configuration, and starts the Uvicorn ASGI server with the MCP SSE transport.

2. **MCP Tools Registration** (`src/mcp_tools.py`): 
   - Implements `MCPServer` class that wraps FastMCP with SSE transport
   - Auto-discovers action modules from `src/actions/` directory
   - Creates tool wrappers with dependency injection based on function signatures
   - Handles API key authentication middleware

3. **Actions System** (`src/actions/`):
   - Each MCP tool is implemented as an async function ending with `_action`
   - Dependencies are injected based on function signatures from the `DEPENDENCIES` registry
   - Actions are automatically registered as MCP tools with names ending in `_tool`

### Adding New MCP Tools

To add a new MCP tool:

1. Create a new file in `src/actions/` (e.g., `my_feature.py`)
2. Define an async function ending with `_action`:
   ```python
   async def my_feature_action(
       user_param: str,  # User-provided parameters
       some_dependency: str,  # Will be injected if in DEPENDENCIES
   ) -> Any:
       """Tool description."""
       # Implementation
       return result
   ```

3. If the tool needs new dependencies, add them to `DEPENDENCIES` in `src/mcp_tools.py`:
   ```python
   DEPENDENCIES: dict[str, object] = {
       # existing dependencies...
       "some_dependency": os.getenv("SOME_API_KEY"),
   }
   ```

4. The tool is automatically registered on server restart

### Key Design Decisions

- **SSE Transport**: Uses Server-Sent Events instead of stdio for remote deployment capability
- **Dependency Injection**: Explicit dependency declaration in function signatures for transparency
- **Auto-Discovery**: Actions are automatically discovered and registered from the `src/actions/` package
- **API Key Authentication**: All endpoints except `/health` require `X-API-Key` header matching `MCP_SERVER_AUTH_KEY`

## Environment Configuration

Required environment variables (in `.env` file):
- `MCP_SERVER_AUTH_KEY`: Authentication key for MCP requests

Optional:
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (default: development)
- `FILE_LOGGING`: Enable file logging (used in Docker containers)