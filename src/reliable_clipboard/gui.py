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


class MaterialStyle:
    """Material Design color palette and styling"""
    # Primary colors
    PRIMARY = "#6200EE"       # Deep Purple
    PRIMARY_VARIANT = "#3700B3"
    SECONDARY = "#03DAC6"     # Teal
    SECONDARY_VARIANT = "#018786"
    
    # Background & Surface
    BACKGROUND = "#FFFFFF"
    SURFACE = "#FFFFFF"
    SURFACE_VARIANT = "#F5F5F5"
    
    # On colors
    PRIMARY_ON = "#FFFFFF"
    SECONDARY_ON = "#000000"
    ON_BACKGROUND = "#000000"
    ON_SURFACE = "#000000"
    
    # Status colors
    ERROR = "#B00020"
    SUCCESS = "#4CAF50"
    WARNING = "#FF9800"
    
    # Text colors
    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DISABLED = "#BDBDBD"
    
    # Divider
    DIVIDER = "#E0E0E0"
    
    # Shadows
    SHADOW_LOW = "0 1 3 rgba(0,0,0,0.12), 0 1 2 rgba(0,0,0,0.24)"
    SHADOW_MED = "0 3 6 rgba(0,0,0,0.15), 0 2 6 rgba(0,0,0,0.20)"
    SHADOW_HIGH = "0 10 20 rgba(0,0,0,0.19), 0 6 10 rgba(0,0,0,0.23)"
    
    @staticmethod
    def configure_styles(root):
        """Configure ttk styles for Material Design"""
        style = ttk.Style(root)
        
        # Use a clean font
        font_family = "Segoe UI"
        
        # Configure Treeview (List)
        style.configure(
            "Material.Treeview",
            background=MaterialStyle.SURFACE,
            foreground=MaterialStyle.TEXT_PRIMARY,
            fieldbackground=MaterialStyle.SURFACE,
            rowheight=40,
            font=(font_family, 10)
        )
        
        style.configure(
            "Material.Treeview.Heading",
            background=MaterialStyle.PRIMARY,
            foreground=MaterialStyle.PRIMARY_ON,
            font=(font_family, 10, "bold"),
            relief="flat"
        )
        
        style.map(
            "Material.Treeview",
            background=[("selected", MaterialStyle.PRIMARY)],
            foreground=[("selected", MaterialStyle.PRIMARY_ON)]
        )
        
        style.map(
            "Material.Treeview.Heading",
            background=[("active", MaterialStyle.PRIMARY_VARIANT)]
        )
        
        # Configure Buttons
        style.configure(
            "Material.TButton",
            padding=(16, 8),
            font=(font_family, 10, "bold"),
            relief="flat",
            background=MaterialStyle.PRIMARY,
            foreground=MaterialStyle.PRIMARY_ON
        )
        
        style.map(
            "Material.TButton",
            background=[("active", MaterialStyle.PRIMARY_VARIANT), ("pressed", MaterialStyle.PRIMARY_VARIANT)],
            relief=[("pressed", "flat")]
        )
        
        # Configure Secondary Button
        style.configure(
            "Material.Secondary.TButton",
            padding=(16, 8),
            font=(font_family, 10),
            relief="flat",
            background=MaterialStyle.SURFACE_VARIANT,
            foreground=MaterialStyle.TEXT_PRIMARY
        )
        
        style.map(
            "Material.Secondary.TButton",
            background=[("active", MaterialStyle.DIVIDER)]
        )
        
        # Configure Entry
        style.configure(
            "Material.TEntry",
            padding=(12, 8),
            fieldbackground=MaterialStyle.SURFACE_VARIANT,
            foreground=MaterialStyle.TEXT_PRIMARY,
            relief="flat",
            borderwidth=0
        )
        
        # Configure Frame
        style.configure(
            "Material.TFrame",
            background=MaterialStyle.SURFACE
        )
        
        # Configure Label
        style.configure(
            "Material.TLabel",
            background=MaterialStyle.SURFACE,
            foreground=MaterialStyle.TEXT_PRIMARY,
            font=(font_family, 10)
        )
        
        # Configure Checkbox
        style.configure(
            "Material.TCheckbutton",
            background=MaterialStyle.SURFACE,
            foreground=MaterialStyle.TEXT_PRIMARY,
            font=(font_family, 10)
        )
        
        return style


class ClipboardApp:
    def __init__(self, root: tk.Tk, db_path: str):
        self.root = root
        self.root.title("📋 Reliable Clipboard")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.root.minsize(600, 450)
        
        # Material Design background
        self.root.configure(bg=MaterialStyle.BACKGROUND)
        
        # Set custom icon if available (Windows-specific)
        if platform.system() == 'Windows':
            try:
                self.set_windows_icon()
            except Exception as e:
                logger.warning(f"Failed to set window icon: {e}")
        
        # Configure Material styles
        self.style = MaterialStyle.configure_styles(self.root)
        
        self.db_path = db_path
        try:
            self.storage = StorageManager(db_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to database: {e}")
            self.root.destroy()
            return

        self.monitor: Optional[ClipboardMonitor] = None
        self.monitoring_var = tk.BooleanVar(value=True)
        
        # Initialize system tray
        self.tray_icon = None
        self.setup_system_tray()
        
        self._setup_ui()
        self.refresh_list()
        
        # Auto-refresh loop
        self.auto_refresh()

    def set_windows_icon(self):
        """Set custom window icon on Windows."""
        import sys
        from pathlib import Path
        
        if getattr(sys, 'frozen', False):
            icon_path = Path(sys._MEIPASS) / 'assets' / 'clipboard.ico'
        else:
            icon_path = Path(__file__).parent / 'assets' / 'clipboard.ico'
        
        if icon_path.exists():
            self.root.iconbitmap(str(icon_path))

    def setup_system_tray(self):
        """Setup system tray icon and menu."""
        try:
            import pystray
            from PIL import Image
            
            # Load custom icon
            icon_path = self._get_icon_path()
            
            if icon_path and icon_path.exists():
                image = Image.open(str(icon_path))
            else:
                from PIL import ImageDraw
                image = Image.new('RGB', (64, 64), MaterialStyle.PRIMARY)
                draw = ImageDraw.Draw(image)
                draw.rectangle((16, 16, 48, 48), fill='white')
            
            menu = (
                pystray.MenuItem('📋 Show', self.show_window),
                pystray.MenuItem('❌ Exit', self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("clipboard", image, "Reliable Clipboard", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
        except ImportError:
            logger.warning("pystray not available")
        except Exception as e:
            logger.error(f"Failed to setup system tray: {e}")

    def _get_icon_path(self):
        """Get the path to the application icon."""
        import sys
        from pathlib import Path
        
        if getattr(sys, 'frozen', False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent
            
        return base_path / 'assets' / 'clipboard.png'

    def show_window(self):
        """Show the main window from system tray."""
        self.tray_icon.visible = False
        self.root.deiconify()

    def quit_app(self):
        """Quit the application from system tray."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def _setup_ui(self):
        """Setup the Material Design UI"""
        
        # Main container with padding
        main_container = tk.Frame(self.root, bg=MaterialStyle.BACKGROUND)
        main_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # ===== HEADER SECTION =====
        header_frame = tk.Frame(main_container, bg=MaterialStyle.BACKGROUND)
        header_frame.pack(fill=tk.X, pady=(0, 16))
        
        # App Title
        title_label = tk.Label(
            header_frame,
            text="📋 Reliable Clipboard",
            font=("Segoe UI", 20, "bold"),
            fg=MaterialStyle.TEXT_PRIMARY,
            bg=MaterialStyle.BACKGROUND
        )
        title_label.pack(side=tk.LEFT)
        
        # Monitor Status Indicator
        self.monitor_status = tk.Label(
            header_frame,
            text="●",
            font=("Segoe UI", 12),
            fg=MaterialStyle.SUCCESS,
            bg=MaterialStyle.BACKGROUND
        )
        self.monitor_status.pack(side=tk.RIGHT, padx=(0, 8))
        
        self.monitor_label = tk.Label(
            header_frame,
            text="Monitoring",
            font=("Segoe UI", 10),
            fg=MaterialStyle.TEXT_SECONDARY,
            bg=MaterialStyle.BACKGROUND
        )
        self.monitor_label.pack(side=tk.RIGHT)
        
        # ===== SEARCH SECTION =====
        search_frame = tk.Frame(main_container, bg=MaterialStyle.SURFACE_VARIANT, padx=12, pady=12)
        search_frame.pack(fill=tk.X, pady=(0, 16))
        
        # Search icon
        search_icon = tk.Label(
            search_frame,
            text="🔍",
            font=("Segoe UI", 14),
            bg=MaterialStyle.SURFACE_VARIANT
        )
        search_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.search_clips())
        
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 12),
            bg=MaterialStyle.SURFACE_VARIANT,
            fg=MaterialStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            bd=0,
            insertbackground=MaterialStyle.PRIMARY
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Placeholder text
        self.search_entry.insert(0, "Search clipboard history...")
        self.search_entry.bind("<FocusIn>", lambda args: self._on_search_focus_in())
        self.search_entry.bind("<FocusOut>", lambda args: self._on_search_focus_out())
        
        # Monitor toggle switch
        self.monitor_check = tk.Checkbutton(
            search_frame,
            text="📡",
            variable=self.monitoring_var,
            command=self.toggle_monitor,
            font=("Segoe UI", 14),
            bg=MaterialStyle.SURFACE_VARIANT,
            fg=MaterialStyle.TEXT_PRIMARY,
            activebackground=MaterialStyle.SURFACE_VARIANT,
            selectcolor=MaterialStyle.SURFACE_VARIANT
        )
        self.monitor_check.pack(side=tk.RIGHT, padx=(12, 0))
        
        # ===== CONTENT SECTION (Card) =====
        content_card = tk.Frame(main_container, bg=MaterialStyle.SURFACE, padx=1, pady=1)
        content_card.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for clips
        columns = ("id", "type", "content")
        self.tree = ttk.Treeview(
            content_card, 
            columns=columns, 
            show="headings", 
            selectmode="browse",
            style="Material.Treeview"
        )
        
        # Configure headings
        self.tree.heading("id", text="#", anchor=tk.CENTER)
        self.tree.heading("type", text="Type", anchor=tk.CENTER)
        self.tree.heading("content", text="Content", anchor=tk.W)
        
        # Configure columns
        self.tree.column("id", width=50, stretch=False, anchor=tk.CENTER)
        self.tree.column("type", width=80, stretch=False, anchor=tk.CENTER)
        self.tree.column("content", stretch=True, anchor=tk.W)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(content_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to copy
        self.tree.bind("<Double-Button-1>", lambda e: self.copy_selected())
        
        # ===== ACTION BAR =====
        action_frame = tk.Frame(main_container, bg=MaterialStyle.BACKGROUND)
        action_frame.pack(fill=tk.X, pady=(16, 0))
        
        # Action buttons
        btn_copy = tk.Button(
            action_frame,
            text="📋 Copy",
            command=self.copy_selected,
            font=("Segoe UI", 10, "bold"),
            bg=MaterialStyle.PRIMARY,
            fg=MaterialStyle.PRIMARY_ON,
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground=MaterialStyle.PRIMARY_VARIANT,
            activeforeground=MaterialStyle.PRIMARY_ON
        )
        btn_copy.pack(side=tk.LEFT, padx=(0, 8))
        
        btn_delete = tk.Button(
            action_frame,
            text="🗑️ Delete",
            command=self.delete_selected,
            font=("Segoe UI", 10),
            bg=MaterialStyle.SURFACE_VARIANT,
            fg=MaterialStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground=MaterialStyle.DIVIDER
        )
        btn_delete.pack(side=tk.LEFT, padx=(0, 8))
        
        btn_refresh = tk.Button(
            action_frame,
            text="🔄 Refresh",
            command=self.refresh_list,
            font=("Segoe UI", 10),
            bg=MaterialStyle.SURFACE_VARIANT,
            fg=MaterialStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground=MaterialStyle.DIVIDER
        )
        btn_refresh.pack(side=tk.LEFT, padx=(0, 8))
        
        # Spacer
        tk.Frame(action_frame, bg=MaterialStyle.BACKGROUND).pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        btn_clear = tk.Button(
            action_frame,
            text="🧹 Clear All",
            command=self.clear_all,
            font=("Segoe UI", 10),
            bg=MaterialStyle.ERROR,
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            activebackground="#900020",
            activeforeground="white"
        )
        btn_clear.pack(side=tk.RIGHT)
        
        # Keyboard shortcuts
        self.root.bind('<F5>', lambda e: self.refresh_list())
        self.root.bind('<Delete>', lambda e: self.delete_selected())
        self.root.bind('<Return>', lambda e: self.copy_selected())
        self.root.bind('<Escape>', lambda e: self.search_var.set(''))
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _on_search_focus_in(self):
        """Handle search entry focus in"""
        if self.search_entry.get() == "Search clipboard history...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.configure(fg=MaterialStyle.TEXT_PRIMARY)
    
    def _on_search_focus_out(self):
        """Handle search entry focus out"""
        if self.search_entry.get() == "":
            self.search_entry.insert(0, "Search clipboard history...")
            self.search_entry.configure(fg=MaterialStyle.TEXT_DISABLED)

    def format_timestamp(self, ts: float) -> str:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')

    def refresh_list(self):
        """Fetch clips from DB and update the list."""
        try:
            query = self.search_var.get()
            if query and query != "Search clipboard history...":
                clips = self.storage.search_clips(query)
            else:
                clips = self.storage.get_recent_clips(limit=50)
            
            # Clear current items
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            for clip in clips:
                clip_type = clip.get('clip_type', 'text')
                content = clip['content']
                
                if clip_type == 'image':
                    display_type = "🖼️ Image"
                    display_content = "Image clipboard data"
                elif clip_type == 'file':
                    files = content.split('\n')
                    display_type = "📁 Files"
                    display_content = f"{len(files)} file{'s' if len(files) > 1 else ''}: {files[0]}"
                    if len(display_content) > 50:
                        display_content = display_content[:47] + "..."
                else:
                    display_type = "📝 Text"
                    display_content = content.replace('\n', ' ')
                    if len(display_content) > 60:
                        display_content = display_content[:57] + "..."
                
                # Insert with tag for alternating rows
                tag = "even" if clip['id'] % 2 == 0 else "odd"
                self.tree.insert("", tk.END, values=(
                    clip['id'],
                    display_type,
                    display_content
                ), tags=(tag,))
                
        except Exception as e:
            logger.error(f"Error refreshing list: {e}")

    def search_clips(self):
        self.refresh_list()

    def auto_refresh(self):
        """Periodically refresh the list."""
        self.refresh_list()
        self.root.after(2000, self.auto_refresh)

    def copy_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        item = self.tree.item(selected_item)
        clip_id = item['values'][0]
        clip_type = item['values'][1]
        content = item['values'][2]
        
        # Get full content from storage
        clips = self.storage.get_recent_clips(limit=1000)
        full_content = next((c['content'] for c in clips if c['id'] == clip_id), "")
        
        try:
            if "Text" in clip_type:
                pyperclip.copy(full_content)
                self._show_toast("✅ Copied to clipboard!")
            elif "Image" in clip_type:
                messagebox.showinfo("🖼️ Image", "Image preview and paste coming soon!")
            elif "File" in clip_type:
                messagebox.showinfo("📁 Files", f"File path(s):\n{full_content}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy: {e}")

    def _show_toast(self, message):
        """Show a temporary toast message"""
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        
        # Position at bottom center
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = ws // 2 - 100
        y = hs - 100
        toast.geometry(f"200x40+{x}+{y}")
        
        toast.configure(bg=MaterialStyle.TEXT_PRIMARY)
        
        label = tk.Label(
            toast,
            text=message,
            font=("Segoe UI", 10, "bold"),
            bg=MaterialStyle.TEXT_PRIMARY,
            fg="white",
            padx=20,
            pady=10
        )
        label.pack(fill=tk.BOTH, expand=True)
        
        toast.after(1500, toast.destroy)

    def delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        item = self.tree.item(selected_item)
        clip_id = item['values'][0]
        
        if messagebox.askyesno("Delete Clip", "Are you sure you want to delete this clip?"):
            try:
                self.storage.delete_clip(clip_id)
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")

    def clear_all(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear ALL clipboard history?"):
            try:
                self.storage.clear_history()
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear: {e}")

    def toggle_monitor(self):
        if self.monitoring_var.get():
            self.start_monitor()
            self.monitor_status.config(text="●", fg=MaterialStyle.SUCCESS)
            self.monitor_label.config(text="Monitoring")
        else:
            self.stop_monitor()
            self.monitor_status.config(text="○", fg=MaterialStyle.TEXT_DISABLED)
            self.monitor_label.config(text="Paused")

    def start_monitor(self):
        if self.monitor:
            return
            
        history = ClipHistory(storage_manager=self.storage)
        
        def on_change(content, clip_type):
            self.root.after(0, self.refresh_list)
            try:
                history.add_clip(content, clip_type)
            except Exception as e:
                logger.error(f"Error adding clip: {e}")

        self.monitor = ClipboardMonitor(on_change)
        self.monitor.start()

    def stop_monitor(self):
        if self.monitor:
            self.monitor.stop()
            self.monitor = None

    def on_close(self):
        """Handle window closing - minimize to tray"""
        if self.tray_icon:
            self.minimize_to_tray()
        else:
            self.quit_app()

    def minimize_to_tray(self):
        """Minimize to system tray"""
        self.root.withdraw()
        if self.tray_icon:
            self.tray_icon.visible = True


def start_gui(db_path: str):
    root = tk.Tk()
    app = ClipboardApp(root, db_path)
    root.mainloop()
