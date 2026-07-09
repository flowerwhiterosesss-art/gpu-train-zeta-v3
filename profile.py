#!/usr/bin/env python3
"""
Pearl Miner Capture — Simple version (no tcpdump needed)
Just runs the miner and captures all output.
"""

import subprocess
import time
import os
import glob

def main():
    print("="*60)
    print("  Pearl Miner Capture — Simple")
    print("="*60)
    print()
    
    # Find the miner binary
    miner_paths = [
        "/workspace/pearl-analysis/pearlfortune/miner-cuda12",
        "/workspace/pearlfortune/miner-cuda12",
        os.path.expanduser("~/pearl-analysis/pearlfortune/miner-cuda12"),
    ]
    
    # Also search for it
    for root, dirs, files in os.walk("/workspace"):
        for f in files:
            if f == "miner-cuda12":
                miner_paths.insert(0, os.path.join(root, f))
    
    miner_binary = None
    for path in miner_paths:
        if os.path.exists(path):
            miner_binary = path
            break
    
    if not miner_binary:
        print("Miner not found! Let me download it...")
        subprocess.run(["mkdir", "-p", "/workspace/pearl-analysis"])
        subprocess.run(["curl", "-fsSL", 
                       "https://github.com/pearlfortune/pearl-miner/releases/download/v1.2.1/pearlfortune-v1.2.1.tar.gz",
                       "-o", "/workspace/pearl-analysis/miner.tar.gz"])
        subprocess.run(["tar", "-xzf", "/workspace/pearl-analysis/miner.tar.gz", 
                       "-C", "/workspace/pearl-analysis/"])
        miner_binary = "/workspace/pearl-analysis/pearlfortune/miner-cuda12"
    
    print(f"[1] Miner: {miner_binary}")
    print(f"[1] Exists: {os.path.exists(miner_binary)}")
    print()
    
    # Run the miner for 20 seconds and capture ALL output
    print("[2] Running miner (20 seconds)...")
    print("[2] Capturing all output...")
    print()
    
    miner = subprocess.Popen(
        [miner_binary, 
         "--proxy", "global.pearlfortune.org:443",
         "--address", "prl1par2eef0c04z6s6fhlzx6setjh5xqv8et50ufsty5zhywqjghwuwq6p085p",
         "--worker", "capture-test",
         "-gpu"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Capture output
    start = time.time()
    lines = []
    while time.time() - start < 20:
        line = miner.stdout.readline()
        if line:
            print(line.strip())
            lines.append(line.strip())
        if miner.poll() is not None:
            break
    
    # Save output
    with open("/workspace/gpu-train-zeta-v3/miner_output.log", "w") as f:
        f.write("\n".join(lines))
    
    print()
    print("="*60)
    print(f"  Captured {len(lines)} lines of output")
    print("  Saved to: miner_output.log")
    print("="*60)
    print()
    print("Send me the output above!")
    
    miner.kill()

if __name__ == "__main__":
    main()
