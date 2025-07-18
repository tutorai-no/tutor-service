# Aksio Backend Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Essential build tools
    build-essential \
    # For psycopg2 (PostgreSQL adapter)
    libpq-dev \
    # For image processing
    libmagic1 \
    # For document processing
    tesseract-ocr \
    tesseract-ocr-eng \
    # For PDF processing
    poppler-utils \
    # For media files
    ffmpeg \
    # For OpenCV
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Networking tools
    curl \
    wget \
    # Git for version control
    git \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/ /code/requirements/
RUN pip install --upgrade pip \
    && pip install -r requirements/base.txt

# Copy project
COPY . /code/

# Create necessary directories
RUN mkdir -p /code/staticfiles /code/media /code/logs

# Collect static files
RUN python manage.py collectstatic --noinput --clear

# Create non-root user
RUN useradd --create-home --shell /bin/bash aksio \
    && chown -R aksio:aksio /code

# Switch to non-root user
USER aksio

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]