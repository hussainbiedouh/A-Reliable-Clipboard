import time
import threading
import logging
import pyperclip
import platform
import io
import base64
from typing import Callable, Optional, Tuple

logger = logging.getLogger(__name__)

class ClipboardMonitor:
    """
    Reliable clipboard monitor with multi-format support.
    Uses polling method with robust error handling.
    """

    def __init__(self, on_change: Callable[[str, str], None], check_interval: float = 0.5):
        """
        Initialize the monitor.
        
        Args:
            on_change: Callback function (content, clip_type)
            check_interval: Time between clipboard checks
        """
        self._on_change = on_change
        self._check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_content: str = ""
        self._last_type: str = "text"
        self._logger = logging.getLogger(__name__)
        self._error_count = 0
        self._max_errors = 10

    def start(self):
        """Start monitoring in background thread."""
        if self._running:
            logger.warning("Monitor already running")
            return
        
        self._running = True
        self._error_count = 0
        
        # Get initial clipboard state
        try:
            self._last_content, self._last_type = self._get_clipboard_content_safe()
        except Exception as e:
            logger.warning(f"Initial clipboard read failed: {e}")
            self._last_content = ""
            self._last_type = "text"
        
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="ClipboardMonitor")
        self._thread.start()
        logger.info("Clipboard monitor started")

    def stop(self):
        """Stop monitoring thread."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("Clipboard monitor stopped")

    def _get_clipboard_content_safe(self) -> Tuple[str, str]:
        """Safely get clipboard content with fallback methods."""
        
        # Method 1: Try to get files first (Windows)
        if platform.system() == 'Windows':
            try:
                import win32clipboard
                import win32con
                
                win32clipboard.OpenClipboard()
                
                # Check for files
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                    files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                    if files and len(files) > 0:
                        win32clipboard.CloseClipboard()
                        return '\n'.join(files), "file"
                
                win32clipboard.CloseClipboard()
            except Exception as e:
                pass
        
        # Method 2: Try to get image
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is not None and hasattr(img, 'size'):
                # Convert image to base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                return base64.b64encode(buffer.getvalue()).decode('utf-8'), "image"
        except Exception as e:
            pass
        
        # Method 3: Try pyperclip (most reliable for text)
        try:
            text = pyperclip.paste()
            if text and len(text.strip()) > 0:
                return text, "text"
        except Exception as e:
            pass
        
        # Method 4: Try tkinter clipboard (fallback)
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            if text and len(text.strip()) > 0:
                return text, "text"
        except:
            pass
        
        return "", "text"

    def _monitor_loop(self):
        """Main monitoring loop with error recovery."""
        while self._running:
            try:
                content, clip_type = self._get_clipboard_content_safe()
                
                # Check if content changed
                if content and (content != self._last_content or clip_type != self._last_type):
                    self._last_content = content
                    self._last_type = clip_type
                    
                    try:
                        self._on_change(content, clip_type)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                self._error_count = 0  # Reset error count on success
                
            except Exception as e:
                self._error_count += 1
                if self._error_count > self._max_errors:
                    logger.error(f"Too many errors ({self._error_count}), stopping monitor")
                    break
                
                # Wait longer on error
                time.sleep(1)
                continue
            
            time.sleep(self._check_interval)
        
        self._running = False
        logger.info("Monitor loop ended")
