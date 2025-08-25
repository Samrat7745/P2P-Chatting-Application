import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import time
from datetime import datetime
import json
import os

class MediatorServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("P2P Mediator Server")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1a1a1a')
        
        # Dark theme colors
        self.colors = {
            'bg': '#1a1a1a',
            'surface': '#2d2d2d',
            'primary': '#4a9eff',
            'secondary': '#6c757d',
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'text': '#ffffff',
            'text_muted': '#b8b8b8',
            'border': '#404040'
        }
        
        # Server configuration
        self.host = '0.0.0.0'
        self.port = 6000
        self.server_socket = None
        self.is_running = False
        
        # Data structures
        self.rooms = {}  # room_id: (pubkey, conn, addr, name, timestamp)
        self.connections = {}  # conn: (addr, room_id, name, timestamp)
        self.stats = {
            'total_connections': 0,
            'successful_matches': 0,
            'failed_connections': 0,
            'active_rooms': 0,
            'server_start_time': None
        }
        
        # Setup UI
        self.create_widgets()
        self.setup_layout()
        self.update_ui_thread()
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        
        # Header frame
        self.header_frame = tk.Frame(self.main_frame, bg=self.colors['surface'], height=80)
        self.header_frame.pack_propagate(False)
        
        # Title and server status
        self.title_label = tk.Label(
            self.header_frame,
            text="P2P Mediator Server",
            font=('Arial', 18, 'bold'),
            fg=self.colors['primary'],
            bg=self.colors['surface']
        )
        
        self.status_frame = tk.Frame(self.header_frame, bg=self.colors['surface'])
        
        self.server_status = tk.Label(
            self.status_frame,
            text="● Server Stopped",
            font=('Arial', 12, 'bold'),
            fg=self.colors['danger'],
            bg=self.colors['surface']
        )
        
        self.server_info = tk.Label(
            self.status_frame,
            text=f"Host: {self.host} | Port: {self.port}",
            font=('Arial', 10),
            fg=self.colors['text_muted'],
            bg=self.colors['surface']
        )
        
        # Control buttons
        self.controls_frame = tk.Frame(self.header_frame, bg=self.colors['surface'])
        
        self.start_button = tk.Button(
            self.controls_frame,
            text="Start Server",
            bg=self.colors['success'],
            fg='white',
            font=('Arial', 10, 'bold'),
            border=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.start_server
        )
        
        self.stop_button = tk.Button(
            self.controls_frame,
            text="Stop Server",
            bg=self.colors['danger'],
            fg='white',
            font=('Arial', 10, 'bold'),
            border=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.stop_server,
            state='disabled'
        )
        
        self.clear_logs_button = tk.Button(
            self.controls_frame,
            text="Clear Logs",
            bg=self.colors['secondary'],
            fg='white',
            font=('Arial', 10, 'bold'),
            border=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.clear_logs
        )
        
        # Main content area with notebook
        self.notebook = ttk.Notebook(self.main_frame)
        
        # Configure notebook style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', 
                       background=self.colors['bg'],
                       borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       padding=[20, 8])
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['primary'])])
        
        # Dashboard Tab
        self.dashboard_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.dashboard_frame, text='Dashboard')
        
        # Statistics cards
        self.stats_frame = tk.Frame(self.dashboard_frame, bg=self.colors['bg'])
        
        # Create stats cards
        self.create_stats_cards()
        
        # Active Rooms Tab
        self.rooms_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.rooms_frame, text='Active Rooms')
        
        # Rooms table
        self.rooms_tree = ttk.Treeview(
            self.rooms_frame,
            columns=('Room ID', 'Client Name', 'IP Address', 'Public Key', 'Wait Time'),
            show='headings',
            height=15
        )
        
        # Configure treeview style
        style.configure('Treeview',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       fieldbackground=self.colors['surface'])
        style.configure('Treeview.Heading',
                       background=self.colors['primary'],
                       foreground='white')
        
        # Define columns
        self.rooms_tree.heading('Room ID', text='Room ID')
        self.rooms_tree.heading('Client Name', text='Client Name')
        self.rooms_tree.heading('IP Address', text='IP Address')
        self.rooms_tree.heading('Public Key', text='Public Key')
        self.rooms_tree.heading('Wait Time', text='Wait Time')
        
        self.rooms_tree.column('Room ID', width=120)
        self.rooms_tree.column('Client Name', width=150)
        self.rooms_tree.column('IP Address', width=120)
        self.rooms_tree.column('Public Key', width=200)
        self.rooms_tree.column('Wait Time', width=100)
        
        # Scrollbar for rooms tree
        self.rooms_scrollbar = ttk.Scrollbar(self.rooms_frame, orient="vertical", command=self.rooms_tree.yview)
        self.rooms_tree.configure(yscrollcommand=self.rooms_scrollbar.set)
        
        # Logs Tab
        self.logs_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.logs_frame, text='Logs')
        
        # Logs display
        self.logs_text = scrolledtext.ScrolledText(
            self.logs_frame,
            wrap=tk.WORD,
            width=100,
            height=30,
            bg=self.colors['surface'],
            fg=self.colors['text'],
            font=('Consolas', 10),
            insertbackground=self.colors['text'],
            selectbackground=self.colors['primary'],
            border=0,
            highlightthickness=1,
            highlightcolor=self.colors['border'],
            highlightbackground=self.colors['border']
        )
        
        # Settings Tab
        self.settings_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.settings_frame, text='Settings')
        
        self.create_settings_widgets()
        
    def create_stats_cards(self):
        """Create statistics cards"""
        # Total Connections Card
        self.total_conn_card = self.create_stat_card(
            self.stats_frame, "Total Connections", "0", self.colors['primary']
        )
        
        # Successful Matches Card
        self.matches_card = self.create_stat_card(
            self.stats_frame, "Successful Matches", "0", self.colors['success']
        )
        
        # Failed Connections Card
        self.failed_card = self.create_stat_card(
            self.stats_frame, "Failed Connections", "0", self.colors['danger']
        )
        
        # Active Rooms Card
        self.active_rooms_card = self.create_stat_card(
            self.stats_frame, "Active Rooms", "0", self.colors['warning']
        )
        
        # Server Uptime Card
        self.uptime_card = self.create_stat_card(
            self.stats_frame, "Server Uptime", "00:00:00", self.colors['info']
        )
        
    def create_stat_card(self, parent, title, value, color):
        """Create a statistics card widget"""
        card_frame = tk.Frame(
            parent,
            bg=self.colors['surface'],
            relief='solid',
            bd=1,
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        
        title_label = tk.Label(
            card_frame,
            text=title,
            font=('Arial', 11, 'bold'),
            fg=self.colors['text_muted'],
            bg=self.colors['surface']
        )
        title_label.pack(pady=(15, 5))
        
        value_label = tk.Label(
            card_frame,
            text=value,
            font=('Arial', 20, 'bold'),
            fg=color,
            bg=self.colors['surface']
        )
        value_label.pack(pady=(0, 15))
        
        return {'frame': card_frame, 'value_label': value_label}
        
    def create_settings_widgets(self):
        """Create settings widgets"""
        settings_content = tk.Frame(self.settings_frame, bg=self.colors['bg'])
        settings_content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Server Configuration
        config_label = tk.Label(
            settings_content,
            text="Server Configuration",
            font=('Arial', 14, 'bold'),
            fg=self.colors['text'],
            bg=self.colors['bg']
        )
        config_label.pack(anchor='w', pady=(0, 10))
        
        # Host setting
        host_frame = tk.Frame(settings_content, bg=self.colors['bg'])
        host_frame.pack(fill='x', pady=5)
        
        tk.Label(host_frame, text="Host:", font=('Arial', 11),
                fg=self.colors['text'], bg=self.colors['bg']).pack(side='left')
        
        self.host_entry = tk.Entry(
            host_frame,
            bg=self.colors['surface'],
            fg=self.colors['text'],
            font=('Arial', 11),
            width=20
        )
        self.host_entry.pack(side='left', padx=(10, 0))
        self.host_entry.insert(0, self.host)
        
        # Port setting
        port_frame = tk.Frame(settings_content, bg=self.colors['bg'])
        port_frame.pack(fill='x', pady=5)
        
        tk.Label(port_frame, text="Port:", font=('Arial', 11),
                fg=self.colors['text'], bg=self.colors['bg']).pack(side='left')
        
        self.port_entry = tk.Entry(
            port_frame,
            bg=self.colors['surface'],
            fg=self.colors['text'],
            font=('Arial', 11),
            width=10
        )
        self.port_entry.pack(side='left', padx=(10, 0))
        self.port_entry.insert(0, str(self.port))
        
        # Apply settings button
        apply_button = tk.Button(
            settings_content,
            text="Apply Settings",
            bg=self.colors['primary'],
            fg='white',
            font=('Arial', 10, 'bold'),
            border=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.apply_settings
        )
        apply_button.pack(anchor='w', pady=20)
        
    def setup_layout(self):
        """Arrange widgets in the window"""
        self.main_frame.pack(fill='both', expand=True)
        
        # Header layout
        self.header_frame.pack(fill='x', padx=10, pady=10)
        
        self.title_label.pack(side='left', padx=(20, 0), pady=20)
        
        self.controls_frame.pack(side='right', padx=(0, 20), pady=20)
        self.clear_logs_button.pack(side='right', padx=(10, 0))
        self.stop_button.pack(side='right', padx=(10, 0))
        self.start_button.pack(side='right')
        
        self.status_frame.pack(expand=True, pady=20)
        self.server_status.pack()
        self.server_info.pack(pady=(5, 0))
        
        # Main content
        self.notebook.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Dashboard layout
        self.stats_frame.pack(fill='x', padx=20, pady=20)
        
        # Arrange stats cards in grid
        cards = [
            self.total_conn_card, self.matches_card, self.failed_card,
            self.active_rooms_card, self.uptime_card
        ]
        
        for i, card in enumerate(cards):
            row = i // 3
            col = i % 3
            card['frame'].grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
        # Configure grid weights
        for i in range(3):
            self.stats_frame.grid_columnconfigure(i, weight=1)
            
        # Rooms layout
        self.rooms_tree.pack(side='left', fill='both', expand=True, padx=(20, 0), pady=20)
        self.rooms_scrollbar.pack(side='right', fill='y', padx=(0, 20), pady=20)
        
        # Logs layout
        self.logs_text.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def log_message(self, message, level="INFO"):
        """Add a message to the logs"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.logs_text.config(state=tk.NORMAL)
        
        # Color coding based on level
        if level == "ERROR":
            self.logs_text.insert(tk.END, log_entry, 'error')
        elif level == "WARNING":
            self.logs_text.insert(tk.END, log_entry, 'warning')
        elif level == "SUCCESS":
            self.logs_text.insert(tk.END, log_entry, 'success')
        else:
            self.logs_text.insert(tk.END, log_entry, 'info')
            
        # Configure tags
        self.logs_text.tag_config('error', foreground=self.colors['danger'])
        self.logs_text.tag_config('warning', foreground=self.colors['warning'])
        self.logs_text.tag_config('success', foreground=self.colors['success'])
        self.logs_text.tag_config('info', foreground=self.colors['text'])
        
        self.logs_text.config(state=tk.DISABLED)
        self.logs_text.see(tk.END)
        
    def start_server(self):
        """Start the mediator server"""
        if self.is_running:
            return
            
        try:
            self.server_socket = socket.socket()
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            self.stats['server_start_time'] = datetime.now()
            
            # Update UI
            self.server_status.config(text="● Server Running", fg=self.colors['success'])
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            
            self.log_message(f"Server started on {self.host}:{self.port}", "SUCCESS")
            
            # Start server thread
            threading.Thread(target=self.server_loop, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"Failed to start server: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
            
    def stop_server(self):
        """Stop the mediator server"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.server_socket:
            self.server_socket.close()
            
        # Close all client connections
        for conn in list(self.connections.keys()):
            try:
                conn.close()
            except:
                pass
                
        self.connections.clear()
        self.rooms.clear()
        
        # Update UI
        self.server_status.config(text="● Server Stopped", fg=self.colors['danger'])
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        self.log_message("Server stopped", "WARNING")
        
    def server_loop(self):
        """Main server loop"""
        while self.is_running:
            try:
                conn, addr = self.server_socket.accept()
                self.stats['total_connections'] += 1
                
                self.log_message(f"New connection from {addr[0]}:{addr[1]}")
                
                # Handle client in separate thread
                threading.Thread(
                    target=self.handle_client, 
                    args=(conn, addr), 
                    daemon=True
                ).start()
                
            except Exception as e:
                if self.is_running:
                    self.log_message(f"Server loop error: {str(e)}", "ERROR")
                break
                
    def handle_client(self, conn, addr):
        """Handle individual client connection"""
        try:
            data = conn.recv(4096).decode()
            parts = data.strip().split(":")
            
            if len(parts) != 3:
                self.log_message(f"Invalid data from {addr}: {data}", "ERROR")
                conn.send(b"error")
                self.stats['failed_connections'] += 1
                return
                
            room_id, pubkey_str, name = parts
            
            try:
                pubkey = int(pubkey_str)
            except ValueError:
                self.log_message(f"Invalid pubkey from {addr}: {pubkey_str}", "ERROR")
                conn.send(b"error")
                self.stats['failed_connections'] += 1
                return
                
            # Store connection info
            self.connections[conn] = (addr, room_id, name, datetime.now())
            
            if room_id not in self.rooms:
                # First client in room - waiting
                self.rooms[room_id] = (pubkey, conn, addr, name, datetime.now())
                self.log_message(f"{name} ({addr[0]}) waiting in room {room_id}")
                
            else:
                # Second client - make connection
                pubkey1, conn1, addr1, name1, _ = self.rooms.pop(room_id)
                
                self.log_message(f"Matching {name1} ({addr1[0]}) and {name} ({addr[0]})", "SUCCESS")
                self.stats['successful_matches'] += 1
                
                try:
                    # Send peer info to both clients
                    conn1.send(f"{pubkey}:{addr[0]}:{name}".encode())
                    conn.send(f"{pubkey1}:{addr1[0]}:{name1}".encode())
                    
                    # Remove from active connections
                    if conn in self.connections:
                        del self.connections[conn]
                    if conn1 in self.connections:
                        del self.connections[conn1]
                        
                except Exception as e:
                    self.log_message(f"Failed to send to both clients: {str(e)}", "ERROR")
                    self.stats['failed_connections'] += 1
                    conn1.close()
                    conn.close()
                    
        except Exception as e:
            self.log_message(f"Client handling error: {str(e)}", "ERROR")
            self.stats['failed_connections'] += 1
        finally:
            # Clean up if connection still exists
            if conn in self.connections:
                del self.connections[conn]
                
    def update_ui_thread(self):
        """Update UI elements periodically"""
        self.update_statistics()
        self.update_rooms_display()
        
        # Schedule next update
        self.root.after(1000, self.update_ui_thread)
        
    def update_statistics(self):
        """Update statistics display"""
        self.total_conn_card['value_label'].config(text=str(self.stats['total_connections']))
        self.matches_card['value_label'].config(text=str(self.stats['successful_matches']))
        self.failed_card['value_label'].config(text=str(self.stats['failed_connections']))
        self.active_rooms_card['value_label'].config(text=str(len(self.rooms)))
        
        # Update uptime
        if self.stats['server_start_time'] and self.is_running:
            uptime = datetime.now() - self.stats['server_start_time']
            uptime_str = str(uptime).split('.')[0]  # Remove microseconds
            self.uptime_card['value_label'].config(text=uptime_str)
        else:
            self.uptime_card['value_label'].config(text="00:00:00")
            
    def update_rooms_display(self):
        """Update active rooms display"""
        # Clear existing items
        for item in self.rooms_tree.get_children():
            self.rooms_tree.delete(item)
            
        # Add current rooms
        for room_id, (pubkey, conn, addr, name, timestamp) in self.rooms.items():
            wait_time = datetime.now() - timestamp
            wait_time_str = str(wait_time).split('.')[0]  # Remove microseconds
            
            self.rooms_tree.insert('', 'end', values=(
                room_id,
                name,
                addr[0],
                str(pubkey)[:20] + "..." if len(str(pubkey)) > 20 else str(pubkey),
                wait_time_str
            ))
            
    def clear_logs(self):
        """Clear the logs display"""
        self.logs_text.config(state=tk.NORMAL)
        self.logs_text.delete(1.0, tk.END)
        self.logs_text.config(state=tk.DISABLED)
        
    def apply_settings(self):
        """Apply new server settings"""
        if self.is_running:
            messagebox.showwarning("Warning", "Stop the server before changing settings")
            return
            
        try:
            new_host = self.host_entry.get().strip()
            new_port = int(self.port_entry.get().strip())
            
            self.host = new_host
            self.port = new_port
            
            self.server_info.config(text=f"Host: {self.host} | Port: {self.port}")
            self.log_message(f"Settings updated - Host: {self.host}, Port: {self.port}")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")
            
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self.stop_server()
        self.root.destroy()
        
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MediatorServerGUI()
    app.run()