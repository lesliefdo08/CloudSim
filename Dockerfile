# CloudSim Dockerfile - Run CloudSim in a Docker container
# Requires Docker socket access for managing compute containers

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY desktop-app/ /app/desktop-app/

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/desktop-app/requirements.txt

# Set environment variables
ENV DISPLAY=:0
ENV QT_QPA_PLATFORM=offscreen
ENV PYTHONUNBUFFERED=1

# Expose any ports if needed (currently not used)
# EXPOSE 8080

# Set working directory to desktop-app
WORKDIR /app/desktop-app

# Run CloudSim
CMD ["python", "main.py"]

# Usage Instructions:
# 
# Build:
#   docker build -t cloudsim:v1.0 .
#
# Run (with Docker socket access):
#   docker run -it --rm \
#     -v /var/run/docker.sock:/var/run/docker.sock \
#     -e DISPLAY=$DISPLAY \
#     cloudsim:v1.0
#
# Note: Docker socket access (-v /var/run/docker.sock) is REQUIRED
# for CloudSim to manage compute instance containers
