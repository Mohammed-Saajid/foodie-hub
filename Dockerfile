# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11 AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /build

# Create a virtual environment in a standard location
RUN uv venv /opt/venv

# Activate the virtual environment for subsequent commands
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

# Install only locked production dependencies into the active virtual environment.
# `--active` ensures packages are installed into /opt/venv (copied to runtime image).
RUN uv sync --frozen --no-dev --no-install-project --active

# ==========================================
# Stage 2: Runner (Production Image)
# ==========================================
FROM python:3.11-slim AS runner

# Set environment variables, including activating the venv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --group appuser

# Copy the completely built virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY . /app/

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Since the venv is in the PATH, uvicorn can be called directly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "warning"]