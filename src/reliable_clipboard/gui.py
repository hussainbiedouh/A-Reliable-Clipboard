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

class ClipboardApp:
    def __init__(self, root: tk.Tk, db_path: str):
        self.root = root
        self.root.title("A Reliable Clipboard")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        self.root.minsize(500, 400)
        
        # Set custom icon if available (Windows-specific)
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
        
        # Initialize system tray (if supported)
        self.tray_icon = None
        self.setup_system_tray()
        
        self._setup_ui()
        self.refresh_list()
        
        # Auto-refresh loop (faster refresh for better user experience)
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
            
            # Load custom icon or create simple one
            icon_path = self._get_icon_path()
            
            if icon_path and icon_path.exists():
                image = Image.open(str(icon_path))
            else:
                # Create a simple fallback icon
                from PIL import ImageDraw
                image = Image.new('RGB', (64, 64), 'red')
                draw = ImageDraw.Draw(image)
                draw.rectangle((16, 16, 48, 48), fill='white')
            
            # Create menu
            menu = (
                pystray.MenuItem('Show', self.show_window),
                pystray.MenuItem('Exit', self.quit_app)
            )
            
            self.tray_icon = pystray.Icon("clipboard", image, "A Reliable Clipboard", menu)
            
            # Run tray icon in separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
            logger.info("System tray icon initialized")
        except ImportError:
            logger.warning("pystray or PIL not available - system tray disabled")
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
            
        icon_path = base_path / 'assets' / 'clipboard.png'
        logger.debug(f"Icon path: {icon_path}")
        return icon_path

    def show_window(self):
        """Show the main window from system tray."""
        self.tray_icon.visible = False
        self.root.deiconify()

    def quit_app(self):
        """Quit the application from system tray."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

    def minimize_to_tray(self):
        """Minimize to system tray instead of taskbar."""
        self.root.withdraw()
        if self.tray_icon:
            self.tray_icon.visible = True
            self.tray_icon.update_menu()

    def _setup_ui(self):
        # Create style
        style = ttk.Style()
        
        # Set modern theme
        try:
            style.theme_use('clam')
        except:
            pass
            
        # Configure colors for a modern look
        bg_color = '#f5f5f5'
        fg_color = '#333333'
        accent_color = '#4a90d9'
        
        self.root.configure(bg=bg_color)
        
        # Top Frame: Search and Monitor Toggle
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # Search label and entry
        ttk.Label(top_frame, text="🔍 Search:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.search_clips())
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, font=('Segoe UI', 10))
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Monitor toggle
        monitor_check = ttk.Checkbutton(top_frame, text="📋 Monitor", 
                                        variable=self.monitoring_var, 
                                        command=self.toggle_monitor)
        monitor_check.pack(side=tk.RIGHT)

        # Middle Frame: List of Clips
        list_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for clips - improved layout
        columns = ("id", "type", "content")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        # Configure headings
        self.tree.heading("id", text="#", anchor=tk.CENTER)
        self.tree.heading("type", text="Type", anchor=tk.CENTER)
        self.tree.heading("content", text="Content", anchor=tk.W)
        
        # Configure column widths - more space for content
        self.tree.column("id", width=50, stretch=False, anchor=tk.CENTER)
        self.tree.column("type", width=70, stretch=False, anchor=tk.CENTER)
        self.tree.column("content", stretch=True, anchor=tk.W)
        
        # Add only vertical scrollbar (removed horizontal)
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=v_scrollbar.set)
        
        # Pack widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom Frame: Actions
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        # Action buttons - better styling
        btn_style = ttk.Style()
        btn_style.configure('Action.TButton', font=('Segoe UI', 9), padding=5)
        
        ttk.Button(bottom_frame, text="📋 Copy", command=self.copy_selected, 
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🗑️ Delete", command=self.delete_selected,
                  style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="🔄 Refresh", command=self.refresh_list,
                  style='Action.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="🧹 Clear All", command=self.clear_all,
                  style='Action.TButton').pack(side=tk.RIGHT, padx=5)

        # Configure treeview selection color
        style.map('Treeview', 
                  background=[('selected', '#4a90d9')],
                  foreground=[('selected', 'white')])

        # Bind keyboard shortcuts
        self.root.bind('<F5>', lambda e: self.refresh_list())
        self.root.bind('<Delete>', lambda e: self.delete_selected())
        self.root.bind('<Return>', lambda e: self.copy_selected())
        self.root.bind('<Escape>', lambda e: self.search_var.set(''))

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def format_timestamp(self, ts: float) -> str:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    def refresh_list(self):
        """Fetch clips from DB and update the list."""
        try:
            query = self.search_var.get()
            if query:
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
                    display_content = "🖼️ Image"
                elif clip_type == 'file':
                    files = content.split('\n')
                    display_content = f"📁 {len(files)} file{'s' if len(files) > 1 else ''}"
                else:
                    display_content = content.replace('\n', ' ')
                    if len(display_content) > 60:
                        display_content = display_content[:57] + "..."
                
                self.tree.insert("", tk.END, values=(
                    clip['id'],
                    clip_type,
                    display_content
                ))
        except Exception as e:
            logger.error(f"Error refreshing list: {e}")

    def search_clips(self):
        self.refresh_list()

    def auto_refresh(self):
        """Periodically refresh the list (faster interval for better UX)."""
        self.refresh_list()
        self.root.after(2000, self.auto_refresh)  # Refresh every 2 seconds

    def copy_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        item = self.tree.item(selected_item)
        clip_id = item['values'][0]
        clip_type = item['values'][1]
        content = item['values'][2]
        
        try:
            if clip_type == 'text':
                pyperclip.copy(content)
                # Show temporary feedback
                feedback = tk.Toplevel(self.root)
                feedback.title("")
                feedback.geometry("200x50+{}+{}".format(
                    self.root.winfo_x() + self.root.winfo_width() // 2 - 100,
                    self.root.winfo_y() + self.root.winfo_height() // 2 - 25
                ))
                ttk.Label(feedback, text="✅ Copied to clipboard!", font=('Segoe UI', 10)).pack(
                    fill=tk.BOTH, expand=True, padx=10, pady=10)
                feedback.after(1500, feedback.destroy)
            elif clip_type == 'image':
                messagebox.showinfo("🖼️ Image Clip", "Images cannot be copied directly from clipboard history.\n\nYou need to open the image first.")
            elif clip_type == 'file':
                files = content.split('\n')
                messagebox.showinfo("File Clip", f"File path{'s' if len(files) > 1 else ''}: \n{content}")
            else:
                messagebox.showinfo("Unknown Type", f"Unsupported clip type: {clip_type}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy to clipboard: {e}")

    def delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        item = self.tree.item(selected_item)
        clip_id = item['values'][0]
        
        try:
            self.storage.delete_clip(clip_id)
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete clip: {e}")

    def clear_all(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all history?"):
            try:
                self.storage.clear_history()
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear history: {e}")

    def toggle_monitor(self):
        if self.monitoring_var.get():
            self.start_monitor()
        else:
            self.stop_monitor()

    def start_monitor(self):
        if self.monitor:
            return
            
        history = ClipHistory(storage_manager=self.storage)
        
        def on_change(content, clip_type):
            # This runs in a thread, so be careful with GUI updates
            self.root.after(0, self.refresh_list)
            try:
                history.add_clip(content, clip_type)
            except Exception as e:
                logger.error(f"Error adding clip in monitor: {e}")

        self.monitor = ClipboardMonitor(on_change)
        self.monitor.start()

    def stop_monitor(self):
        if self.monitor:
            self.monitor.stop()
            self.monitor = None

    def on_close(self):
        """Handle window closing - minimize to tray or quit."""
        if self.tray_icon:
            self.minimize_to_tray()
        else:
            self.quit_app()

def start_gui(db_path: str):
    root = tk.Tk()
    app = ClipboardApp(root, db_path)
    root.mainloop()
