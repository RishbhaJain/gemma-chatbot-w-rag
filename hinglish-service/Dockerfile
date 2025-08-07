# Use Python 3.11 with CUDA support for TTS models
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    alsa-utils \
    libasound2-dev \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install additional audio dependencies
RUN pip install --no-cache-dir \
    PyAudio \
    simpleaudio \
    playsound

# Create necessary directories
RUN mkdir -p /app/temp /app/models /app/logs

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TEMP_DIR=/app/temp
ENV MODEL_DIR=/app/models
ENV LOG_LEVEL=INFO

# Create non-root user for security
RUN useradd -m -u 1000 hinglish && \
    chown -R hinglish:hinglish /app

# Switch to non-root user
USER hinglish

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 