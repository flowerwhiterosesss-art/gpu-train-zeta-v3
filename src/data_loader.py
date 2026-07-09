#!/usr/bin/env python3
"""
Pearl RPC Client v3.0
Based on LIVE protocol capture from Salad GPU instance.

Pool: global.pearlfortune.org:443
Protocol: Custom RPC (NOT stratum!)
Algorithm: PearlHash (MatMul-based PoW)
Matrix: m=1024, n=196608, k=8192, rank=512
"""

import socket
import ssl
import json
import time
import threading
import os

class PearlRPCClient:
    """Custom RPC client for Pearl pools."""
    
    def __init__(self, pool_host, pool_port, wallet, worker):
        self.pool_host = pool_host
        self.pool_port = pool_port
        self.wallet = wallet
        self.worker = worker
        self.sock = None
        self.ssl_sock = None
        self.connected = False
        self.running = True
        self.job = None
        self.task_id = None
        self.height = None
        
    def connect(self):
        """Connect to pool via TLS."""
        print(f"[RPC] Connecting to {self.pool_host}:{self.pool_port}")
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(30)
        
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        try:
            self.ssl_sock = ctx.wrap_socket(self.sock, server_hostname=self.pool_host)
            self.ssl_sock.connect((self.pool_host, self.pool_port))
            self.connected = True
            print(f"[RPC] Connected to {self.pool_host}")
            return True
        except Exception as e:
            print(f"[RPC] Connection failed: {e}")
            return False
    
    def send(self, method, params=None):
        """Send RPC message."""
        if not self.connected:
            return False
        
        msg = {
            "id": int(time.time() * 1000) % 1000000,
            "method": method,
            "params": params or {}
        }
        
        data = json.dumps(msg) + "\n"
        try:
            self.ssl_sock.sendall(data.encode())
            print(f"[RPC] Sent: {method}")
            return True
        except Exception as e:
            print(f"[RPC] Send failed: {e}")
            return False
    
    def receive(self):
        """Receive RPC response."""
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
            print(f"[RPC] Receive failed: {e}")
        return None
    
    def subscribe(self):
        """Subscribe to mining tasks (rpc.subscribe)."""
        print("[RPC] Subscribing...")
        self.send("rpc.subscribe")
        responses = self.receive()
        if responses:
            for resp in responses:
                if "result" in resp:
                    print(f"[RPC] Subscribed: {resp['result']}")
                    return True
                elif "method" in resp and resp["method"] == "task.switch":
                    # Got a task
                    params = resp.get("params", {})
                    self.task_id = params.get("task_id")
                    self.height = params.get("height")
                    print(f"[RPC] Got task: {self.task_id}, height: {self.height}")
                    return True
        return False
    
    def authorize(self):
        """Authorize with wallet (rpc.authorize)."""
        print(f"[RPC] Authorizing with wallet: {self.wallet[:16]}...")
        self.send("rpc.authorize")
        responses = self.receive()
        if responses:
            for resp in responses:
                if resp.get("result") == True or "id" in resp:
                    print("[RPC] Authorized successfully")
                    return True
                elif "error" in resp:
                    print(f"[RPC] Auth error: {resp['error']}")
        return False
    
    def handle_task(self, params):
        """Handle task.switch (new mining task)."""
        self.task_id = params.get("task_id")
        self.height = params.get("height")
        self.job = params
        print(f"[RPC] New task: {self.task_id}, height: {self.height}")
        return True
    
    def submit_share(self, nonce, result):
        """Submit a share to the pool."""
        if not self.task_id:
            print("[RPC] No task to submit")
            return False
        
        msg = {
            "task_id": self.task_id,
            "nonce": nonce,
            "result": result
        }
        print(f"[RPC] Submitting share: task={self.task_id}")
        self.send("rpc.submit", msg)
        responses = self.receive()
        if responses:
            for resp in responses:
                if resp.get("result") == True:
                    print("[RPC] Share ACCEPTED!")
                    return True
                elif "error" in resp:
                    print(f"[RPC] Share REJECTED: {resp['error']}")
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
                        if method == "task.switch":
                            self.handle_task(resp.get("params", {}))
                        elif method == "rpc.submit":
                            # Submit response
                            pass
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[RPC] Listen error: {e}")
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
        print("[RPC] Disconnected")


def main():
    """Main function."""
    # Pool configuration
    POOL_HOST = "global.pearlfortune.org"
    POOL_PORT = 443
    WALLET = "prl1par2eef0c04z6s6fhlzx6setjh5xqv8et50ufsty5zhywqjghwuwq6p085p"
    WORKER = "worker1"
    
    # Matrix dimensions (from live capture)
    M = 1024
    N = 196608
    K = 8192
    RANK = 512
    
    print("="*60)
    print("  Pearl RPC Client v3.0")
    print("="*60)
    print(f"  Pool: {POOL_HOST}:{POOL_PORT}")
    print(f"  Wallet: {WALLET[:16]}...")
    print(f"  Matrix: {M}x{N}x{K}, rank={RANK}")
    print("="*60)
    
    # Create client
    client = PearlRPCClient(POOL_HOST, POOL_PORT, WALLET, WORKER)
    
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
    
    print("[Main] Connected and listening for tasks...")
    print("[Main] Press Ctrl+C to stop")
    
    # Wait for first task
    while client.running and not client.job:
        time.sleep(1)
    
    if client.job:
        print(f"[Main] Got task: {client.task_id}")
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
