#!/usr/bin/env python3
"""
Pearl TLS Enrollment Capture
Captures the enrollment handshake to understand the protocol.

Run this on the Salad instance BEFORE the miner.
"""

import socket
import ssl
import json
import time
import threading

POOL_HOST = "global.pearlfortune.org"
POOL_PORT = 443

def capture_enrollment():
    """Capture the TLS enrollment handshake."""
    print("="*60)
    print("  Pearl TLS Enrollment Capture")
    print("="*60)
    print()
    
    # Connect WITHOUT client cert to see what the server asks for
    print("[1] Connecting without client cert...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Try to see what the server wants
    try:
        ssl_sock = ctx.wrap_socket(sock, server_hostname=POOL_HOST)
        ssl_sock.connect((POOL_HOST, POOL_PORT))
        
        print(f"[1] Connected! TLS version: {ssl_sock.version()}")
        print(f"[1] Cipher: {ssl_sock.cipher()}")
        
        # Send a dummy message to see what happens
        msg = {"method": "rpc.subscribe", "id": 1, "params": {}}
        data = json.dumps(msg) + "\n"
        ssl_sock.sendall(data.encode())
        
        print("[2] Sent subscribe, waiting for response...")
        
        try:
            resp = ssl_sock.recv(65536)
            print(f"[2] Response: {resp[:500]}")
        except ssl.SSLCertVerificationError as e:
            print(f"[2] Cert error: {e}")
        except Exception as e:
            print(f"[2] Error: {e}")
        
        ssl_sock.close()
        
    except Exception as e:
        print(f"[1] Error: {e}")
    
    print()
    print("="*60)
    print("  Analysis")
    print("="*60)
    print()
    print("The pool requires a client certificate for TLS.")
    print("The miner gets this via enrollment:")
    print("  1. First connection (no cert)")
    print("  2. Server sends enrollment challenge")
    print("  3. Client responds with token")
    print("  4. Server issues client certificate")
    print("  5. Client uses cert for mining connection")
    print()
    print("We need to capture the enrollment traffic to understand it.")
    print("="*60)

if __name__ == "__main__":
    capture_enrollment()
