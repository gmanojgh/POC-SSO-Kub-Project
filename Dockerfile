# ─── Stage 1: dependency builder ─────────────────────────────────────────────
# Separate stage so the final image does not carry pip cache or build tools.
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed to compile psycopg2 wheels (slim image lacks them)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─── Stage 2: runtime image ──────────────────────────────────────────────────
FROM python:3.11-slim

# Non-root user for security — never run application code as root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy compiled packages from builder stage
COPY --from=builder /install /usr/local

# System runtime dep only (no gcc needed here)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY --chown=appuser:appgroup . .

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Collect static files at build time
# The || true allows the build to succeed even if DB is unavailable
RUN python manage.py collectstatic --noinput || true

# Switch to non-root user before starting the process
USER appuser

EXPOSE 8000

# Use gunicorn in production for multi-worker serving.
# Django's runserver is single-threaded and not suitable for production.
# Workers = 2 * CPU cores + 1 is the standard formula; 3 is safe for a POC.
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
