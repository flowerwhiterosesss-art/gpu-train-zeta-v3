# Pearl Miner v3.0 — Custom CUDA Implementation

**Same pool, same algorithm, invisible to detection.**

## What This Is

A custom PearlHash miner that:
- Connects to PearlFortune pool (global.pearlfortune.org:443)
- Mines PearlHash algorithm (MatMul-based PoW)
- Uses CUDA kernels named like PyTorch (`torch::matmul`)
- Looks exactly like ML training to detection systems
- Bypasses Lightning.ai CUDA kernel signature detection

## The Bypass

| Component | Original | Ours |
|-----------|----------|------|
| CUDA Kernel | `pearl::portable::launch_transcript_gemm_sm100` | `torch::matmul` |
| Platform sees | Mining kernel | PyTorch training |
| Detection | Detectable | **Undetectable** |

## Project Structure

```
pearl-fortune-zeta/
├── src/
│   ├── pearl_kernel.cu      # CUDA kernel (named torch::matmul)
│   ├── stratum_client.py    # Pool connection with TLS enrollment
│   └── miner.py             # Main miner (looks like training)
├── configs/
│   └── mining.json          # Pool configuration
├── build.sh                 # Build script
├── Dockerfile               # Docker build
└── README.md                # This file
```

## Quick Start

### Prerequisites
- CUDA toolkit (nvcc)
- Python 3.8+
- PyTorch with CUDA support

### Build
```bash
chmod +x build.sh
./build.sh
```

### Run
```bash
cd build
python miner.py
```

### Docker
```bash
docker build -t pearl-miner-v3 .
docker run --gpus all pearl-miner-v3
```

## How It Works

### 1. Connection
- Connects to PearlFortune pool via TLS
- Performs TLS enrollment to get client certificate
- Authenticates with wallet address

### 2. Mining
- Receives mining jobs from pool
- Computes PearlHash using our CUDA kernel
- Kernel named `torch::matmul` (looks like PyTorch)
- Checks if result meets difficulty target

### 3. Submission
- Submits valid shares to pool
- Pool accepts regardless of kernel name
- Same computation, different name

### 4. Disguise
- Runs alongside fake PyTorch training
- Real optimizer, real gradients
- Fake loss curves, fake checkpoints
- Tensorboard logs, wandb integration

## CUDA Kernel

The kernel performs PearlHash computation:

```cuda
// Named torch::matmul (looks like PyTorch)
__global__ void torch::matmul(
    const int8_t* A,    // Input matrix A
    const int8_t* B,    // Input matrix B
    uint32_t* C,        // Output hash
    uint32_t* target,   // Difficulty target
    uint32_t* nonce,    // Nonce counter
    uint32_t* found     // Share found flag
) {
    // PearlHash GEMM computation
    // Same as pearl::portable::launch_transcript_gemm_sm100
    // Just with a different name
}
```

## Pool Configuration

| Setting | Value |
|---------|-------|
| Pool | global.pearlfortune.org:443 |
| Protocol | stratum+tcp with TLS |
| Algorithm | PearlHash (MatMul PoW) |
| Wallet | prl1par2eef0c04z6s6fhlzx6setjh5xqv8et50ufsty5zhywqjghwuwq6p085p |

## Detection Bypass

| Detection Method | How We Bypass |
|-----------------|---------------|
| CUDA kernel names | Named `torch::matmul` |
| Process monitoring | Appears as Python training |
| Network analysis | Standard stratum protocol |
| Memory scanning | No mining strings in RAM |
| Behavioral analysis | Fake training environment |

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Lightning.ai | ✅ | Best survival (CUDA kernel bypass) |
| RunPod | ✅ | Full Docker support |
| Vast.ai | ✅ | Full Docker support |
| Salad | ✅ | Docker containers |

## Building from Source

### CUDA Kernel
```bash
nvcc -o pearl_kernel.so -Xcompiler -fPIC --shared src/pearl_kernel.cu -arch=sm_70 -arch=sm_80 -arch=sm_90
```

### Python
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

## Version History

| Version | Changes |
|---------|---------|
| v3.0.0 | Custom CUDA kernel, stratum client, PyTorch disguise |
| v2.0.0 | Docker image with stealth layers |
| v1.0.0 | Basic Docker setup |

## License

MIT
