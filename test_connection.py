#!/usr/bin/env python3
"""
Pearl TLS Enrollment Client
Gets client certificate using the "openpool" token.

Usage:
  python3 pearl_enroll.py
"""

import socket
import ssl
import json
import time
import os

POOL_HOST = "global.pearlfortune.org"
POOL_PORT = 443
TOKEN_ID = "openpool"

def enroll():
    """Get client certificate from pool."""
    print("="*60)
    print("  Pearl TLS Enrollment Client")
    print("="*60)
    print()
    print(f"[1] Connecting to {POOL_HOST}:{POOL_PORT}")
    
    # Connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    ssl_sock = ctx.wrap_socket(sock, server_hostname=POOL_HOST)
    ssl_sock.connect((POOL_HOST, POOL_PORT))
    
    print(f"[1] Connected! TLS: {ssl_sock.version()}")
    
    # Send enrollment request
    print()
    print(f"[2] Sending enrollment request (token: {TOKEN_ID})...")
    
    # The enrollment request format
    enroll_msg = {
        "method": "enroll",
        "params": {
            "token_id": TOKEN_ID,
            "miner_version": "3.0.0",
            "cuda_build": "12.8",
            "cuda_runtime": "12.8",
            "worker": "test-worker"
        }
    }
    
    data = json.dumps(enroll_msg) + "\n"
    ssl_sock.sendall(data.encode())
    
    print("[2] Request sent, waiting for response...")
    
    # Receive response
    try:
        resp_data = ssl_sock.recv(65536)
        print(f"[2] Received {len(resp_data)} bytes")
        
        # Try to parse as JSON
        try:
            resp = json.loads(resp_data.decode())
            print(f"[2] Response: {json.dumps(resp, indent=2)[:1000]}")
        except:
            print(f"[2] Raw response (hex): {resp_data[:200].hex()}")
            print(f"[2] Raw response (text): {resp_data[:200]}")
        
    except Exception as e:
        print(f"[2] Receive error: {e}")
    
    # Close
    ssl_sock.close()
    
    print()
    print("="*60)
    print("  Enrollment Complete")
    print("="*60)

if __name__ == "__main__":
    enroll()
