# 🔐 Secure P2P Chat App

A lightweight Python-based peer-to-peer (P2P) encrypted messaging app that uses **Diffie-Hellman Key Exchange** for secure key generation and **AES encryption** for communication. The app connects two peers via a mediator server, then establishes a direct encrypted channel for messaging.

---

## 🚀 Features

- 🔐 End-to-end encrypted messaging using AES (CBC mode)
- 🧠 Secure key generation with Diffie-Hellman Key Exchange
- 🌐 P2P connection without permanent centralized servers
- 📝 Logs connected peer IPs and names in `peers.txt` for later use
- 🔄 Auto-reconnect attempts for clients waiting on host

---

## 🛠️ Technologies Used

- Python `socket` and `threading` modules for networking
- Custom `DHKE.py` for Diffie-Hellman key generation
- `PyCryptodome` for AES encryption (CBC mode)
- Basic file logging for peer history

---

## 📁 Project Structure

SecureP2PChat/
│
├── client.py         # P2P messaging client (handles DHKE, AES, messaging)
├── server.py         # Mediator server to match peers based on room ID
├── DHKE.py           # Diffie-Hellman Key Exchange implementation
├── peers.txt         # Log of connected peer IPs and names
└── README.md         # Project documentation

## 🚀 How It Works

This project implements a secure peer-to-peer (P2P) messaging system with end-to-end encryption, using a mediator server for peer discovery and initial connection setup.

1. **Start the Mediator Server**  
   Run `server.py` on a public or LAN-accessible machine. This acts as a temporary mediator to help two users find each other using a shared room ID.

2. **Connect the Clients**  
   Each user runs `client.py`, enters their name, and provides the same room ID. The client:
   - Sends its Diffie-Hellman (DH) public key and name to the server.
   - Waits for the other peer to join the same room.

3. **Key Exchange**  
   When both peers are connected:
   - They receive each other's public keys and IP addresses.
   - A shared AES encryption key is derived using Diffie-Hellman Key Exchange.

4. **P2P Connection & Messaging**  
   - One peer acts as a host and listens for a connection.
   - The other connects directly to the host using the received IP address.
   - All messages are encrypted with AES in CBC mode using the shared key.

5. **Logging Peers**  
   Each time a new peer connects, their IP and name are logged in `peers.txt` for later reference.

✅ No messages pass through the server — all communication is encrypted and direct between peers.

## ⚙️ How to Set Up

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/secure-p2p-chat.git
cd secure-p2p-chat
```

### 2. Install Dependencies

Make sure you have Python 3 installed, then install the required libraries:

```bash
pip install pycryptodome
```

### 3. Set the Server IP in `client.py`

Open `client.py` in a text editor and update the `server_host` variable with the IP address of the machine running `server.py`:

```python
server_host = 'YOUR.SERVER.IP.ADDRESS'  # <-- Replace this with actual server IP
```

### 4. Start the Mediator Server

Run the mediator on a machine accessible to both clients (public IP or same LAN):

```bash
python server.py
```

> The mediator helps peers find each other. It does **not** relay messages.

### 5. Run the Clients

On each client machine, run:

```bash
python client.py
```

- You will be prompted to enter your **name**.
- Make sure both peers enter the **same room name** to connect.
- The clients use **Diffie-Hellman** to securely derive a shared key, then chat via a **peer-to-peer AES-encrypted socket**.
