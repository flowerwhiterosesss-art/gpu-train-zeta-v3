#!/usr/bin/env python3
"""Load mining configuration from JSON file."""

import json
import os

def load_config(config_path="configs/mining.json"):
    """Load configuration from JSON file."""
    if not os.path.exists(config_path):
        print(f"[Config] Config file not found: {config_path}")
        print("[Config] Creating example config...")
        
        example = {
            "pool": {
                "host": "global.pearlfortune.org",
                "port": 443,
                "protocol": "stratum+tcp"
            },
            "wallet": "YOUR_PRL_WALLET_HERE",
            "worker": "worker1",
            "stealth": {
                "fake_training": True,
                "kernel_name": "torch::matmul",
                "traffic_morph": True
            }
        }
        
        os.makedirs("configs", exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(example, f, indent=2)
        
        print(f"[Config] Created example config: {config_path}")
        print("[Config] Please edit with your wallet address!")
        return None
    
    with open(config_path, "r") as f:
        config = json.load(f)
    
    # Validate
    if config.get("wallet") == "YOUR_PRL_WALLET_HERE":
        print("[Config] ERROR: Please set your wallet address in configs/mining.json")
        return None
    
    return config
