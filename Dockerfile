FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

LABEL org.opencontainers.image.source="https://github.com/flowerwhiterosesss-art/pearl-fortune-zeta"
LABEL org.opencontainers.image.description="Pearl Miner v3.0 - Custom CUDA Implementation"
LABEL org.opencontainers.image.version="3.0.0"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
RUN pip3 install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu124

WORKDIR /app

# Copy source files
COPY src/ /app/src/
COPY build.sh /app/
COPY configs/ /app/configs/

# Build CUDA kernel
RUN chmod +x build.sh && ./build.sh

# Environment variables
ENV POOL_HOST="global.pearlfortune.org"
ENV POOL_PORT="443"
ENV PEARL_WALLET=""
ENV PEARL_WORKER=""

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD pgrep -f "train.py" > /dev/null || exit 1

ENTRYPOINT ["python3", "src/train.py"]
