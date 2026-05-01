#!/usr/bin/env python3
"""
OpenClaw Pro GUI - Desktop application interface
Built with Tkinter for cross-platform compatibility
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
from pathlib import Path
from datetime import datetime
import json


class OpenClawGUI:
    """GUI for OpenClaw Pro"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OpenClaw Pro 🦅")
        self.root.geometry("1200x800")

        # Message queue for thread-safe updates
        self.message_queue = queue.Queue()

        # Agent instance (will be set later)
        self.agent = None

        # Setup UI
        self.setup_ui()

        # Start queue processor
        self.process_queue()

    def setup_ui(self):
        """Setup the user interface"""

        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self.new_session)
        file_menu.add_command(label="Load Session", command=self.load_session)
        file_menu.add_command(label="Save Session", command=self.save_session)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Open Memory Vault", command=self.open_memory_vault)
        tools_menu.add_command(label="View Business Plans", command=self.view_business_plans)
        tools_menu.add_command(label="Settings", command=self.open_settings)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="About", command=self.show_about)

        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Top bar with status
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.status_label = ttk.Label(top_frame, text="🦅 OpenClaw Pro - Ready", font=("Arial", 12, "bold"))
        self.status_label.pack(side=tk.LEFT)

        self.model_label = ttk.Label(top_frame, text="Model: qwen2.5-coder:7b", font=("Arial", 9))
        self.model_label.pack(side=tk.RIGHT)

        # Main content area with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Chat tab
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="💬 Chat")
        self.setup_chat_tab()

        # Projects tab
        self.projects_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.projects_frame, text="📁 Projects")
        self.setup_projects_tab()

        # Memory tab
        self.memory_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.memory_frame, text="🧠 Memory")
        self.setup_memory_tab()

        # Tools tab
        self.tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tools_frame, text="🔧 Tools")
        self.setup_tools_tab()

    def setup_chat_tab(self):
        """Setup chat interface tab"""
        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.rowconfigure(0, weight=1)

        # Chat history display
        self.chat_display = scrolledtext.ScrolledText(
            self.chat_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            state=tk.DISABLED
        )
        self.chat_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # Configure tags for styling
        self.chat_display.tag_config("user", foreground="#0066cc", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("assistant", foreground="#00aa00", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("system", foreground="#cc6600", font=("Arial", 9, "italic"))
        self.chat_display.tag_config("tool", foreground="#9900cc", font=("Arial", 9))

        # Input area
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=("Arial", 10),
            height=3
        )
        self.input_text.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.input_text.bind("<Control-Return>", lambda e: self.send_message())

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=0, column=1)

        self.send_button = ttk.Button(button_frame, text="Send 🚀", command=self.send_message)
        self.send_button.pack(pady=(0, 5))

        self.clear_button = ttk.Button(button_frame, text="Clear 🗑️", command=self.clear_chat)
        self.clear_button.pack()

    def setup_projects_tab(self):
        """Setup projects management tab"""
        self.projects_frame.columnconfigure(0, weight=1)
        self.projects_frame.rowconfigure(0, weight=1)

        # Projects list
        projects_list_frame = ttk.LabelFrame(self.projects_frame, text="Active Projects", padding="10")
        projects_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        self.projects_listbox = tk.Listbox(projects_list_frame, font=("Arial", 10))
        self.projects_listbox.pack(fill=tk.BOTH, expand=True)

        # Project actions
        actions_frame = ttk.Frame(self.projects_frame)
        actions_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Button(actions_frame, text="New Project", command=self.new_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Open Project", command=self.open_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(actions_frame, text="Refresh", command=self.refresh_projects).pack(side=tk.LEFT, padx=2)

    def setup_memory_tab(self):
        """Setup memory/knowledge tab"""
        self.memory_frame.columnconfigure(0, weight=1)
        self.memory_frame.rowconfigure(0, weight=1)

        # Memory stats
        stats_frame = ttk.LabelFrame(self.memory_frame, text="Memory Stats", padding="10")
        stats_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.memory_stats_label = ttk.Label(
            stats_frame,
            text="Conversations: 0 | Projects: 0 | Code Snippets: 0 | Learnings: 0"
        )
        self.memory_stats_label.pack()

        # Recent items
        recent_frame = ttk.LabelFrame(self.memory_frame, text="Recent Memory Items", padding="10")
        recent_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        recent_frame.columnconfigure(0, weight=1)
        recent_frame.rowconfigure(0, weight=1)

        self.memory_listbox = tk.Listbox(recent_frame, font=("Arial", 10))
        self.memory_listbox.pack(fill=tk.BOTH, expand=True)

        # Actions
        memory_actions = ttk.Frame(self.memory_frame)
        memory_actions.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Button(memory_actions, text="Open Vault", command=self.open_memory_vault).pack(side=tk.LEFT, padx=2)
        ttk.Button(memory_actions, text="Search", command=self.search_memory).pack(side=tk.LEFT, padx=2)
        ttk.Button(memory_actions, text="Refresh", command=self.refresh_memory).pack(side=tk.LEFT, padx=2)

    def setup_tools_tab(self):
        """Setup tools and utilities tab"""
        tools_grid = ttk.Frame(self.tools_frame, padding="10")
        tools_grid.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Tool buttons in grid layout
        tools = [
            ("📖 Read File", self.tool_read_file),
            ("✍️ Write File", self.tool_write_file),
            ("🔍 Search Files", self.tool_search_files),
            ("📂 List Directory", self.tool_list_directory),
            ("⚡ Run Command", self.tool_run_command),
            ("🐍 Python REPL", self.tool_python_repl),
            ("🌐 Web Search", self.tool_web_search),
            ("🔗 Browse URL", self.tool_browse_url),
            ("💼 Business Plan", self.tool_business_plan),
        ]

        row, col = 0, 0
        for label, command in tools:
            btn = ttk.Button(tools_grid, text=label, command=command, width=20)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E))
            col += 1
            if col > 2:
                col = 0
                row += 1

    def add_chat_message(self, role: str, content: str):
        """Add message to chat display"""
        self.chat_display.config(state=tk.NORMAL)

        timestamp = datetime.now().strftime("%H:%M:%S")

        if role == "user":
            self.chat_display.insert(tk.END, f"\n[{timestamp}] ", "system")
            self.chat_display.insert(tk.END, "👤 You:\n", "user")
        elif role == "assistant":
            self.chat_display.insert(tk.END, f"\n[{timestamp}] ", "system")
            self.chat_display.insert(tk.END, "🦅 OpenClaw:\n", "assistant")
        elif role == "tool":
            self.chat_display.insert(tk.END, f"\n[{timestamp}] ", "system")
            self.chat_display.insert(tk.END, "🔧 Tool:\n", "tool")
        else:
            self.chat_display.insert(tk.END, f"\n[{timestamp}] ", "system")
            self.chat_display.insert(tk.END, f"{role}:\n")

        self.chat_display.insert(tk.END, f"{content}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def send_message(self):
        """Send message to agent"""
        message = self.input_text.get("1.0", tk.END).strip()

        if not message:
            return

        # Clear input
        self.input_text.delete("1.0", tk.END)

        # Add to chat
        self.add_chat_message("user", message)

        # Disable send button
        self.send_button.config(state=tk.DISABLED)
        self.status_label.config(text="🦅 OpenClaw Pro - Thinking...")

        # Process in background thread
        thread = threading.Thread(target=self.process_message, args=(message,))
        thread.daemon = True
        thread.start()

    def process_message(self, message: str):
        """Process message in background thread"""
        try:
            # TODO: Call actual agent
            # For now, simulate response
            import time
            time.sleep(1)

            response = f"This is a demo response to: {message}\n\nFull agent integration coming soon!"

            # Queue response for main thread
            self.message_queue.put(("assistant", response))
            self.message_queue.put(("status", "Ready"))

        except Exception as e:
            self.message_queue.put(("assistant", f"Error: {e}"))
            self.message_queue.put(("status", "Error"))

    def process_queue(self):
        """Process message queue"""
        try:
            while True:
                msg_type, content = self.message_queue.get_nowait()

                if msg_type in ["user", "assistant", "tool"]:
                    self.add_chat_message(msg_type, content)
                elif msg_type == "status":
                    self.status_label.config(text=f"🦅 OpenClaw Pro - {content}")
                    if content == "Ready":
                        self.send_button.config(state=tk.NORMAL)

        except queue.Empty:
            pass

        # Schedule next check
        self.root.after(100, self.process_queue)

    def clear_chat(self):
        """Clear chat history"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)

    # Stub methods for functionality
    def new_session(self):
        messagebox.showinfo("New Session", "Starting new session...")

    def load_session(self):
        messagebox.showinfo("Load Session", "Load session functionality coming soon!")

    def save_session(self):
        messagebox.showinfo("Save Session", "Save session functionality coming soon!")

    def open_memory_vault(self):
        vault_path = Path("./openclaw_memory")
        if vault_path.exists():
            import subprocess, sys
            if sys.platform == "darwin":
                subprocess.run(["open", str(vault_path)])
            elif sys.platform == "win32":
                os.startfile(str(vault_path))
            else:
                subprocess.run(["xdg-open", str(vault_path)])
        else:
            messagebox.showinfo("Memory Vault", "Memory vault not found. It will be created on first use.")

    def view_business_plans(self):
        messagebox.showinfo("Business Plans", "Business plans viewer coming soon!")

    def open_settings(self):
        messagebox.showinfo("Settings", "Settings panel coming soon!")

    def show_docs(self):
        messagebox.showinfo("Documentation", "Opening documentation...")

    def show_about(self):
        messagebox.showinfo(
            "About OpenClaw Pro",
            "OpenClaw Pro 🦅\n\n"
            "AI Co-Founder for Coding & Business\n\n"
            "Features:\n"
            "- Full-stack coding agent\n"
            "- Business strategy & planning\n"
            "- Web research capabilities\n"
            "- Discord bot integration\n"
            "- Persistent memory (Obsidian)\n"
            "- Secure & private\n\n"
            "Version: 1.0.0\n"
            "License: MIT"
        )

    def new_project(self):
        messagebox.showinfo("New Project", "New project wizard coming soon!")

    def open_project(self):
        messagebox.showinfo("Open Project", "Open project functionality coming soon!")

    def refresh_projects(self):
        messagebox.showinfo("Refresh", "Refreshing projects list...")

    def refresh_memory(self):
        messagebox.showinfo("Refresh", "Refreshing memory items...")

    def search_memory(self):
        messagebox.showinfo("Search", "Memory search coming soon!")

    # Tool methods
    def tool_read_file(self):
        filename = filedialog.askopenfilename(title="Select file to read")
        if filename:
            self.input_text.insert(tk.END, f"Read file: {filename}")

    def tool_write_file(self):
        messagebox.showinfo("Write File", "Write file tool coming soon!")

    def tool_search_files(self):
        messagebox.showinfo("Search Files", "Search files tool coming soon!")

    def tool_list_directory(self):
        directory = filedialog.askdirectory(title="Select directory to list")
        if directory:
            self.input_text.insert(tk.END, f"List directory: {directory}")

    def tool_run_command(self):
        messagebox.showinfo("Run Command", "Command runner coming soon!")

    def tool_python_repl(self):
        messagebox.showinfo("Python REPL", "Python REPL coming soon!")

    def tool_web_search(self):
        messagebox.showinfo("Web Search", "Web search tool coming soon!")

    def tool_browse_url(self):
        messagebox.showinfo("Browse URL", "URL browser coming soon!")

    def tool_business_plan(self):
        messagebox.showinfo("Business Plan", "Business plan generator coming soon!")

    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = OpenClawGUI()
    app.run()


if __name__ == "__main__":
    main()
