# MCP SSE Server - Reference Implementation

A minimal MCP (Model Context Protocol) server implementation using Server-Sent Events (SSE) transport. Unlike many MCP servers examples that use stdio transport, this is a remote SSE server that can be deployed via Docker to any hosting platform. This serves as a clean, easy-to-understand reference for building deployable MCP servers.

> **Note:** This implementation prioritizes clarity and ease of understanding over production-ready features. It does not include comprehensive production aspects such as robust error handling, monitoring, security hardening, rate limiting, or scalability considerations that would be required for enterprise deployments.

## Features

- **SSE Transport**: Server-Sent Events for remote MCP server deployment
- **Docker Ready**: Containerized for easy deployment to any cloud platform
- **MCP Integration**
- **Clean Architecture**: Minimal dependencies and clear separation of concerns
- **Configurable Logging**: Console logging with optional log level override
- **Environment-based Configuration**: Uses `.env` files for setup

## Quick Start

### 1. Environment Setup

Copy `.env.example` to `.env` and update with your configuration:

```bash
cp .env.example .env
```

Then edit `.env` with your values:

```env
# Required
MCP_SERVER_AUTH_KEY=your-mcp-auth-key

# Optional
LOG_LEVEL=INFO
ENVIRONMENT=development

# Docker/Deployment Specific (optional)
FILE_LOGGING=true
```

### 2. Installation

First, install uv (see [Astral's installation guide](https://github.com/astral-sh/uv#installation)):

```bash
# Create virtual environment and install dependencies
uv venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

uv sync  # Install dependencies into virtual environment
```

### 3. Run the Server

```bash
uv run python mcp_server.py
```

## Deployment

### Docker Deployment

```bash
# Build and run
docker build -f deployment/Dockerfile -t mcp-sse-server .
docker run -d --name mcp-sse-server -p 8080:8080 --env-file .env mcp-sse-server
```

### Azure Container Apps Deployment

#### Quick Deploy
```bash
cd deployment/bicep
chmod +x deploy.sh
./deploy.sh
```

#### Custom Deployment Options

The deployment script now reads `BASE_NAME` and `REGION_CODE` from your `.env` file by default. For one-off deployments, you can override these:

```bash
# Use custom names from environment variables
export BASE_NAME=myclient-mcp REGION_CODE=eastus
./deploy.sh

# Or override via command line (takes precedence over .env)
./deploy.sh --base-name myclient-mcp --environment prod --region-code eastus

# Update code only (no infrastructure changes)
./deploy.sh --update
```

#### Azure Resources Created

The deployment creates these Azure resources following [standard naming conventions](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/azure-best-practices/resource-abbreviations):

| Resource | Name Pattern | Example |
|----------|--------------|---------|
| Resource Group | rg-{service}-{env}-{region} | rg-mcp-sse-dev-weu |
| Container App | ca-{service}-{env}-{region} | ca-mcp-sse-dev-weu |
| Container App Environment | cae-{service}-{env}-{region} | cae-mcp-sse-dev-weu |
| Log Analytics Workspace | log-{service}-{env}-{region} | log-mcp-sse-dev-weu |
| Container Registry | cr{service}{env}{region} | crmcpssedevweu |

**Configuration:**
- CPU: 0.5 vCPU, Memory: 1GB
- Fixed scaling: 1 replica (min=1, max=1)
- HTTPS ingress enabled

#### Prerequisites
- Azure CLI installed and configured
- Docker installed and running
- `.env` file with required variables

### Live Deployment

The service is currently deployed at:
- **URL**: https://ca-mcp-sse-development-weu.mangosea-a4cea9ef.westeurope.azurecontainerapps.io
- **Environment**: Development (West Europe)
- **Resource Group**: rg-mcp-sse-dev-weu

#### Azure Management

**Portal Access:**
1. Navigate to [Azure Portal](https://portal.azure.com)
2. Search for resource group: `rg-mcp-sse-dev-weu`
3. Find container app: `ca-mcp-sse-development-weu`

**CLI Commands:**
```bash
# Get container app details
az containerapp show --name ca-mcp-sse-development-weu --resource-group rg-mcp-sse-dev-weu

# View logs
az containerapp logs show --name ca-mcp-sse-development-weu --resource-group rg-mcp-sse-dev-weu

# Restart app
az containerapp restart --name ca-mcp-sse-development-weu --resource-group rg-mcp-sse-dev-weu
```

### Troubleshooting

**Common Issues:**
1. **Missing Environment Variables**: Ensure `.env` file exists with all required variables
2. **Azure CLI Issues**: Verify login with `az account show`
3. **Container Failures**: Check Docker daemon is running
4. **Runtime Issues**: Review container logs in Azure Log Analytics

**Health Check:**
```bash
curl https://your-container-app-url.azurecontainerapps.io/health
```

## Local Development with ngrok

For local development with web clients, you can use ngrok to expose your local server:

1. Install ngrok: https://ngrok.com/download
2. Start your local MCP server:
   ```bash
   uv run python mcp_server.py
   ```
3. In another terminal, expose the server:
   ```bash
   ngrok http 8080
   ```
4. Use the provided HTTPS URL (e.g., `https://abc123.ngrok.io`) in your web client
5. Remember to include your `X-API-Key` header when making requests

## Testing with AI Buddy

You can test your MCP SSE server in AI Buddy using ngrok to create a secure tunnel:

1. **Start your local server:**
   ```bash
   uv run python mcp_server.py
   ```

2. **Create an ngrok tunnel:**
   ```bash
   ngrok http 8080
   ```

3. **Configure AI Buddy MCP connector:**
   - Open AI Buddy and create a new MCP connector
   - Set the server URL to your ngrok public URL with `/sse` endpoint
   - Example: `https://abc123.ngrok.io/sse`
   - Set the `X-API-Key` header value to match your `MCP_SERVER_AUTH_KEY` from `.env`

4. **Test the connection:**
    - AI Buddy should now be able to connect to your local MCP server
    - Ask the expert to reveal what tool calls it has access to
    - You should see a request come through ngrok and the app server (in console )output
    - The expert should include in its list of tools the available actions


## Project Structure

```
mcp-sse-server/
├── mcp_server.py           # Main entry point and core application logic
├── src/                    # Main source code
│   ├── __init__.py         # Package marker
│   ├── config.py           # Configuration management
│   ├── mcp_tools.py        # MCP server and tools registration
│   ├── utils/              # Utility modules
│   │   ├── __init__.py     # Package marker
│   │   └── __init__.py     # Package marker
│   └── actions/            # MCP action implementations
│       ├── __init__.py     # Package marker
│       └── status.py       # Example action with no dependencies
├── tests/                  # Test files
│   ├── test_config.py      # Configuration tests
│   ├── test_email_utils.py # Email utility tests
│   ├── test_mcp_tools.py   # MCP tools tests
│   └── test_*.py           # Other test files
├── deployment/             # Deployment files
│   ├── Dockerfile          # Container configuration
│   └── bicep/              # Azure Bicep templates and scripts
│       ├── deploy.sh       # Automated deployment script
│       └── main.bicep      # Azure resource definitions
├── logs/                   # Runtime logs (created automatically)
├── pyproject.toml          # Dependencies and project config
└── README.md              # This file
```

## Configuration

### Environment Variables

**Required:**
- `MCP_SERVER_AUTH_KEY`: Authentication key for MCP requests

**Optional:**
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (default: development)
- `FILE_LOGGING`: Enable file logging (used in Docker containers)

## Development

### Actions System - Adding New MCP Tools

The server uses a transparent actions-based architecture where each MCP tool is implemented as a separate action module. Dependencies are explicitly declared in function signatures, making the system easy to understand and extend.

#### Directory Structure

```
src/actions/
├── __init__.py          # Package marker
└── status.py            # Server status functionality (no dependencies)
```

#### How It Works

The system uses a **dependency registry** approach:

1. **Central Registry**: All server dependencies are declared in `src/mcp_tools.py`:
   ```python
   DEPENDENCIES: dict[str, object] = {
       "postmark_api_key": api_key,
       "sender_email": from_email,
       # Add new dependencies here ↓
       # "weather_api_key": os.getenv("WEATHER_API_KEY"),
   }
   ```

2. **Signature-Based Injection**: Only dependencies that appear in the function signature are injected - no hidden behavior.

#### Adding a New Action (< 60 seconds)

**Step 1: Write the Action**

Create `src/actions/my_feature.py`:

```python
"""
My feature action implementation.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def my_feature_action(
    user_param1: str,
    user_param2: int,
    postmark_api_key: str,    # Only injected if you need it
    sender_email: str,        # Only injected if you need it
) -> Any:
    """
    Description of what this action does.
    
    Args:
        user_param1: User-provided parameter
        user_param2: Another user-provided parameter
        postmark_api_key: Postmark API key (injected)
        sender_email: Sender email (injected)
        
    Returns:
        Result of the action
    """
    logger.info("My feature action called")
    
    # Your implementation here
    result = f"Processed {user_param1} with value {user_param2}"
    
    logger.info("My feature action completed")
    return result
```

**Step 2: Add New Dependencies (if needed)**

If your action needs additional services (like a weather API key), add them to the `DEPENDENCIES` registry in `src/mcp_tools.py`:

```python
DEPENDENCIES: dict[str, object] = {
    "postmark_api_key": api_key,
    "sender_email": from_email,
    "weather_api_key": os.getenv("WEATHER_API_KEY"),  # ← Add this
}
```

**Step 3: Restart the Server**

That's it! The action is automatically registered as `my_feature_tool`.

#### Action Examples

**Simple Action (No Dependencies):**
```python
async def status_action() -> dict:
    """Get server status - needs no external dependencies."""
    return {"status": "ok", "version": "1.0.0"}
```

**Action with User Parameters Only:**
```python
async def greet_user_action(name: str, greeting: str = "Hello") -> str:
    """Greet a user - no server dependencies needed."""
    return f"{greeting}, {name}!"
```

**Action Using Server Dependencies:**
```python
async def some_action(
    message: str,
    some_api_key: str,  # Injected because it's in DEPENDENCIES
) -> str:
    return f"Processed '{message}'"
```

**Action with Custom Dependencies:**
```python
async def fetch_weather_action(
    city: str,
    weather_api_key: str,   # Must be added to DEPENDENCIES first
) -> dict:
    """Fetch weather data using external API."""
    # Use weather_api_key to call external service
    return {"city": city, "temperature": "22°C"}
```

#### Function Requirements

**Naming Convention:**
- Function name must end with `_action` (e.g., `status_action`)
- The registered MCP tool will be named by replacing `_action` with `_tool`

**Parameters:**
- **User parameters**: Exposed to MCP clients, must be documented
- **Dependency parameters**: Must match names in the `DEPENDENCIES` registry
- **Type hints**: Required for all parameters
- **No `**kwargs`**: Dependencies are passed as explicit named parameters

**Return Value:**
- Can return any serializable type (str, dict, list, etc.)
- Return value will be sent back to the MCP client

**Async Function:**
- Must be an `async` function using `async def`
- Can use `await` for I/O operations

#### Auto-Discovery Process

When the server starts:

1. The `register_tools()` function populates the `DEPENDENCIES` registry (if needed for your actions)
2. It scans the `src/actions/` package for Python modules
3. It looks for async functions ending with `_action`
4. For each action, it inspects the function signature
5. It creates a wrapper that injects only the dependencies the action requests
6. It registers the wrapper as an MCP tool

### Testing

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Test action registration specifically
uv run python -m pytest tests/test_mcp_tools.py::TestRegisterTools -v

# Test individual actions
```

## Dependencies

- **httpx**: HTTP client
- **mcp[cli]**: Model Context Protocol implementation
- **starlette**: ASGI framework for the web server
- **uvicorn**: ASGI server
- **python-dotenv**: Environment variable loading
- **pydantic-settings**: Configuration management

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).