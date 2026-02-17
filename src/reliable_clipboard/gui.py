import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
from datetime import datetime
from typing import Optional
import platform

from .storage import StorageManager
from .clipboard_monitor import ClipboardMonitor
from .clip_history import ClipHistory
import pyperclip

logger = logging.getLogger(__name__)


class ClipboardApp:
    def __init__(self, root: tk.Tk, db_path: str):
        self.root = root
        self.root.title("Reliable Clipboard")
        self.root.geometry("850x600")
        self.root.resizable(True, True)
        self.root.minsize(600, 450)
        
        # Modern dark theme
        self.colors = {
            'bg': '#1e1e2e',
            'surface': '#2a2a3e',
            'surface_hover': '#3a3a4e',
            'primary': '#7c3aed',
            'primary_hover': '#8b5cf6',
            'accent': '#06b6d4',
            'text': '#f8fafc',
            'text_muted': '#94a3b8',
            'border': '#3f3f5a',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Set icon
        if platform.system() == 'Windows':
            self._set_icon()
        
        self.db_path = db_path
        try:
            self.storage = StorageManager(db_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
            self.root.destroy()
            return

        self.monitor: Optional[ClipboardMonitor] = None
        self.monitoring = True
        
        # System tray
        self.tray_icon = None
        self._setup_tray()
        
        self._build_ui()
        self._refresh()
        
        # Auto refresh
        self._auto_refresh()
        
        # Start monitoring
        self._start_monitor()

    def _set_icon(self):
        try:
            from pathlib import Path
            import sys
            path = Path(sys._MEIPASS) / 'assets' / 'clipboard.ico' if getattr(sys, 'frozen', False) else Path(__file__).parent / 'assets' / 'clipboard.ico'
            if path.exists():
                self.root.iconbitmap(str(path))
        except:
            pass

    def _setup_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Create simple icon
            img = Image.new('RGB', (64, 64), self.colors['primary'])
            d = ImageDraw.Draw(img)
            d.rectangle((16, 16, 48, 48), fill='white')
            
            self.tray_icon = pystray.Icon("rc", img, "Reliable Clipboard", (
                pystray.MenuItem("Show", self._show),
                pystray.MenuItem("Exit", self._quit)
            ))
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except:
            pass

    def _show(self):
        if self.tray_icon:
            self.tray_icon.visible = False
        self.root.deiconify()

    def _quit(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def _build_ui(self):
        # Main container
        main = tk.Frame(self.root, bg=self.colors['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header = tk.Frame(main, bg=self.colors['bg'])
        header.pack(fill=tk.X, pady=(0, 15))
        
        # Title
        tk.Label(header, text="📋", font=("Segoe UI", 24), bg=self.colors['bg']).pack(side=tk.LEFT)
        tk.Label(header, text="Reliable Clipboard", font=("Segoe UI", 18, "bold"), 
                fg=self.colors['text'], bg=self.colors['bg']).pack(side=tk.LEFT, padx=(10, 0))
        
        # Status indicator
        self.status_frame = tk.Frame(header, bg=self.colors['surface'], padx=12, pady=6)
        self.status_frame.pack(side=tk.RIGHT)
        self.status_label = tk.Label(self.status_frame, text="●", font=("Segoe UI", 12), 
                                    fg=self.colors['success'], bg=self.colors['surface'])
        self.status_label.pack(side=tk.LEFT)
        tk.Label(self.status_frame, text="Monitoring", font=("Segoe UI", 10), 
                 fg=self.colors['text_muted'], bg=self.colors['surface']).pack(side=tk.LEFT, padx=(6, 0))
        
        # Search box
        search_box = tk.Frame(main, bg=self.colors['surface'], padx=15, pady=10)
        search_box.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(search_box, text="🔍", font=("Segoe UI", 14), bg=self.colors['surface']).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self._refresh())
        
        self.search_entry = tk.Entry(search_box, textvariable=self.search_var, font=("Segoe UI", 12),
                                   bg=self.colors['bg'], fg=self.colors['text'], relief=tk.FLAT, bd=0,
                                   insertbackground=self.colors['accent'])
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        self.search_entry.insert(0, "Search clips...")
        self.search_entry.bind("<FocusIn>", lambda e: self._search_focus(True))
        self.search_entry.bind("<FocusOut>", lambda e: self._search_focus(False))
        
        # Toggle button
        self.toggle_btn = tk.Button(search_box, text="⏸", font=("Segoe UI", 14),
                                   command=self._toggle_monitor, bg=self.colors['surface'], 
                                   fg=self.colors['text'], relief=tk.FLAT, bd=0, padx=10,
                                   cursor="hand2", activebackground=self.colors['surface_hover'])
        self.toggle_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # List container
        list_frame = tk.Frame(main, bg=self.colors['surface'], padx=1, pady=1)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        self.tree = ttk.Treeview(list_frame, columns=("id", "type", "content", "time"), 
                                show="", style="Modern.Treeview", selectmode="browse")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("type", width=70, anchor=tk.CENTER)
        self.tree.column("content", stretch=True)
        self.tree.column("time", width=80, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", lambda e: self._copy())
        
        # Style
        style = ttk.Style()
        style.configure("Modern.Treeview", background=self.colors['surface'], 
                      foreground=self.colors['text'], fieldbackground=self.colors['surface'],
                      rowheight=42, font=("Segoe UI", 10))
        style.configure("Modern.Treeview.Heading", background=self.colors['primary'],
                      foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Modern.Treeview", background=[("selected", self.colors['primary'])])
        
        # Buttons
        btns = tk.Frame(main, bg=self.colors['bg'], pady=(15, 0))
        btns.pack(fill=tk.X)
        
        self._btn(btns, "📋 Copy", self._copy, self.colors['primary'])
        self._btn(btns, "🗑️ Delete", self._delete, self.colors['surface'])
        self._btn(btns, "🔄 Refresh", self._refresh, self.colors['surface'])
        
        tk.Frame(btns, bg=self.colors['bg']).pack(side=tk.LEFT, expand=True)
        
        self._btn(btns, "🧹 Clear All", self._clear, self.colors['danger'])
        
        # Keyboard shortcuts
        self.root.bind("<Delete>", lambda e: self._delete())
        self.root.bind("<Return>", lambda e: self._copy())
        self.root.bind("<F5>", lambda e: self._refresh())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _btn(self, parent, text, command, bg):
        btn = tk.Button(parent, text=text, command=command, font=("Segoe UI", 10, "bold"),
                       bg=bg, fg="white", relief=tk.FLAT, bd=0, padx=16, pady=8,
                       cursor="hand2", activebackground=self.colors['primary_hover'])
        btn.pack(side=tk.LEFT, padx=(0, 8))

    def _search_focus(self, in_focus):
        if in_focus and self.search_entry.get() == "Search clips...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=self.colors['text'])
        elif not in_focus and self.search_entry.get() == "":
            self.search_entry.insert(0, "Search clips...")
            self.search_entry.config(fg=self.colors['text_muted'])

    def _refresh(self):
        try:
            query = self.search_var.get()
            clips = self.storage.search_clips(query) if query and query != "Search clips..." else self.storage.get_recent_clips(100)
            
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            for clip in clips:
                ct = clip.get('clip_type', 'text')
                content = clip['content']
                
                if ct == 'image':
                    typ, txt = "🖼️", "Image"
                elif ct == 'file':
                    files = content.split('\n')
                    typ, txt = "📁", f"{len(files)} file(s)"
                else:
                    typ, txt = "📝", content[:60] + "..." if len(content) > 60 else content
                
                self.tree.insert("", tk.END, values=(clip['id'], typ, txt, 
                               datetime.fromtimestamp(clip['timestamp']).strftime('%H:%M')))
        except Exception as e:
            logger.error(f"Refresh error: {e}")

    def _auto_refresh(self):
        self._refresh()
        self.root.after(2000, self._auto_refresh)

    def _copy(self):
        sel = self.tree.selection()
        if not sel:
            return
        
        clip_id = self.tree.item(sel)['values'][0]
        
        try:
            clips = self.storage.get_recent_clips(1000)
            content = next((c['content'] for c in clips if c['id'] == clip_id), "")
            pyperclip.copy(content)
            self._toast("✅ Copied!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        
        if messagebox.askyesno("Delete", "Delete this clip?"):
            try:
                self.storage.delete_clip(self.tree.item(sel)['values'][0])
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _clear(self):
        if messagebox.askyesno("Clear All", "Clear ALL history? This cannot be undone!"):
            try:
                self.storage.clear_history()
                self._refresh()
                self._toast("🗑️ Cleared!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _toast(self, msg):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        x = self.root.winfo_screenwidth() // 2 - 60
        y = self.root.winfo_screenheight() - 80
        toast.geometry(f"120x35+{x}+{y}")
        toast.configure(bg=self.colors['success'])
        tk.Label(toast, text=msg, font=("Segoe UI", 10, "bold"), bg=self.colors['success'], 
                fg="white").pack(expand=True)
        toast.after(1200, toast.destroy)

    def _toggle_monitor(self):
        self.monitoring = not self.monitoring
        if self.monitoring:
            self._start_monitor()
            self.status_label.config(text="●", fg=self.colors['success'])
            self.toggle_btn.config(text="⏸")
        else:
            self._stop_monitor()
            self.status_label.config(text="○", fg=self.colors['text_muted'])
            self.toggle_btn.config(text="▶")

    def _start_monitor(self):
        if self.monitor:
            return
        history = ClipHistory(storage_manager=self.storage)
        
        def on_change(content, ct):
            self.root.after(0, self._refresh)
            try:
                history.add_clip(content, ct)
            except:
                pass
        
        self.monitor = ClipboardMonitor(on_change=on_change, check_interval=0.5)
        self.monitor.start()

    def _stop_monitor(self):
        if self.monitor:
            self.monitor.stop()
            self.monitor = None

    def _on_close(self):
        if self.tray_icon:
            self.root.withdraw()
            self.tray_icon.visible = True
        else:
            self._quit()


def start_gui(db_path: str):
    root = tk.Tk()
    ClipboardApp(root, db_path)
    root.mainloop()
