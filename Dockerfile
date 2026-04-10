# ============================================
# Stage 1: Builder - install dependencies
# ============================================
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install packages
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ============================================
# Stage 2: Runtime - minimal production image
# ============================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Install runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy application code (layered for better cache)
COPY --chown=appuser:appgroup config.py .
COPY --chown=appuser:appgroup pipeline.py .
COPY --chown=appuser:appgroup fetch.yaml .

COPY --chown=appuser:appgroup fetch/ ./fetch/
COPY --chown=appuser:appgroup wash/ ./wash/
COPY --chown=appuser:appgroup vector/ ./vector/
COPY --chown=appuser:appgroup mcp_server/ ./mcp_server/

# Create runtime directories
RUN mkdir -p fetch/datas fetch/raw docs \
    && chown -R appuser:appgroup fetch/datas fetch/raw docs

# Expose MCP server port
EXPOSE 15277

# Environment defaults (can be overridden)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=15277

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${MCP_SERVER_PORT}/health || exit 1

# Switch to non-root user
USER appuser

# Default: run MCP server
CMD ["python", "-m", "mcp_server.server"]