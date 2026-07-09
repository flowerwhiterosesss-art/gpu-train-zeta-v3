#!/usr/bin/env python3
"""
Pearl Enrollment Capture — Full Traffic
Runs the actual miner and captures the enrollment handshake.

Usage:
  python3 capture_full.py
"""

import subprocess
import time
import sys
import os

def main():
    print("="*60)
    print("  Pearl Full Traffic Capture")
    print("="*60)
    print()
    
    # Step 1: Start tcpdump in background
    print("[1] Starting packet capture...")
    tcpdump = subprocess.Popen(
        ["tcpdump", "-i", "any", "-nn", "-w", "pearl_traffic.pcap", 
         "host", "global.pearlfortune.org"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)
    print(f"[1] tcpdump started (PID: {tcpdump.pid})")
    
    # Step 2: Run the miner
    print()
    print("[2] Starting miner (15 seconds)...")
    miner_dir = os.path.expanduser("~/pearl-analysis/pearlfortune")
    if not os.path.exists(miner_dir):
        # Try to find it
        for root, dirs, files in os.walk("/workspace"):
            for d in dirs:
                if "pearlfortune" in d:
                    miner_dir = os.path.join(root, d)
                    break
    
    miner_binary = os.path.join(miner_dir, "miner-cuda12")
    if not os.path.exists(miner_binary):
        print(f"[2] Miner not found at {miner_binary}")
        print("[2] Looking for miner...")
        result = subprocess.run(["find", "/workspace", "-name", "miner-cuda12", "-type", "f"], 
                              capture_output=True, text=True)
        if result.stdout:
            miner_binary = result.stdout.strip().split("\n")[0]
            print(f"[2] Found: {miner_binary}")
        else:
            print("[2] Miner not found! Please download it first.")
            tcpdump.kill()
            return
    
    print(f"[2] Running: {miner_binary}")
    miner = subprocess.Popen(
        [miner_binary, 
         "--proxy", "global.pearlfortune.org:443",
         "--address", "prl1par2eef0c04z6s6fhlzx6setjh5xqv8et50ufsty5zhywqjghwuwq6p085p",
         "--worker", "capture-test",
         "-gpu"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Capture miner output
    print("[2] Miner output:")
    start = time.time()
    while time.time() - start < 15:
        line = miner.stdout.readline()
        if line:
            print(f"  {line.strip()}")
        if miner.poll() is not None:
            break
    
    # Step 3: Stop both
    print()
    print("[3] Stopping...")
    miner.kill()
    tcpdump.kill()
    
    # Step 4: Analyze capture
    print()
    print("[4] Analyzing capture...")
    result = subprocess.run(["tshark", "-r", "pearl_traffic.pcap", "-Y", "tcp", "-T", "fields", 
                           "-e", "tcp.port", "-e", "tcp.len"], 
                          capture_output=True, text=True)
    if result.stdout:
        print(f"[4] TCP packets: {len(result.stdout.splitlines())}")
    
    # Try to decode TLS
    result = subprocess.run(["tshark", "-r", "pearl_traffic.pcap", "-Y", "tls", "-T", "fields",
                           "-e", "tls.handshake.type", "-e", "tls.handshake.certificate"],
                          capture_output=True, text=True)
    if result.stdout:
        print(f"[4] TLS handshake data captured")
    
    print()
    print("="*60)
    print("  Capture Complete")
    print("="*60)
    print()
    print("Files created:")
    print("  - pearl_traffic.pcap (full packet capture)")
    print()
    print("Analyze with:")
    print("  tshark -r pearl_traffic.pcap")
    print("  tshark -r pearl_traffic.pcap -Y 'tls'")
    print("  tshark -r pearl_traffic.pcap -Y 'http'")
    print()

if __name__ == "__main__":
    main()
