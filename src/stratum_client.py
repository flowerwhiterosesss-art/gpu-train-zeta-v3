#!/usr/bin/env python3
"""
Pearl Stratum Client v3.0
Custom implementation with TLS enrollment.

Pool: global.pearlfortune.org:443
Protocol: stratum+tcp with TLS client cert
Algorithm: PearlHash (MatMul-based PoW)
"""

import socket
import ssl
import json
import time
import hashlib
import base64
import threading
import struct
import os
import sys

class PearlStratumClient:
    """Custom stratum client for Pearl pools with TLS enrollment."""
    
    def __init__(self, pool_host, pool_port, wallet, worker):
        self.pool_host = pool_host
        self.pool_port = pool_port
        self.wallet = wallet
        self.worker = worker
        self.sock = None
        self.ssl_sock = None
        self.job = None
        self.job_id = None
        self.extranonce = None
        self.difficulty = None
        self.connected = False
        self.running = True
        self.client_cert = None
        self.client_key = None
        self.server_ca = None
        
    def enroll_tls(self):
        """TLS enrollment - get client certificate from pool."""
        print("[Enroll] Starting TLS enrollment...")
        
        # Create HTTP connection to enrollment endpoint
        enroll_url = f"https://{self.pool_host}/enroll/client-cert"
        
        # Build enrollment payload
        payload = {
            "miner_version": "3.0.0",
            "cuda_build": "12.4",
            "cuda_runtime": "12.4",
            "cuda_driver": "545.0",
            "worker": self.worker,
            "address": self.wallet
        }
        
        print(f"[Enroll] Requesting client certificate from {enroll_url}")
        
        try:
            # Simple HTTPS POST
            import urllib.request
            import urllib.parse
            
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                enroll_url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "PearlMiner/3.0"
                }
            )
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            response = urllib.request.urlopen(req, context=ctx, timeout=10)
            response_data = response.read()
            
            # Parse response
            result = json.loads(response_data)
            
            if "encrypted" in result:
                # Response is encrypted - need to decrypt
                print("[Enroll] Received encrypted enrollment response")
                # TODO: Implement AES-256-GCM decryption
                # For now, we'll try without client cert
                print("[Enroll] WARNING: Encrypted enrollment not implemented yet")
                return False
            
            if "client_cert_pem" in result:
                self.client_cert = result["client_cert_pem"]
                self.client_key = result["client_key_pem"]
                self.server_ca = result.get("server_ca_pem")
                print("[Enroll] Got client certificate")
                return True
            
            print(f"[Enroll] Unexpected response: {result}")
            return False
            
        except Exception as e:
            print(f"[Enroll] Enrollment failed: {e}")
            return False
    
    def connect(self):
        """Connect to pool via TLS with client certificate."""
        print(f"[Stratum] Connecting to {self.pool_host}:{self.pool_port}")
        
        # Create socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(30)
        
        # TLS context
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Load client certificate if we have one
        if self.client_cert and self.client_key:
            # Write temp cert files
            cert_file = "/tmp/pearl_client_cert.pem"
            key_file = "/tmp/pearl_client_key.pem"
            
            with open(cert_file, "w") as f:
                f.write(self.client_cert)
            with open(key_file, "w") as f:
                f.write(self.client_key)
            
            ctx.load_cert_chain(cert_file, key_file)
            print("[Stratum] Using client certificate")
            
            # Cleanup
            os.unlink(cert_file)
            os.unlink(key_file)
        
        # Load server CA if provided
        if self.server_ca:
            ca_file = "/tmp/pearl_server_ca.pem"
            with open(ca_file, "w") as f:
                f.write(self.server_ca)
            ctx.load_verify_locations(ca_file)
            os.unlink(ca_file)
        
        try:
            self.ssl_sock = ctx.wrap_socket(self.sock, server_hostname=self.pool_host)
            self.ssl_sock.connect((self.pool_host, self.pool_port))
            self.connected = True
            print(f"[Stratum] Connected to {self.pool_host}")
            return True
        except Exception as e:
            print(f"[Stratum] Connection failed: {e}")
            return False
    
    def send(self, msg):
        """Send JSON-RPC message."""
        if not self.connected:
            return False
        
        data = json.dumps(msg) + "\n"
        try:
            self.ssl_sock.sendall(data.encode())
            return True
        except Exception as e:
            print(f"[Stratum] Send failed: {e}")
            return False
    
    def receive(self):
        """Receive JSON-RPC response."""
        if not self.connected:
            return None
        
        try:
            data = self.ssl_sock.recv(65536).decode()
            if data:
                messages = []
                for line in data.strip().split("\n"):
                    if line:
                        try:
                            messages.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
                return messages
        except Exception as e:
            print(f"[Stratum] Receive failed: {e}")
        return None
    
    def subscribe(self):
        """Subscribe to mining notifications."""
        msg = {
            "id": 1,
            "method": "mining.subscribe",
            "params": ["PearlMiner/3.0", None]
        }
        print("[Stratum] Subscribing...")
        self.send(msg)
        responses = self.receive()
        if responses:
            for resp in responses:
                if "result" in resp:
                    self.extranonce = resp["result"][1] if len(resp["result"]) > 1 else None
                    print(f"[Stratum] Subscribed, extranonce: {self.extranonce}")
                    return True
        return False
    
    def authorize(self):
        """Authorize with wallet."""
        msg = {
            "id": 2,
            "method": "mining.authorize",
            "params": [self.wallet, self.worker]
        }
        print(f"[Stratum] Authorizing with wallet: {self.wallet[:16]}...")
        self.send(msg)
        responses = self.receive()
        if responses:
            for resp in responses:
                if resp.get("result") == True:
                    print("[Stratum] Authorized successfully")
                    return True
                elif "error" in resp:
                    print(f"[Stratum] Auth error: {resp['error']}")
        return False
    
    def handle_notify(self, params):
        """Handle mining.notify (new job)."""
        if params and len(params) >= 7:
            self.job_id = params[0]
            self.job = {
                "job_id": params[0],
                "prev_hash": params[1],
                "coinb1": params[2],
                "coinb2": params[3],
                "merkle_branches": params[4],
                "version": params[5],
                "nbits": params[6],
                "ntime": params[7] if len(params) > 7 else None,
                "clean_jobs": params[8] if len(params) > 8 else False
            }
            print(f"[Stratum] New job: {self.job_id}")
            return True
        return False
    
    def submit_share(self, nonce, result):
        """Submit a share to the pool."""
        if not self.job_id:
            print("[Stratum] No job to submit")
            return False
        
        msg = {
            "id": 3,
            "method": "mining.submit",
            "params": [
                self.wallet,
                self.job_id,
                nonce,
                result
            ]
        }
        print(f"[Stratum] Submitting share: job={self.job_id}")
        self.send(msg)
        responses = self.receive()
        if responses:
            for resp in responses:
                if resp.get("result") == True:
                    print("[Stratum] Share ACCEPTED!")
                    return True
                elif "error" in resp:
                    print(f"[Stratum] Share REJECTED: {resp['error']}")
                    return False
        return False
    
    def listen(self):
        """Listen for pool messages."""
        while self.running and self.connected:
            try:
                responses = self.receive()
                if responses:
                    for resp in responses:
                        method = resp.get("method", "")
                        if method == "mining.notify":
                            self.handle_notify(resp.get("params", []))
                        elif method == "mining.set_difficulty":
                            self.difficulty = resp.get("params", [None])[0]
                            print(f"[Stratum] Difficulty set: {self.difficulty}")
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Stratum] Listen error: {e}")
                break
    
    def disconnect(self):
        """Disconnect from pool."""
        self.running = False
        if self.ssl_sock:
            try:
                self.ssl_sock.close()
            except:
                pass
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.connected = False
        print("[Stratum] Disconnected")


def main():
    """Main function."""
    # Pool configuration
    POOL_HOST = "global.pearlfortune.org"
    POOL_PORT = 443
    WALLET = "prl1par2eef0c04z6s6fhlzx6setjh5xqv8et50ufsty5zhywqjghwuwq6p085p"
    WORKER = "worker1"
    
    # Create client
    client = PearlStratumClient(POOL_HOST, POOL_PORT, WALLET, WORKER)
    
    # Try TLS enrollment
    if not client.enroll_tls():
        print("[Main] TLS enrollment failed, trying without client cert...")
    
    # Connect
    if not client.connect():
        print("[Main] Failed to connect")
        return
    
    # Subscribe
    if not client.subscribe():
        print("[Main] Failed to subscribe")
        client.disconnect()
        return
    
    # Authorize
    if not client.authorize():
        print("[Main] Failed to authorize")
        client.disconnect()
        return
    
    # Start listener thread
    listener = threading.Thread(target=client.listen, daemon=True)
    listener.start()
    
    print("[Main] Connected and listening for jobs...")
    print("[Main] Press Ctrl+C to stop")
    
    # Wait for first job
    while client.running and not client.job:
        time.sleep(1)
    
    if client.job:
        print(f"[Main] Got first job: {client.job_id}")
        print("[Main] Ready to mine!")
        
        # Mining loop (placeholder - actual CUDA kernel goes here)
        while client.running:
            time.sleep(1)
            # TODO: Call our custom CUDA kernel here
            # nonce, result = pearl_mine(client.job)
            # client.submit_share(nonce, result)
    
    client.disconnect()


if __name__ == "__main__":
    main()
