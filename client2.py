import socket
import threading
import time
from DHKE import DHKE, p, g
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA256

# === CONFIGURATION ===
room = "room123"
server_host = '10.196.43.51' # Update to your server's IP
server_port = 6000
listen_port = 7000  # P2P listening port
# ======================

# === Ask name from user ===
name = input("Enter your name: ").strip()

# Setup DHKE
dh = DHKE(p, g)
dh.generate_private_key()
pubkey = dh.generate_public_key()

# Connect to mediator server
s = socket.socket()
s.connect((server_host, server_port))
s.send(f"{room}:{pubkey}:{name}".encode())

# Receive peer info
response = s.recv(4096).decode().strip()
print(f"[DEBUG] Raw response from server: {response}")

if ":" not in response:
    print("[ERROR] Malformed response from server.")
    exit()

peer_pubkey_str, peer_ip, peername = response.split(":", 2)
# Log peer IP and name
with open("peers.txt", "a") as f:
    f.write(f"{peername} - {peer_ip}\n")
print(f"[INFO] Peer logged: {peername} - {peer_ip}")
try:
    peer_pubkey = int(peer_pubkey_str)
except ValueError:
    print("[ERROR] Invalid peer public key.")
    exit()

print(f"[INFO] Received peer IP: {peer_ip}, peer public key: {peer_pubkey}")

# AES key setup
shared_secret = dh.compute_shared_secret(peer_pubkey)
aes_key = SHA256.new(str(shared_secret).encode()).digest()
print(f"[INFO] AES Key: {aes_key.hex()}")

s.close()

# Role decision
my_ip = socket.gethostbyname(socket.gethostname())
is_host = pubkey > peer_pubkey
print(f"[INFO] My IP: {my_ip}")
print(f"[INFO] Peer IP: {peer_ip}")
print(f"[INFO] Peer Name: {peername}")
print(f"[INFO] I am {'host' if is_host else 'client'}")

# === Receive messages ===
def handle_recv(p2p_conn):
    while True:
        try:
            data = p2p_conn.recv(4096)
            if not data:
                print(f"\n[INFO] {peername} disconnected.")
                break
            iv = data[:16]
            ct = data[16:]
            cipher = AES.new(aes_key, AES.MODE_CBC, iv)
            msg = unpad(cipher.decrypt(ct), AES.block_size)
            print(f"\n{peername}: {msg.decode()}\nYou: ", end="")
        except Exception as e:
            print(f"[RECEIVE ERROR] {e}")
            break

# === Send messages ===
def handle_send(p2p_conn):
    while True:
        try:
            msg = input("You: ").encode()
            cipher = AES.new(aes_key, AES.MODE_CBC)
            ct = cipher.encrypt(pad(msg, AES.block_size))
            p2p_conn.send(cipher.iv + ct)
        except Exception as e:
            print(f"[SEND ERROR] {e}")
            break

# === P2P Connection ===
if is_host:
    print("[P2P] Acting as host... Waiting for peer to connect.")
    listener = socket.socket()
    listener.bind(('', listen_port))
    listener.listen(1)
    conn, addr = listener.accept()
    print(f"[P2P] Connection established with {addr}")
else:
    print("[P2P] Acting as client...")
    conn = socket.socket()
    while True:
        try:
            conn.connect((peer_ip, listen_port))
            print(f"[P2P] Connected to host at {peer_ip}:{listen_port}")
            break
        except ConnectionRefusedError:
            print("[P2P] Host not ready, retrying...")
            time.sleep(1)

# Start threads
threading.Thread(target=handle_recv, args=(conn,), daemon=True).start()
threading.Thread(target=handle_send, args=(conn,), daemon=True).start()

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[INFO] Exiting.")
    conn.close()
