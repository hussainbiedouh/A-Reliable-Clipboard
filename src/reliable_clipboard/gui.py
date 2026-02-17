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
        
        # Colors
        self.c = {
            'bg': '#f0f4f8',
            'white': '#ffffff',
            'primary': '#6366f1',
            'primary_hover': '#4f46e5',
            'success': '#10b981',
            'danger': '#ef4444',
            'danger_hover': '#dc2626',
            'text': '#1e293b',
            'text_light': '#64748b',
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
                pystray.MenuItem("Show", lambda _: self._show()),
                pystray.MenuItem("Exit", lambda _: self._quit())
            ))
            threading.Thread(target=self.tray.run, daemon=True).start()
        except:
            pass

    def _show(self):
        if self.tray:
            self.tray.visible = False
        self.root.deiconify()

    def _quit(self):
        if self.tray:
            self.tray.stop()
        self.root.quit()

    def _build_ui(self):
        # Main container
        main = tk.Frame(self.root, bg=self.c['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)
        
        # ===== HEADER =====
        header = tk.Frame(main, bg=self.c['bg'])
        header.pack(fill=tk.X, pady=(0, 20))
        
        # Title
        title_box = tk.Frame(header, bg=self.c['bg'])
        title_box.pack(side=tk.LEFT)
        
        tk.Label(title_box, text="📋", font=("Segoe UI", 32), bg=self.c['bg']).pack(side=tk.LEFT)
        
        title_text = tk.Frame(title_box, bg=self.c['bg'])
        title_text.pack(side=tk.LEFT, padx=(12, 0))
        
        tk.Label(title_text, text="Clipboard Manager", font=("Segoe UI", 22, "bold"),
                bg=self.c['bg'], fg=self.c['text']).pack(anchor=tk.W)
        
        tk.Label(title_text, text="Copy, paste, and manage your clipboard",
                font=("Segoe UI", 11), bg=self.c['bg'], fg=self.c['text_light']).pack(anchor=tk.W)
        
        # Status badge
        self.status_frame = tk.Frame(header, bg=self.c['success'], padx=16, pady=8)
        self.status_frame.pack(side=tk.RIGHT)
        self.status_frame.config(highlightthickness=0, relief=tk.FLAT)
        
        tk.Label(self.status_frame, text="●  Active", font=("Segoe UI", 11, "bold"),
                fg="white", bg=self.c['success']).pack()
        
        # Toggle button
        self.toggle_btn = tk.Button(header, text="⏸️", font=("Segoe UI", 14),
                                   command=self._toggle_monitoring, bg=self.c['white'],
                                   fg=self.c['text'], relief=tk.FLAT, bd=0, padx=12, pady=8,
                                   cursor="hand2", highlightthickness=0)
        self.toggle_btn.pack(side=tk.RIGHT, padx=(12, 0))
        
        # ===== SEARCH =====
        search_box = tk.Frame(main, bg=self.c['white'], padx=16, pady=12)
        search_box.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(search_box, text="🔍", font=("Segoe UI", 14), bg=self.c['white']).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *_: self._refresh())
        
        self.search_entry = tk.Entry(search_box, textvariable=self.search_var, font=("Segoe UI", 12),
                              bg=self.c['white'], fg=self.c['text'], relief=tk.FLAT, bd=0,
                              insertbackground=self.c['primary'])
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 0))
        self.search_entry.insert(0, "Search clips...")
        self.search_entry.bind("<FocusIn>", lambda e: self._search_focus(True))
        self.search_entry.bind("<FocusOut>", lambda e: self._search_focus(False))
        
        # ===== LIST =====
        list_box = tk.Frame(main, bg=self.c['white'])
        list_box.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        self.tree = ttk.Treeview(list_box, columns=("id", "type", "content", "time"), 
                                show="", selectmode="browse")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("type", width=60, anchor=tk.CENTER)
        self.tree.column("time", width=70, anchor=tk.CENTER)
        self.tree.column("content", stretch=True)
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="white", foreground=self.c['text'],
                      rowheight=48, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=self.c['primary'], foreground="white",
                      font=("Segoe UI", 10, "bold"), relief=tk.FLAT)
        style.map("Treeview", background=[("selected", self.c['primary'])])
        
        scrollbar = ttk.Scrollbar(list_box, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", lambda e: self._copy())
        
        # ===== BUTTONS =====
        btns = tk.Frame(main, bg=self.c['bg'])
        btns.pack(fill=tk.X, pady=(20, 0))
        
        # Use standard tk buttons with better styling
        self.btn_copy = tk.Button(btns, text="📋  Copy", command=self._copy,
                       font=("Segoe UI", 11, "bold"), bg=self.c['primary'], fg="white",
                       relief=tk.FLAT, bd=0, padx=20, pady=10, cursor="hand2",
                       activebackground=self.c['primary_hover'], activeforeground="white",
                       highlightthickness=0)
        self.btn_copy.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_delete = tk.Button(btns, text="🗑️  Delete", command=self._delete,
                       font=("Segoe UI", 11), bg=self.c['hover'], fg=self.c['text'],
                       relief=tk.FLAT, bd=0, padx=20, pady=10, cursor="hand2",
                       activebackground=self.c['border'], activeforeground=self.c['text'],
                       highlightthickness=0)
        self.btn_delete.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_refresh = tk.Button(btns, text="🔄  Refresh", command=self._refresh,
                       font=("Segoe UI", 11), bg=self.c['hover'], fg=self.c['text'],
                       relief=tk.FLAT, bd=0, padx=20, pady=10, cursor="hand2",
                       activebackground=self.c['border'], activeforeground=self.c['text'],
                       highlightthickness=0)
        self.btn_refresh.pack(side=tk.LEFT, padx=(0, 10))
        
        # Spacer - this keeps buttons visible
        spacer = tk.Frame(btns, bg=self.c['bg'])
        spacer.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.btn_clear = tk.Button(btns, text="🧹  Clear All", command=self._clear,
                       font=("Segoe UI", 11, "bold"), bg=self.c['danger'], fg="white",
                       relief=tk.FLAT, bd=0, padx=20, pady=10, cursor="hand2",
                       activebackground=self.c['danger_hover'], activeforeground="white",
                       highlightthickness=0)
        self.btn_clear.pack(side=tk.RIGHT)
        
        # Shortcuts
        self.root.bind("<Delete>", lambda e: self._delete())
        self.root.bind("<Return>", lambda e: self._copy())
        self.root.bind("<F5>", lambda e: self._refresh())
        self.root.bind("<Escape>", lambda e: self.search_var.set(""))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _search_focus(self, in_focus):
        if in_focus and self.search_entry.get() == "Search clips...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=self.c['text'])
        elif not in_focus and self.search_entry.get() == "":
            self.search_entry.insert(0, "Search clips...")
            self.search_entry.config(fg=self.c['text_light'])

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
        y = self.root.winfo_screenheight() - 100
        t.geometry(f"140x38+{x}+{y}")
        t.configure(bg=self.c['success'])
        
        tk.Label(t, text=msg, font=("Segoe UI", 10, "bold"), bg=self.c['success'], 
                fg="white").pack(expand=True, pady=8)
        
        t.after(1200, t.destroy)

    def _toggle_monitoring(self):
        self.monitoring = not self.monitoring
        if self.monitoring:
            self._start_monitor()
            self.status_frame.config(bg=self.c['success'])
            self.status_frame.winfo_children()[0].config(text="●  Active", bg=self.c['success'])
            self.toggle_btn.config(text="⏸️")
        else:
            self._stop_monitor()
            self.status_frame.config(bg=self.c['text_light'])
            self.status_frame.winfo_children()[0].config(text="○  Paused", bg=self.c['text_light'])
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
            self._quit()


def start_gui(db_path: str):
    root = tk.Tk()
    ClipboardApp(root, db_path)
    root.mainloop()
