# Multi-stage build for MCP Python Analyzer Server
# Use a Python image with uv pre-installed for efficient dependency management
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Enable bytecode compilation for better performance
ENV UV_COMPILE_BYTECODE=1

# Copy from cache instead of linking for containerized environments
ENV UV_LINK_MODE=copy

# Install project dependencies using lockfile for reproducible builds
# Mount cache and bind source files for efficient Docker layer caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Add project source code and install the package
# Separating dependency installation from source installation optimizes Docker layers
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Production stage with minimal Python runtime
FROM python:3.12-slim-bookworm AS runtime

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r analyzer && useradd -r -g analyzer analyzer

# Copy built virtual environment from builder stage
COPY --from=builder --chown=analyzer:analyzer /app/.venv /app/.venv

# Ensure virtual environment binaries are in PATH
ENV PATH="/app/.venv/bin:$PATH"

# Set Python optimization flags
ENV PYTHONOPTIMIZE=1
ENV PYTHONUNBUFFERED=1

# Health check to ensure the MCP server is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import mcp_python_analyzer.server; print('MCP Python Analyzer Server is healthy')" || exit 1

# Switch to non-root user
USER analyzer

# Set the entrypoint to the MCP server analyzer
ENTRYPOINT ["mcp-server-analyzer"]
