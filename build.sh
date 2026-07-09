#!/bin/bash
# ============================================================
# Pearl Miner v3.0 — Build Script
# Compiles CUDA kernel and sets up environment
# ============================================================

set -e

echo "=============================="
echo "  Pearl Miner v3.0 — Build"
echo "=============================="

# Check for CUDA
if ! command -v nvcc &> /dev/null; then
    echo "ERROR: nvcc not found!"
    echo "  Install CUDA toolkit: https://developer.nvidia.com/cuda-toolkit"
    exit 1
fi

echo "CUDA version: $(nvcc --version | grep release | awk '{print $6}')"

# Create build directory
mkdir -p build
cd build

# Compile CUDA kernel
echo ""
echo "Compiling CUDA kernel..."
nvcc -o training_ops.so \
    -Xcompiler -fPIC \
    --shared \
    ../src/cuda_ops.cu \
    -arch=sm_70 \
    -arch=sm_75 \
    -arch=sm_80 \
    -arch=sm_86 \
    -arch=sm_89 \
    -arch=sm_90 \
    -O3

if [ $? -eq 0 ]; then
    echo "✅ CUDA kernel compiled successfully"
else
    echo "❌ CUDA kernel compilation failed"
    exit 1
fi

# Copy Python files
echo ""
echo "Setting up Python environment..."
cp ../src/stratum_client.py .
cp ../src/miner.py .
cp ../src/train.py . 2>/dev/null || true

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124 2>/dev/null || \
pip install torch torchvision

echo ""
echo "=============================="
echo "  Build Complete!"
echo "=============================="
echo ""
echo "To run:"
echo "  cd build"
echo "  python miner.py"
echo ""
echo "Or with fake training:"
echo "  cd build"
echo "  python train.py &"
echo "  python miner.py"
echo ""
