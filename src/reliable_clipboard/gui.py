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
        self.root.title("📋 Clipboard Manager")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        self.root.minsize(650, 480)
        
        # Beautiful light theme
        self.c = {
            'bg': '#f0f4f8',
            'white': '#ffffff',
            'primary': '#6366f1',
            'primary_hover': '#4f46e5',
            'success': '#10b981',
            'danger': '#ef4444',
            'text': '#1e293b',
            'text_light': '#64748b',
            'border': '#e2e8f0',
            'hover': '#f1f5f9',
        }
        
        self.root.configure(bg=self.c['bg'])
        
        # Set icon
        if platform.system() == 'Windows':
            try:
                from pathlib import Path
                import sys
                p = Path(sys._MEIPASS) / 'assets' / 'clipboard.ico' if getattr(sys, 'frozen', False) else Path(__file__).parent / 'assets' / 'clipboard.ico'
                if p.exists():
                    self.root.iconbitmap(str(p))
            except:
                pass
        
        self.db_path = db_path
        try:
            self.storage = StorageManager(db_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect: {e}")
            self.root.destroy()
            return

        self.monitor = None
        self.monitoring = True
        
        # Tray
        self.tray = None
        self._setup_tray()
        
        self._build_ui()
        self._refresh()
        self._auto_refresh()
        self._start_monitor()

    def _setup_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            img = Image.new('RGB', (64, 64), self.c['primary'])
            d = ImageDraw.Draw(img)
            d.rectangle((16, 16, 48, 48), fill='white')
            
            self.tray = pystray.Icon("rc", img, "📋 Clipboard", (
                pystray.MenuItem("Show", lambda _: self._show_tray()),
                pystray.MenuItem("Exit", lambda _: self._quit_tray())
            ))
            threading.Thread(target=self.tray.run, daemon=True).start()
        except:
            pass

    def _show_tray(self):
        if self.tray:
            self.tray.visible = False
        self.root.deiconify()

    def _quit_tray(self):
        if self.tray:
            self.tray.stop()
        self.root.quit()

    def _round(self, widget, radius=12, color=None):
        """Apply round corners effect"""
        try:
            widget.config(bg=color or self.c['white'])
        except:
            pass

    def _build_ui(self):
        # Main padding
        main = tk.Frame(self.root, bg=self.c['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ===== HEADER =====
        header = tk.Frame(main, bg=self.c['bg'])
        header.pack(fill=tk.X, pady=(0, 15))
        
        # Logo + Title
        title_box = tk.Frame(header, bg=self.c['bg'])
        title_box.pack(side=tk.LEFT)
        
        tk.Label(title_box, text="📋", font=("Segoe UI", 28), bg=self.c['bg']).pack(side=tk.LEFT)
        
        title_text = tk.Frame(title_box, bg=self.c['bg'])
        title_text.pack(side=tk.LEFT, padx=(10, 0))
        
        tk.Label(title_text, text="Clipboard Manager", font=("Segoe UI", 20, "bold"),
                bg=self.c['bg'], fg=self.c['text']).pack(anchor=tk.W)
        
        tk.Label(title_text, text="Copy, paste, and manage your clipboard history",
                font=("Segoe UI", 10), bg=self.c['bg'], fg=self.c['text_light']).pack(anchor=tk.W)
        
        # Status badge
        self.status_badge = tk.Frame(header, bg=self.c['success'], padx=12, pady=6)
        self.status_badge.pack(side=tk.RIGHT)
        
        self.status_dot = tk.Label(self.status_badge, text="●", font=("Segoe UI", 12),
                                   fg=self.c['white'], bg=self.c['success'])
        self.status_dot.pack(side=tk.LEFT, padx=(0, 5))
        
        self.status_text = tk.Label(self.status_badge, text="Active", font=("Segoe UI", 10, "bold"),
                                    fg=self.c['white'], bg=self.c['success'])
        self.status_text.pack(side=tk.LEFT)
        
        # ===== SEARCH =====
        search_box = tk.Frame(main, bg=self.c['white'], padx=4, pady=4)
        search_box.pack(fill=tk.X, pady=(0, 15))
        
        # Round corners effect
        style = ttk.Style()
        style.configure("Search.TEntry", fieldbackground=self.c['white'], borderwidth=0)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self._refresh())
        
        search_entry = tk.Entry(search_box, textvariable=self.search_var, font=("Segoe UI", 12),
                              bg=self.c['white'], fg=self.c['text'], relief=tk.FLAT, bd=0,
                              insertbackground=self.c['primary'])
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(10, 0))
        
        search_entry.insert(0, "🔍 Search clips...")
        search_entry.bind("<FocusIn>", lambda e: (search_entry.delete(0, tk.END) if search_entry.get() == "🔍 Search clips..." else None, search_entry.config(fg=self.c['text'])))
        search_entry.bind("<FocusOut>", lambda e: (search_entry.insert(0, "🔍 Search clips...") if not search_entry.get() else None, search_entry.config(fg=self.c['text_light'])))
        
        # Toggle button
        self.toggle_btn = tk.Button(search_box, text="⏸️", font=("Segoe UI", 14),
                                  command=self._toggle_monitoring, bg=self.c['white'],
                                  fg=self.c['text'], relief=tk.FLAT, bd=0, padx=12,
                                  cursor="hand2", activebackground=self.c['hover'])
        self.toggle_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # ===== LIST =====
        list_box = tk.Frame(main, bg=self.c['white'])
        list_box.pack(fill=tk.BOTH, expand=True)
        
        # Configure treeview style FIRST
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=self.c['white'], foreground=self.c['text'],
                      fieldbackground=self.c['white'], rowheight=48, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=self.c['primary'], foreground="white",
                      font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", self.c['primary'])])
        
        self.tree = ttk.Treeview(list_box, columns=("id", "type", "content", "time"), 
                                show="", selectmode="browse")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("type", width=60, anchor=tk.CENTER)
        self.tree.column("time", width=70, anchor=tk.CENTER)
        self.tree.column("content", stretch=True)
        
        scrollbar = tk.Scrollbar(list_box, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", lambda e: self._copy())
        
        # ===== BUTTONS =====
        btns = tk.Frame(main, bg=self.c['bg'])
        btns.pack(fill=tk.X, pady=(15, 0))
        
        # Nice rounded buttons
        self._make_btn(btns, "📋 Copy", self._copy, self.c['primary'])
        self._make_btn(btns, "🗑️ Delete", self._delete, self.c['hover'])
        self._make_btn(btns, "🔄 Refresh", self._refresh, self.c['hover'])
        
        tk.Frame(btns, bg=self.c['bg']).pack(side=tk.LEFT, expand=True)
        
        self._make_btn(btns, "🧹 Clear All", self._clear, self.c['danger'])
        
        # Shortcuts
        self.root.bind("<Delete>", lambda e: self._delete())
        self.root.bind("<Return>", lambda e: self._copy())
        self.root.bind("<F5>", lambda e: self._refresh())
        self.root.bind("<Escape>", lambda e: self.search_var.set(""))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _make_btn(self, parent, text, cmd, bg):
        btn = tk.Button(parent, text=text, command=cmd,
                       font=("Segoe UI", 10, "bold"), bg=bg, fg=self.c['text'] if bg == self.c['hover'] else "white",
                       relief=tk.FLAT, bd=0, padx=18, pady=8, cursor="hand2",
                       activebackground=self.c['primary_hover'] if bg == self.c['primary'] else self.c['border'])
        btn.pack(side=tk.LEFT, padx=(0, 8))

    def _refresh(self):
        try:
            q = self.search_var.get()
            clips = self.storage.search_clips(q) if q and "Search" not in q else self.storage.get_recent_clips(100)
            
            for i in self.tree.get_children():
                self.tree.delete(i)
            
            for c in clips:
                ct = c.get('clip_type', 'text')
                content = c['content']
                
                if ct == 'image':
                    typ, txt = "🖼️", "Image"
                elif ct == 'file':
                    files = content.split('\n')
                    typ, txt = "📁", f"{len(files)} files"
                else:
                    typ, txt = "📝", content[:55] + "..." if len(content) > 55 else content
                
                self.tree.insert("", tk.END, values=(c['id'], typ, txt,
                               datetime.fromtimestamp(c['timestamp']).strftime('%H:%M')))
        except Exception as e:
            logger.error(f"Error: {e}")

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
            content = next((x['content'] for x in clips if x['id'] == clip_id), "")
            pyperclip.copy(content)
            self._toast("✅ Copied!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        if messagebox.askyesno("🗑️ Delete", "Delete this clip?"):
            try:
                self.storage.delete_clip(self.tree.item(sel)['values'][0])
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _clear(self):
        if messagebox.askyesno("🧹 Clear All", "Clear ALL history? This cannot be undone!"):
            try:
                self.storage.clear_history()
                self._refresh()
                self._toast("🗑️ Cleared!")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _toast(self, msg):
        t = tk.Toplevel(self.root)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        x = self.root.winfo_screenwidth() // 2 - 70
        y = self.root.winfo_screenheight() - 80
        t.geometry(f"140x35+{x}+{y}")
        t.configure(bg=self.c['success'])
        tk.Label(t, text=msg, font=("Segoe UI", 10, "bold"), bg=self.c['success'], 
                fg="white").pack(expand=True)
        t.after(1200, t.destroy)

    def _toggle_monitoring(self):
        self.monitoring = not self.monitoring
        if self.monitoring:
            self._start_monitor()
            self.status_badge.config(bg=self.c['success'])
            self.status_dot.config(text="●", fg="white", bg=self.c['success'])
            self.status_text.config(text="Active", bg=self.c['success'], fg="white")
            self.toggle_btn.config(text="⏸️")
        else:
            self._stop_monitor()
            self.status_badge.config(bg=self.c['text_light'])
            self.status_dot.config(text="○", fg="white", bg=self.c['text_light'])
            self.status_text.config(text="Paused", bg=self.c['text_light'], fg="white")
            self.toggle_btn.config(text="▶️")

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
        if self.tray:
            self.root.withdraw()
            self.tray.visible = True
        else:
            self._quit_tray()


def start_gui(db_path: str):
    root = tk.Tk()
    ClipboardApp(root, db_path)
    root.mainloop()
