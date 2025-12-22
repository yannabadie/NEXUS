# NEXUS Core - Python 3.13
FROM python:3.13-slim-bookworm

# Environment Variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    WORKSPACE_PATH=/app/workspace

# System Dependencies (git for gitpython, build-essential for compiling)
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python Dependencies
# Copy requirements from root context
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy Project Code
COPY . .

# Create Workspace Directory
RUN mkdir -p $WORKSPACE_PATH

# Expose API Port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start Start Script
# Runs API server by default, but can be overridden
CMD ["python", "interface/server/app.py"]
