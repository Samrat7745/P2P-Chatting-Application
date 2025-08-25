import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import socket
import threading
import time
from datetime import datetime
import json
import os
from DHKE import DHKE, p, g
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA256

class P2PChatGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("P2P Secure Chat")
        self.root.geometry("800x600")
        self.root.configure(bg='#1e1e1e')
        
        # Dark theme colors
        self.colors = {
            'bg': '#1e1e1e',
            'surface': '#2d2d2d',
            'primary': '#4a9eff',
            'secondary': '#6c757d',
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'text': '#ffffff',
            'text_muted': '#b8b8b8',
            'border': '#404040'
        }
        
        # Configuration
        self.room = "room123"
        self.server_host = '10.196.43.51'
        self.server_port = 6000
        self.listen_port = 7000
        
        # Chat variables
        self.name = ""
        self.peer_name = ""
        self.peer_ip = ""
        self.conn = None
        self.aes_key = None
        self.is_connected = False
        self.is_host = False
        
        # Setup UI
        self.setup_styles()
        self.create_widgets()
        self.setup_layout()
        
        # Start with connection dialog
        self.root.after(100, self.show_connection_dialog)
        
    def setup_styles(self):
        """Configure ttk styles for dark theme"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Dark.TLabel', 
                       background=self.colors['bg'], 
                       foreground=self.colors['text'])
        
        style.configure('Dark.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Dark.TButton',
                 background=[('active', '#3d8bfd')])
        
        style.configure('Dark.TEntry',
                       fieldbackground=self.colors['surface'],
                       foreground=self.colors['text'],
                       borderwidth=1,
                       insertcolor=self.colors['text'])
        
        style.configure('Dark.TFrame',
                       background=self.colors['bg'],
                       borderwidth=0)
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        
        # Header frame
        self.header_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        
        # Status indicators
        self.status_frame = ttk.Frame(self.header_frame, style='Dark.TFrame')
        
        self.connection_status = tk.Label(self.status_frame,
                                        text="● Disconnected",
                                        fg=self.colors['danger'],
                                        bg=self.colors['bg'],
                                        font=('Arial', 10, 'bold'))
        
        self.peer_info = tk.Label(self.status_frame,
                                text="No peer connected",
                                fg=self.colors['text_muted'],
                                bg=self.colors['bg'],
                                font=('Arial', 9))
        
        # Chat area
        self.chat_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        
        # Messages display
        self.messages_text = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            width=70,
            height=25,
            bg=self.colors['surface'],
            fg=self.colors['text'],
            font=('Consolas', 11),
            insertbackground=self.colors['text'],
            selectbackground=self.colors['primary'],
            border=0,
            highlightthickness=1,
            highlightcolor=self.colors['border'],
            highlightbackground=self.colors['border']
        )
        
        # Input area
        self.input_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        
        self.message_entry = tk.Entry(
            self.input_frame,
            bg=self.colors['surface'],
            fg=self.colors['text'],
            font=('Arial', 11),
            insertbackground=self.colors['text'],
            border=0,
            highlightthickness=1,
            highlightcolor=self.colors['primary'],
            highlightbackground=self.colors['border']
        )
        
        self.send_button = tk.Button(
            self.input_frame,
            text="Send",
            bg=self.colors['primary'],
            fg='white',
            font=('Arial', 10, 'bold'),
            border=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.send_message
        )
        
        # Control buttons
        self.controls_frame = ttk.Frame(self.main_frame, style='Dark.TFrame')
        
        self.connect_button = tk.Button(
            self.controls_frame,
            text="Connect",
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 9, 'bold'),
            border=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.connect_to_peer
        )
        
        self.disconnect_button = tk.Button(
            self.controls_frame,
            text="Disconnect",
            bg=self.colors['danger'],
            fg='white',
            font=('Arial', 9, 'bold'),
            border=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.disconnect,
            state='disabled'
        )
        
        self.settings_button = tk.Button(
            self.controls_frame,
            text="Settings",
            bg=self.colors['secondary'],
            fg='white',
            font=('Arial', 9, 'bold'),
            border=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.show_settings
        )
        
    def setup_layout(self):
        """Arrange widgets in the window"""
        # Main frame
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        self.status_frame.pack(side=tk.LEFT)
        self.connection_status.pack(side=tk.LEFT)
        self.peer_info.pack(side=tk.LEFT, padx=(10, 0))
        
        # Controls (right side of header)
        self.controls_frame.pack(side=tk.RIGHT)
        self.settings_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.disconnect_button.pack(side=tk.RIGHT, padx=(5, 0))
        self.connect_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Chat area
        self.chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.messages_text.pack(fill=tk.BOTH, expand=True)
        
        # Input area
        self.input_frame.pack(fill=tk.X)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.send_button.pack(side=tk.RIGHT)
        
        # Bind events
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def show_connection_dialog(self):
        """Show initial connection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Connect to Chat")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 200,
            self.root.winfo_rooty() + 150
        ))
        
        # Title
        title_label = tk.Label(dialog,
                              text="P2P Secure Chat",
                              font=('Arial', 16, 'bold'),
                              fg=self.colors['primary'],
                              bg=self.colors['bg'])
        title_label.pack(pady=20)
        
        # Name input
        tk.Label(dialog, text="Your Name:", 
                fg=self.colors['text'], bg=self.colors['bg'],
                font=('Arial', 11)).pack(pady=(10, 5))
        
        name_entry = tk.Entry(dialog,
                             bg=self.colors['surface'],
                             fg=self.colors['text'],
                             font=('Arial', 11),
                             width=20)
        name_entry.pack(pady=(0, 10))
        name_entry.focus()
        
        # Server settings
        tk.Label(dialog, text="Server IP:", 
                fg=self.colors['text'], bg=self.colors['bg'],
                font=('Arial', 11)).pack(pady=(10, 5))
        
        server_entry = tk.Entry(dialog,
                               bg=self.colors['surface'],
                               fg=self.colors['text'],
                               font=('Arial', 11),
                               width=20)
        server_entry.pack(pady=(0, 10))
        server_entry.insert(0, self.server_host)
        
        # Room input
        tk.Label(dialog, text="Room:", 
                fg=self.colors['text'], bg=self.colors['bg'],
                font=('Arial', 11)).pack(pady=(10, 5))
        
        room_entry = tk.Entry(dialog,
                             bg=self.colors['surface'],
                             fg=self.colors['text'],
                             font=('Arial', 11),
                             width=20)
        room_entry.pack(pady=(0, 20))
        room_entry.insert(0, self.room)
        
        def on_connect():
            name = name_entry.get().strip()
            server_ip = server_entry.get().strip()
            room = room_entry.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Please enter your name")
                return
                
            self.name = name
            self.server_host = server_ip
            self.room = room
            dialog.destroy()
            self.connect_to_peer()
        
        # Connect button
        connect_btn = tk.Button(dialog,
                               text="Connect",
                               bg=self.colors['success'],
                               fg='white',
                               font=('Arial', 11, 'bold'),
                               border=0,
                               padx=30,
                               pady=8,
                               cursor='hand2',
                               command=on_connect)
        connect_btn.pack(pady=10)
        
        name_entry.bind('<Return>', lambda e: on_connect())
        
    def add_message(self, sender, message, is_system=False):
        """Add a message to the chat display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.messages_text.config(state=tk.NORMAL)
        
        if is_system:
            self.messages_text.insert(tk.END, f"[{timestamp}] {message}\n", 'system')
        else:
            if sender == self.name:
                self.messages_text.insert(tk.END, f"[{timestamp}] You: {message}\n", 'you')
            else:
                self.messages_text.insert(tk.END, f"[{timestamp}] {sender}: {message}\n", 'peer')
        
        # Configure tags for colors
        self.messages_text.tag_config('system', foreground=self.colors['warning'])
        self.messages_text.tag_config('you', foreground=self.colors['primary'])
        self.messages_text.tag_config('peer', foreground=self.colors['success'])
        
        self.messages_text.config(state=tk.DISABLED)
        self.messages_text.see(tk.END)
        
    def send_message(self):
        """Send a message to the peer"""
        if not self.is_connected or not self.conn:
            messagebox.showwarning("Warning", "Not connected to peer")
            return
            
        message = self.message_entry.get().strip()
        if not message:
            return
            
        try:
            msg_bytes = message.encode()
            cipher = AES.new(self.aes_key, AES.MODE_CBC)
            ct = cipher.encrypt(pad(msg_bytes, AES.block_size))
            self.conn.send(cipher.iv + ct)
            
            self.add_message(self.name, message)
            self.message_entry.delete(0, tk.END)
            
        except Exception as e:
            self.add_message("System", f"Send error: {str(e)}", True)
            
    def connect_to_peer(self):
        """Connect to peer through mediator server"""
        if self.is_connected:
            return
            
        self.add_message("System", "Connecting to server...", True)
        self.connect_button.config(state='disabled')
        
        # Run connection in separate thread
        threading.Thread(target=self._connect_thread, daemon=True).start()
        
    def _connect_thread(self):
        """Connection thread"""
        try:
            # Setup DHKE
            dh = DHKE(p, g)
            dh.generate_private_key()
            pubkey = dh.generate_public_key()
            
            # Connect to mediator server
            s = socket.socket()
            s.connect((self.server_host, self.server_port))
            s.send(f"{self.room}:{pubkey}:{self.name}".encode())
            
            # Receive peer info
            response = s.recv(4096).decode().strip()
            
            if ":" not in response:
                raise Exception("Malformed response from server")
                
            peer_pubkey_str, self.peer_ip, self.peer_name = response.split(":", 2)
            peer_pubkey = int(peer_pubkey_str)
            
            # Setup AES key
            shared_secret = dh.compute_shared_secret(peer_pubkey)
            self.aes_key = SHA256.new(str(shared_secret).encode()).digest()
            
            s.close()
            
            # Determine role
            self.is_host = pubkey > peer_pubkey
            
            self.root.after(0, lambda: self.add_message("System", 
                f"Found peer: {self.peer_name} ({self.peer_ip})", True))
            self.root.after(0, lambda: self.add_message("System", 
                f"Role: {'Host' if self.is_host else 'Client'}", True))
            
            # Establish P2P connection
            if self.is_host:
                self._host_connection()
            else:
                self._client_connection()
                
        except Exception as e:
            self.root.after(0, lambda: self.add_message("System", 
                f"Connection error: {str(e)}", True))
            self.root.after(0, lambda: self.connect_button.config(state='normal'))
            
    def _host_connection(self):
        """Host P2P connection"""
        try:
            self.root.after(0, lambda: self.add_message("System", 
                "Waiting for peer to connect...", True))
            
            listener = socket.socket()
            listener.bind(('', self.listen_port))
            listener.listen(1)
            
            self.conn, addr = listener.accept()
            listener.close()
            
            self._connection_established()
            
        except Exception as e:
            self.root.after(0, lambda: self.add_message("System", 
                f"Host connection error: {str(e)}", True))
            
    def _client_connection(self):
        """Client P2P connection"""
        try:
            self.conn = socket.socket()
            max_retries = 10
            
            for i in range(max_retries):
                try:
                    self.conn.connect((self.peer_ip, self.listen_port))
                    break
                except ConnectionRefusedError:
                    if i == max_retries - 1:
                        raise Exception("Host not available")
                    time.sleep(1)
            
            self._connection_established()
            
        except Exception as e:
            self.root.after(0, lambda: self.add_message("System", 
                f"Client connection error: {str(e)}", True))
            
    def _connection_established(self):
        """Handle successful P2P connection"""
        self.is_connected = True
        
        # Update UI
        self.root.after(0, self._update_connection_ui)
        
        # Start message handling threads
        threading.Thread(target=self._receive_messages, daemon=True).start()
        
    def _update_connection_ui(self):
        """Update UI for connected state"""
        self.connection_status.config(text="● Connected", fg=self.colors['success'])
        self.peer_info.config(text=f"Connected to: {self.peer_name}")
        self.connect_button.config(state='disabled')
        self.disconnect_button.config(state='normal')
        self.add_message("System", f"Connected to {self.peer_name}!", True)
        
    def _receive_messages(self):
        """Handle incoming messages"""
        while self.is_connected and self.conn:
            try:
                data = self.conn.recv(4096)
                if not data:
                    break
                    
                iv = data[:16]
                ct = data[16:]
                cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
                msg = unpad(cipher.decrypt(ct), AES.block_size)
                
                self.root.after(0, lambda m=msg.decode(): 
                    self.add_message(self.peer_name, m))
                    
            except Exception as e:
                self.root.after(0, lambda: self.add_message("System", 
                    f"Receive error: {str(e)}", True))
                break
                
        # Connection lost
        if self.is_connected:
            self.root.after(0, self._connection_lost)
            
    def _connection_lost(self):
        """Handle connection loss"""
        self.is_connected = False
        self.connection_status.config(text="● Disconnected", fg=self.colors['danger'])
        self.peer_info.config(text="Connection lost")
        self.connect_button.config(state='normal')
        self.disconnect_button.config(state='disabled')
        self.add_message("System", "Connection lost", True)
        
    def disconnect(self):
        """Disconnect from peer"""
        if self.conn:
            self.conn.close()
            self.conn = None
        self.is_connected = False
        self._connection_lost()
        
    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog coming soon!")
        
    def on_closing(self):
        """Handle window closing"""
        self.disconnect()
        self.root.destroy()
        
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = P2PChatGUI()
    app.run()