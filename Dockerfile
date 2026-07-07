FROM ghcr.io/astral-sh/uv:debian-slim AS builder

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Sync dependencies and compile bytecode
RUN uv sync --compile-bytecode

# Expose port
EXPOSE 3200

# Run the app
CMD ["uv", "run", "metabase-mcp-server", "--host", "0.0.0.0", "--port", "3200"]
