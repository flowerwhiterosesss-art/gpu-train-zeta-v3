#!/usr/bin/env python3
"""
Pearl TLS Handshake Capture
Captures the actual TLS handshake to understand enrollment.

Usage:
  python3 capture_tls.py
"""

import socket
import ssl
import json
import time

POOL_HOST = "global.pearlfortune.org"
POOL_PORT = 443

def capture_handshake():
    """Capture TLS handshake details."""
    print("="*60)
    print("  Pearl TLS Handshake Capture")
    print("="*60)
    print()
    
    # Create raw socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    
    # Connect first (raw TCP)
    print("[1] Connecting (raw TCP)...")
    sock.connect((POOL_HOST, POOL_PORT))
    print(f"[1] Connected to {POOL_HOST}:{POOL_PORT}")
    
    # Now try TLS with certificate request
    print()
    print("[2] Starting TLS handshake...")
    
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Enable certificate request
    ctx.post_handshake_auth = True
    
    try:
        ssl_sock = ctx.wrap_socket(sock, server_hostname=POOL_HOST)
        print(f"[2] TLS connected! Version: {ssl_sock.version()}")
        print(f"[2] Cipher: {ssl_sock.cipher()}")
        
        # Try to get peer certificate
        peer_cert = ssl_sock.getpeercert(binary_form=True)
        if peer_cert:
            print(f"[2] Peer cert: {len(peer_cert)} bytes")
        
        # Send a test message
        print()
        print("[3] Sending test message...")
        msg = json.dumps({"method": "test", "id": 1}) + "\n"
        ssl_sock.sendall(msg.encode())
        
        # Receive response
        try:
            resp = ssl_sock.recv(65536)
            print(f"[3] Response: {resp[:500]}")
        except Exception as e:
            print(f"[3] Receive error: {e}")
        
        ssl_sock.close()
        
    except ssl.SSLCertVerificationError as e:
        print(f"[2] Cert error: {e}")
    except Exception as e:
        print(f"[2] Error: {e}")
    
    sock.close()
    
    print()
    print("="*60)
    print("  Analysis")
    print("="*60)
    print()
    print("The server requires a client certificate during TLS handshake.")
    print("The miner gets this via a special enrollment process.")
    print()
    print("We need to capture the actual miner's TLS traffic to understand")
    print("how it performs enrollment.")
    print("="*60)

if __name__ == "__main__":
    capture_handshake()
