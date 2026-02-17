import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any
import platform

from .storage import StorageManager
from .clipboard_monitor import ClipboardMonitor
from .clip_history import ClipHistory
import pyperclip

logger = logging.getLogger(__name__)


class ModernColors:
    """Modern color palette"""
    # Gradients & Effects
    BG_GRADIENT_START = "#1a1a2e"
    BG_GRADIENT_END = "#16213e"
    CARD_BG = "#0f3460"
    CARD_HOVER = "#1a4a7a"
    
    # Accent colors
    PRIMARY = "#e94560"
    PRIMARY_HOVER = "#ff6b6b"
    SECONDARY = "#00d9ff"
    SUCCESS = "#00e676"
    WARNING = "#ffab00"
    ERROR = "#ff5252"
    
    # Text colors
    TEXT_WHITE = "#ffffff"
    TEXT_LIGHT = "#b8b8d1"
    TEXT_MUTED = "#6c6c8a"
    
    # UI Elements
    TOGGLE_ON = "#00e676"
    TOGGLE_OFF = "#4a4a6a"
    BORDER = "#2a2a4a"
    SHADOW = "#000000"
    
    # Emojis with colors
    EMOJI_COPY = "📋"
    EMOJI_DELETE = "🗑️"
    EMOJI_REFRESH = "🔄"
    EMOJI_CLEAR = "🧹"
    EMOJI_SEARCH = "🔍"
    EMOJI_MONITOR_ON = "🟢"
    EMOJI_MONITOR_OFF = "🔴"
    EMOJI_IMAGE = "🖼️"
    EMOJI_FILE = "📁"
    EMOJI_TEXT = "📝"
    EMOJI_CLIPBOARD = "📎"
    EMOJI_CHECK = "✅"
    EMOJI_WARNING = "⚠️"


class RoundButton(tk.Canvas):
    """Custom rounded button widget"""
    def __init__(self, parent, text, command, bg=ModernColors.PRIMARY, hover=ModernColors.PRIMARY_HOVER, 
                 fg=ModernColors.TEXT_WHITE, width=120, height=36, radius=18, font=("Segoe UI", 10, "bold")):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0)
        
        self.command = command
        self.bg = bg
        self.hover = hover
        self.fg = fg
        self.radius = radius
        self.width = width
        self.height = height
        
        self.btn_frame = tk.Frame(parent, bg=parent["bg"])
        
        self.btn = tk.Button(
            self.btn_frame,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            font=font,
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground=hover,
            activeforeground=fg,
            highlightthickness=0
        )
        
        # Round corners using canvas
        self.round_rectangle(0, 0, width, height, radius, fill=bg, outline="")
        self.btn.place(x=0, y=0, width=width, height=height)
        
        # Hover effects
        self.btn.bind("<Enter>", lambda e: self._on_hover(True))
        self.btn.bind("<Leave>", lambda e: self._on_hover(False))
    
    def round_rectangle(self, x1, y1, x2, y2, r, **kwargs):
        """Create rounded rectangle"""
        self.create_oval(x1, y1, x1 + 2*r, y1 + 2*r, **kwargs)
        self.create_oval(x2-2*r, y1, x2, y1 + 2*r, **kwargs)
        self.create_oval(x1, y2-2*r, x1 + 2*r, y2, **kwargs)
        self.create_oval(x2-2*r, y2-2*r, x2, y2, **kwargs)
        self.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
        self.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)
    
    def _on_hover(self, entering):
        self.btn.config(bg=self.hover if entering else self.bg)


class ModernToggle(tk.Canvas):
    """Custom modern toggle switch"""
    def __init__(self, parent, variable, on_command, off_command, bg_color=None):
        super().__init__(parent, width=50, height=26, bg=parent["bg"], highlightthickness=0)
        
        self.variable = variable
        self.on_command = on_command
        self.off_command = off_command
        self.bg_color = parent["bg"] if bg_color is None else bg_color
        
        self.toggle_on = ModernColors.TOGGLE_ON
        self.toggle_off = ModernColors.TOGGLE_OFF
        
        self.bind("<Button-1>", self._toggle)
        
        self.draw_toggle()
        
        # Update toggle when variable changes
        self.variable.trace("w", self._on_variable_change)
    
    def draw_toggle(self):
        """Draw the toggle switch"""
        self.delete("all")
        
        is_on = self.variable.get()
        
        # Background track
        color = self.toggle_on if is_on else self.toggle_off
        self.round_rectangle(2, 2, 48, 24, 12, fill=color, outline="")
        
        # Circle knob
        knob_color = "#ffffff"
        x = 32 if is_on else 8
        self.create_oval(x-8, 2, x+8, 24, fill=knob_color, outline="")
        
        # Glow effect when on
        if is_on:
            self.create_oval(10, 4, 40, 20, outline=ModernColors.TOGGLE_ON, width=2, stipple="gray50")
    
    def round_rectangle(self, x1, y1, x2, y2, r, **kwargs):
        self.create_oval(x1, y1, x1 + 2*r, y1 + 2*r, **kwargs)
        self.create_oval(x2-2*r, y1, x2, y1 + 2*r, **kwargs)
        self.create_oval(x1, y2-2*r, x1 + 2*r, y2, **kwargs)
        self.create_oval(x2-2*r, y2-2*r, x2, y2, **kwargs)
        self.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
        self.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)
    
    def _toggle(self, event):
        new_val = not self.variable.get()
        self.variable.set(new_val)
        
        if new_val:
            if self.on_command:
                self.on_command()
        else:
            if self.off_command:
                self.off_command()
        
        self.draw_toggle()
    
    def _on_variable_change(self, *args):
        self.draw_toggle()


class ClipboardApp:
    def __init__(self, root: tk.Tk, db_path: str):
        self.root = root
        self.root.title(f"{ModernColors.EMOJI_CLIPBOARD} Reliable Clipboard")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        self.root.minsize(700, 500)
        
        # Set dark gradient background
        self.root.configure(bg=ModernColors.BG_GRADIENT_START)
        
        # Set window icon
        if platform.system() == 'Windows':
            try:
                self.set_windows_icon()
            except Exception as e:
                logger.warning(f"Failed to set window icon: {e}")
        
        self.db_path = db_path
        try:
            self.storage = StorageManager(db_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to database: {e}")
            self.root.destroy()
            return

        self.monitor: Optional[ClipboardMonitor] = None
        self.monitoring_var = tk.BooleanVar(value=True)
        self.monitoring_var.trace("w", self._on_monitor_toggle)
        
        # System tray
        self.tray_icon = None
        self.setup_system_tray()
        
        self._setup_ui()
        self.refresh_list()
        self.auto_refresh()
        
        # Start monitoring automatically
        self.start_monitor()

    def set_windows_icon(self):
        import sys
        from pathlib import Path
        
        if getattr(sys, 'frozen', False):
            icon_path = Path(sys._MEIPASS) / 'assets' / 'clipboard.ico'
        else:
            icon_path = Path(__file__).parent / 'assets' / 'clipboard.ico'
        
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))

    def setup_system_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            icon_path = self._get_icon_path()
            if icon_path and icon_path.exists():
                image = Image.open(str(icon_path)).resize((64, 64))
            else:
                image = Image.new('RGB', (64, 64), ModernColors.PRIMARY)
                draw = ImageDraw.Draw(image)
                draw.rectangle((16, 16, 48, 48), fill='white')
            
            menu = (
                pystray.MenuItem(f'{ModernColors.EMOJI_CLIPBOARD} Show', self.show_window),
                pystray.MenuItem(f'{ModernColors.EMOJI_WARNING} Exit', self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("clipboard", image, "Reliable Clipboard", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            logger.warning(f"System tray not available: {e}")

    def _get_icon_path(self):
        import sys
        from pathlib import Path
        base_path = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent
        return base_path / 'assets' / 'clipboard.png'

    def show_window(self):
        if self.tray_icon:
            self.tray_icon.visible = False
        self.root.deiconify()

    def quit_app(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def _setup_ui(self):
        """Setup modern dark theme UI"""
        
        # Main container with gradient
        main_container = tk.Frame(self.root, bg=ModernColors.BG_GRADIENT_START)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # ===== HEADER =====
        header = tk.Frame(main_container, bg=ModernColors.BG_GRADIENT_START)
        header.pack(fill=tk.X, padx=24, pady=(20, 0))
        
        # Logo/Title
        title_frame = tk.Frame(header, bg=ModernColors.BG_GRADIENT_START)
        title_frame.pack(side=tk.LEFT)
        
        # App icon
        icon_label = tk.Label(
            title_frame,
            text=ModernColors.EMOJI_CLIPBOARD,
            font=("Segoe UI", 28),
            bg=ModernColors.BG_GRADIENT_START
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 12))
        
        # Title
        title = tk.Label(
            title_frame,
            text="Reliable Clipboard",
            font=("Segoe UI", 22, "bold"),
            fg=ModernColors.TEXT_WHITE,
            bg=ModernColors.BG_GRADIENT_START
        )
        title.pack(side=tk.LEFT)
        
        # Monitor toggle
        toggle_frame = tk.Frame(header, bg=ModernColors.BG_GRADIENT_START)
        toggle_frame.pack(side=tk.RIGHT)
        
        # Monitor status emoji
        self.monitor_emoji = tk.Label(
            toggle_frame,
            text=ModernColors.EMOJI_MONITOR_ON,
            font=("Segoe UI", 14),
            bg=ModernColors.BG_GRADIENT_START
        )
        self.monitor_emoji.pack(side=tk.LEFT, padx=(0, 8))
        
        # Custom toggle switch
        self.toggle = ModernToggle(
            toggle_frame, 
            self.monitoring_var,
            on_command=self.start_monitor,
            off_command=self.stop_monitor
        )
        self.toggle.pack(side=tk.LEFT)
        
        # ===== SEARCH BAR =====
        search_container = tk.Frame(main_container, bg=ModernColors.CARD_BG, padx=2, pady=2)
        search_container.pack(fill=tk.X, padx=24, pady=(20, 16))
        
        # Inner search frame
        search_inner = tk.Frame(search_container, bg=ModernColors.CARD_BG, padx=16, pady=12)
        search_inner.pack(fill=tk.X)
        
        # Search emoji
        search_emoji = tk.Label(
            search_inner,
            text=ModernColors.EMOJI_SEARCH,
            font=("Segoe UI", 16),
            bg=ModernColors.CARD_BG
        )
        search_emoji.pack(side=tk.LEFT, padx=(0, 12))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.search_clips())
        
        self.search_entry = tk.Entry(
            search_inner,
            textvariable=self.search_var,
            font=("Segoe UI", 12),
            bg=ModernColors.CARD_HOVER,
            fg=ModernColors.TEXT_WHITE,
            relief=tk.FLAT,
            bd=0,
            insertbackground=ModernColors.SECONDARY
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Placeholder
        self.search_entry.insert(0, "Search your clipboard history...")
        self.search_entry.bind("<FocusIn>", lambda e: self._on_search_in())
        self.search_entry.bind("<FocusOut>", lambda e: self._on_search_out())
        
        # Results count
        self.results_label = tk.Label(
            search_inner,
            text="",
            font=("Segoe UI", 10),
            fg=ModernColors.TEXT_MUTED,
            bg=ModernColors.CARD_BG
        )
        self.results_label.pack(side=tk.RIGHT, padx=(12, 0))
        
        # ===== CLIPBOARD LIST (Card) =====
        list_container = tk.Frame(main_container, bg=ModernColors.CARD_BG, padx=2, pady=2)
        list_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 16))
        
        # List inner frame
        list_inner = tk.Frame(list_container, bg=ModernColors.CARD_BG)
        list_inner.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ("id", "type", "content", "time")
        self.tree = ttk.Treeview(
            list_inner,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Modern.Treeview"
        )
        
        # Configure columns
        self.tree.heading("id", text="#", anchor=tk.CENTER)
        self.tree.heading("type", text="Type", anchor=tk.CENTER)
        self.tree.heading("content", text="Content", anchor=tk.W)
        self.tree.heading("time", text="Time", anchor=tk.CENTER)
        
        self.tree.column("id", width=50, stretch=False, anchor=tk.CENTER)
        self.tree.column("type", width=80, stretch=False, anchor=tk.CENTER)
        self.tree.column("content", stretch=True, anchor=tk.W)
        self.tree.column("time", width=100, stretch=False, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_inner, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to copy
        self.tree.bind("<Double-Button-1>", lambda e: self.copy_selected())
        
        # Configure treeview style
        style = ttk.Style()
        style.configure(
            "Modern.Treeview",
            background=ModernColors.CARD_BG,
            foreground=ModernColors.TEXT_WHITE,
            fieldbackground=ModernColors.CARD_BG,
            rowheight=44,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=ModernColors.PRIMARY,
            foreground=ModernColors.TEXT_WHITE,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT
        )
        style.map(
            "Modern.Treeview",
            background=[("selected", ModernColors.PRIMARY)],
            foreground=[("selected", ModernColors.TEXT_WHITE)]
        )
        
        # ===== ACTION BUTTONS =====
        actions = tk.Frame(main_container, bg=ModernColors.BG_GRADIENT_START)
        actions.pack(fill=tk.X, padx=24, pady=(0, 20))
        
        # Button container with card look
        btn_container = tk.Frame(actions, bg=ModernColors.CARD_BG, padx=16, pady=12)
        btn_container.pack(fill=tk.X)
        
        # Create modern buttons
        self.create_modern_button(btn_container, f"{ModernColors.EMOJI_COPY} Copy", self.copy_selected, ModernColors.PRIMARY)
        self.create_modern_button(btn_container, f"{ModernColors.EMOJI_DELETE} Delete", self.delete_selected, ModernColors.CARD_HOVER)
        self.create_modern_button(btn_container, f"{ModernColors.EMOJI_REFRESH} Refresh", self.refresh_list, ModernColors.CARD_HOVER)
        
        # Spacer
        tk.Frame(btn_container, bg=ModernColors.CARD_BG).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Clear all button (danger)
        self.create_modern_button(btn_container, f"{ModernColors.EMOJI_CLEAR} Clear All", self.clear_all, ModernColors.ERROR)
        
        # Keyboard shortcuts
        self.root.bind('<F5>', lambda e: self.refresh_list())
        self.root.bind('<Delete>', lambda e: self.delete_selected())
        self.root.bind('<Return>', lambda e: self.copy_selected())
        self.root.bind('<Escape>', lambda e: self.search_var.set(''))
        
        # Close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_modern_button(self, parent, text, command, bg_color):
        """Create a modern styled button"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=ModernColors.TEXT_WHITE,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            activebackground=ModernColors.PRIMARY_HOVER if bg_color == ModernColors.PRIMARY else ModernColors.BORDER,
            activeforeground=ModernColors.TEXT_WHITE,
            highlightthickness=0
        )
        btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # Bind hover
        btn.bind("<Enter>", lambda e: e.widget.config(bg=ModernColors.PRIMARY_HOVER if bg_color == ModernColors.PRIMARY else ModernColors.BORDER))
        btn.bind("<Leave>", lambda e: e.widget.config(bg=bg_color))

    def _on_search_in(self):
        if self.search_entry.get() == "Search your clipboard history...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=ModernColors.TEXT_WHITE)

    def _on_search_out(self):
        if self.search_entry.get() == "":
            self.search_entry.insert(0, "Search your clipboard history...")
            self.search_entry.config(fg=ModernColors.TEXT_MUTED)

    def _on_monitor_toggle(self, *args):
        if self.monitoring_var.get():
            self.monitor_emoji.config(text=ModernColors.EMOJI_MONITOR_ON)
        else:
            self.monitor_emoji.config(text=ModernColors.EMOJI_MONITOR_OFF)

    def refresh_list(self):
        try:
            query = self.search_var.get()
            if query and query != "Search your clipboard history...":
                clips = self.storage.search_clips(query)
            else:
                clips = self.storage.get_recent_clips(limit=100)
            
            # Update results count
            self.results_label.config(text=f"{len(clips)} items")
            
            # Clear and repopulate
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            for clip in clips:
                clip_type = clip.get('clip_type', 'text')
                content = clip['content']
                timestamp = datetime.fromtimestamp(clip['timestamp']).strftime('%H:%M')
                
                # Format based on type
                if clip_type == 'image':
                    emoji = ModernColors.EMOJI_IMAGE
                    display = "Image data"
                elif clip_type == 'file':
                    emoji = ModernColors.EMOJI_FILE
                    files = content.split('\n')
                    display = f"{len(files)} file(s)"
                else:
                    emoji = ModernColors.EMOJI_TEXT
                    display = content.replace('\n', ' ')
                    if len(display) > 50:
                        display = display[:47] + "..."
                
                self.tree.insert("", tk.END, values=(
                    clip['id'],
                    emoji,
                    display,
                    timestamp
                ))
                
        except Exception as e:
            logger.error(f"Error refreshing list: {e}")

    def search_clips(self):
        self.refresh_list()

    def auto_refresh(self):
        self.refresh_list()
        self.root.after(1500, self.auto_refresh)

    def copy_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected)
        clip_id = item['values'][0]
        
        # Get full content from storage
        clips = self.storage.get_recent_clips(limit=1000)
        full_content = next((c['content'] for c in clips if c['id'] == clip_id), "")
        
        try:
            pyperclip.copy(full_content)
            self._show_toast(f"{ModernColors.EMOJI_CHECK} Copied!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {e}")

    def _show_toast(self, message):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = ws // 2 - 80
        y = hs - 120
        toast.geometry(f"160x40+{x}+{y}")
        
        toast.configure(bg=ModernColors.SUCCESS)
        
        label = tk.Label(
            toast,
            text=message,
            font=("Segoe UI", 11, "bold"),
            bg=ModernColors.SUCCESS,
            fg="white",
            padx=20,
            pady=8
        )
        label.pack(fill=tk.BOTH, expand=True)
        
        toast.after(1200, toast.destroy)

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected)
        clip_id = item['values'][0]
        
        if messagebox.askyesno("🗑️ Delete", "Delete this clip?"):
            try:
                self.storage.delete_clip(clip_id)
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")

    def clear_all(self):
        if messagebox.askyesno("🧹 Clear All", "Clear ALL clipboard history? This cannot be undone!"):
            try:
                self.storage.clear_history()
                self.refresh_list()
                self._show_toast(f"{ModernColors.EMOJI_CHECK} Cleared!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear: {e}")

    def start_monitor(self):
        if self.monitor:
            return
        
        history = ClipHistory(storage_manager=self.storage)
        
        def on_change(content, clip_type):
            self.root.after(0, self.refresh_list)
            try:
                history.add_clip(content, clip_type)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
        
        self.monitor = ClipboardMonitor(on_change=on_change, check_interval=0.3)
        self.monitor.start()

    def stop_monitor(self):
        if self.monitor:
            self.monitor.stop()
            self.monitor = None

    def on_close(self):
        if self.tray_icon:
            self.minimize_to_tray()
        else:
            self.quit_app()

    def minimize_to_tray(self):
        self.root.withdraw()
        if self.tray_icon:
            self.tray_icon.visible = True


def start_gui(db_path: str):
    root = tk.Tk()
    app = ClipboardApp(root, db_path)
    root.mainloop()
