#!/usr/bin/env python3
"""
Pearl Miner v3.0 — Quick Test Script
Run this on the Salad GPU instance to test RPC connection.

Usage:
  python3 test_rpc.py
"""

import socket
import ssl
import json
import time
import sys

# Pool configuration
POOL_HOST = "global.pearlfortune.org"
POOL_PORT = 443
WALLET = "prl1par2eef0c04z6s6fhlzx6setjh5xqv8et50ufsty5zhywqjghwuwq6p085p"
WORKER = "test-worker"

# Matrix dimensions (from live capture)
M = 1024
N = 196608
K = 8192
RANK = 512

def connect():
    """Connect to pool via TLS."""
    print(f"[1] Connecting to {POOL_HOST}:{POOL_PORT}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    ssl_sock = ctx.wrap_socket(sock, server_hostname=POOL_HOST)
    ssl_sock.connect((POOL_HOST, POOL_PORT))
    
    print(f"[1] ✅ Connected!")
    return ssl_sock

def send(ssl_sock, method, params=None):
    """Send RPC message."""
    msg = {
        "id": int(time.time() * 1000) % 1000000,
        "method": method,
        "params": params or {}
    }
    
    data = json.dumps(msg) + "\n"
    ssl_sock.sendall(data.encode())
    print(f"[2] Sent: {method}")

def receive(ssl_sock):
    """Receive RPC response."""
    try:
        data = ssl_sock.recv(65536).decode()
        if data:
            for line in data.strip().split("\n"):
                if line:
                    try:
                        resp = json.loads(line)
                        print(f"[3] Received: {json.dumps(resp, indent=2)[:500]}")
                        return resp
                    except json.JSONDecodeError:
                        print(f"[3] Raw: {line[:200]}")
            return None
    except Exception as e:
        print(f"[3] Receive error: {e}")
        return None

def main():
    """Main test function."""
    print("="*60)
    print("  Pearl RPC Test — v3.0")
    print("="*60)
    print()
    
    try:
        # Step 1: Connect
        ssl_sock = connect()
        
        # Step 2: Subscribe
        print()
        print("[2] Subscribing...")
        send(ssl_sock, "rpc.subscribe")
        time.sleep(1)
        resp = receive(ssl_sock)
        
        # Step 3: Authorize
        print()
        print("[2] Authorizing...")
        send(ssl_sock, "rpc.authorize")
        time.sleep(1)
        resp = receive(ssl_sock)
        
        # Step 4: Listen for tasks
        print()
        print("[4] Listening for tasks (5 seconds)...")
        for i in range(5):
            try:
                resp = receive(ssl_sock)
                if resp and resp.get("method") == "task.switch":
                    print(f"[4] ✅ Got task: {resp.get('params', {})}")
                    break
            except:
                pass
            time.sleep(1)
        
        # Step 5: Disconnect
        print()
        print("[5] Disconnecting...")
        ssl_sock.close()
        print("[5] ✅ Done!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("="*60)
    print("  Test Complete")
    print("="*60)

if __name__ == "__main__":
    main()
