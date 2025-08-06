# Stage 1: Builder with Python and dependencies
FROM python:3.11-slim AS builder

# System deps
RUN apt-get update && apt-get install -y build-essential curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install dependencies from pyproject.toml using pip
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .
RUN pip install --upgrade pip && pip install .

# Copy app source
COPY . .

# Stage 2: Runtime image
FROM python:3.11-slim

WORKDIR /app

# Install runtime deps only
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# Expose MCP server port (default)
EXPOSE 3200

# Start your MCP server
CMD ["python", "src/metabase_mcp_server.py"]
