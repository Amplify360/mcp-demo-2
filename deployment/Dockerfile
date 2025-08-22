FROM python:3.11-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install UV package manager and dependencies
RUN pip install --upgrade pip && \
    pip install uv && \
    uv pip install --system -e . 

# Copy application code
COPY . .

# Create log directory
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FILE_LOGGING=true \
    LOG_LEVEL=INFO

# Expose the port the app runs on
EXPOSE 8080

# Run the application
CMD ["python", "mcp_server.py", "--host", "0.0.0.0", "--port", "8080"] 