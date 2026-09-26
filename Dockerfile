# =============================================================================
# ResearchPilot — Production Containerfile (Phase 14)
# =============================================================================
# A secure, lightweight Python 3.12 container running FastAPI and Uvicorn.
# =============================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install curl for container health checks
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Step 1: Install Python dependencies (cached in Docker layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 2: Copy application code
COPY app /app/app

# Step 3: Create storage directory for SQLite persistence with permissions
RUN mkdir -p /app/data && \
    useradd -u 1001 -m appuser && \
    chown -R appuser:appuser /app

# Step 4: Run as non-privileged user for security
USER appuser

# Expose API server port
EXPOSE 8000

# Step 5: Container healthcheck against /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Step 6: Start Uvicorn ASGI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
