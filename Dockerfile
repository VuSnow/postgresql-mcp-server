FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and install package
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Expose default MCP port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import postgresql_mcp; print('ok')" || exit 1

# Run the MCP server
ENTRYPOINT ["fastmcp", "run", "src/postgresql_mcp/app.py:mcp"]
