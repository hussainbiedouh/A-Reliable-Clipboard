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


class RoundedButton(tk.Canvas):
    """Button with rounded corners"""
    def __init__(self, parent, text, command, bg="#6366f1", fg="white", 
                 hover_bg=None, width=100, height=36, radius=10, font=("Segoe UI", 10, "bold")):
        super().__init__(parent, width=width, height=height, 
                        bg=parent.cget('bg'), highlightthickness=0, cursor="hand2")
        
        self.command = command
        self.bg = bg
        self.fg = fg
        self.hover_bg = hover_bg or bg
        self.current_bg = bg
        self.width = width
        self.height = height
        self.radius = radius
        self.text = text
        self.font = font
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self._draw()
    
    def _draw(self):
        self.delete("all")
        r = self.radius
        w, h = self.width, self.height
        
        # Draw rounded rectangle using ovals and rectangles
        self.create_oval(0, 0, 2*r, 2*r, fill=self.current_bg, outline="")
        self.create_oval(w-2*r, 0, w, 2*r, fill=self.current_bg, outline="")
        self.create_oval(0, h-2*r, 2*r, h, fill=self.current_bg, outline="")
        self.create_oval(w-2*r, h-2*r, w, h, fill=self.current_bg, outline="")
        self.create_rectangle(r, 0, w-r, h, fill=self.current_bg, outline="")
        self.create_rectangle(0, r, w, h-r, fill=self.current_bg, outline="")
        
        # Text
        self.create_text(w//2, h//2, text=self.text, fill=self.fg, font=self.font)
    
    def _on_click(self, e):
        if self.command:
            self.command()
    
    def _on_enter(self, e):
        self.current_bg = self.hover_bg
        self._draw()
    
    def _on_leave(self, e):
        self.current_bg = self.bg
        self._draw()
    
    def set_colors(self, bg, fg, hover_bg=None):
        self.bg = bg
        self.fg = fg
        self.hover_bg = hover_bg or bg
        self.current_bg = bg
        self._draw()
    
    def set_text(self, text):
        self.text = text
        self._draw()


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
            'success_hover': '#059669',
            'danger': '#ef4444',
            'danger_hover': '#dc2626',
            'text': '#1e293b',
            'text_light': '#64748b',
            'hover': '#e2e8f0',
            'hover_btn': '#cbd5e1',
            'border': '#e2e8f0',
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
        # Main container with grid
        main = tk.Frame(self.root, bg=self.c['bg'])
        main.pack(fill=tk.BOTH, expand=True, padx=24, pady=24)
        main.grid_rowconfigure(0, weight=0)
        main.grid_rowconfigure(1, weight=0)
        main.grid_rowconfigure(2, weight=1)
        main.grid_rowconfigure(3, weight=0)
        main.grid_columnconfigure(0, weight=1)
        
        # ===== HEADER =====
        header = tk.Frame(main, bg=self.c['bg'])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
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
        
        # Merged status/toggle button (rounded)
        self.status_btn = RoundedButton(
            header, "●  Active", self._toggle_monitoring,
            bg=self.c['success'], hover_bg=self.c['success_hover'],
            width=110, height=36, radius=18
        )
        self.status_btn.pack(side=tk.RIGHT)
        
        # ===== SEARCH =====
        search_box = tk.Frame(main, bg=self.c['white'], padx=16, pady=12)
        search_box.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
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
        list_box.grid(row=2, column=0, sticky="nsew")
        
        # Treeview with material scrollbar
        self.tree = ttk.Treeview(list_box, columns=("id", "type", "content", "time"), 
                                show="", selectmode="browse")
        
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("type", width=60, anchor=tk.CENTER)
        self.tree.column("time", width=70, anchor=tk.CENTER)
        self.tree.column("content", stretch=True)
        
        # Material style for treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="white", foreground=self.c['text'],
                      rowheight=48, font=("Segoe UI", 10), borderwidth=0)
        style.configure("Treeview.Heading", background=self.c['primary'], foreground="white",
                      font=("Segoe UI", 10, "bold"), relief=tk.FLAT, borderwidth=0)
        style.map("Treeview", background=[("selected", self.c['primary'])])
        
        # Material scrollbar style
        style.configure("Vertical.TScrollbar", background=self.c['hover'], 
                       troughcolor=self.c['white'], borderwidth=0, arrowcolor=self.c['text'])
        style.map("Vertical.TScrollbar", background=[("active", self.c['primary'])])
        
        scrollbar = ttk.Scrollbar(list_box, orient=tk.VERTICAL, command=self.tree.yview, 
                                 style="Vertical.TScrollbar")
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", lambda e: self._copy())
        
        # ===== BUTTONS =====
        btns = tk.Frame(main, bg=self.c['bg'])
        btns.grid(row=3, column=0, sticky="ew", pady=(20, 0))
        
        # Rounded buttons
        RoundedButton(btns, "📋  Copy", self._copy, bg=self.c['primary'], 
                     hover_bg=self.c['primary_hover'], width=100, height=40, radius=12).pack(side=tk.LEFT, padx=(0, 10))
        
        RoundedButton(btns, "🗑️  Delete", self._delete, bg=self.c['hover'], 
                     fg=self.c['text'], hover_bg=self.c['hover_btn'], width=100, height=40, radius=12).pack(side=tk.LEFT, padx=(0, 10))
        
        RoundedButton(btns, "🔄  Refresh", self._refresh, bg=self.c['hover'], 
                     fg=self.c['text'], hover_bg=self.c['hover_btn'], width=110, height=40, radius=12).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Frame(btns, bg=self.c['bg']).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        RoundedButton(btns, "🧹  Clear All", self._clear, bg=self.c['danger'], 
                     hover_bg=self.c['danger_hover'], width=120, height=40, radius=12).pack(side=tk.RIGHT)
        
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
            self.status_btn.set_colors(self.c['success'], "white", self.c['success_hover'])
            self.status_btn.set_text("●  Active")
        else:
            self._stop_monitor()
            self.status_btn.set_colors(self.c['text_light'], "white", self.c['border'])
            self.status_btn.set_text("○  Paused")

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
