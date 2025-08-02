import socket
import threading

host = '0.0.0.0' # Listen on all interfaces
port = 6000

rooms = {}  # room_id: (pubkey, conn, addr, name)

def handle_client(conn, addr):
    try:
        data = conn.recv(4096).decode()
        parts = data.strip().split(":")

        if len(parts) != 3:
            print(f"[ERROR] Invalid data from {addr}: {data}")
            conn.send(b"error")
            return

        room_id, pubkey_str, name = parts
        try:
            pubkey = int(pubkey_str)
        except ValueError:
            print(f"[ERROR] Invalid pubkey from {addr}: {pubkey_str}")
            conn.send(b"error")
            return

        if room_id not in rooms:
            rooms[room_id] = (pubkey, conn, addr, name)
            print(f"[WAITING] {name} ({addr}) waiting in room {room_id}")
        else:
            pubkey1, conn1, addr1, name1 = rooms.pop(room_id)
            print(f"[MATCH] Connecting {name1} ({addr1}) and {name} ({addr})")

            try:
                # Send peer info to both clients: pubkey and IP
                conn1.send(f"{pubkey}:{addr[0]}:{name}".encode())
                conn.send(f"{pubkey1}:{addr1[0]}:{name1}".encode())
            except Exception as e:
                print("[ERROR] Failed to send to both clients:", e)
                conn1.close()
                conn.close()
    except Exception as e:
        print("[SERVER ERROR]", e)
    finally:
        pass  # Let client handle socket closing

server = socket.socket()
server.bind((host, port))
server.listen(5)
print(f"[MEDIATOR] Listening on {host}:{port}")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr)).start()
