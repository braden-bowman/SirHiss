# Multi-stage build for optimized backend
FROM python:3.11-slim AS base
WORKDIR /app

# Install system dependencies in separate layer for better caching
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip and install wheel for faster package installation
RUN pip install --upgrade pip wheel setuptools

# Dependencies stage
FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Development stage
FROM base AS development
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy the application
COPY . .

# Create directories for bot storage
RUN mkdir -p bot_storage

# Expose port
EXPOSE 8000

# Run the application in development mode with auto-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base AS production
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN mkdir -p bot_storage && chown appuser:appuser bot_storage

# Copy the application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run the application in production mode
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]