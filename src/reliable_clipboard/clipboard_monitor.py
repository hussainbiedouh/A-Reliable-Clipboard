import time
import threading
import logging
import pyperclip
import platform
import io
import base64
from typing import Callable, Optional, Tuple
from PIL import ImageGrab

logger = logging.getLogger(__name__)

class ClipboardMonitor:
    """
    Monitors the system clipboard for changes and triggers a callback.
    Supports text, images, and file content types.
    """

    def __init__(self, on_change: Callable[[str, str], None], check_interval: float = 0.5):
        """
        Initialize the monitor.

        Args:
            on_change: Callback function to execute when clipboard content changes.
                       It receives the new content and clip type as arguments.
            check_interval: Time in seconds between clipboard checks.
        """
        self._on_change = on_change
        self._check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_content: Optional[str] = None
        self._last_type: str = "text"
        self._logger = logging.getLogger(__name__)

    def start(self):
        """Starts the monitoring in a background thread."""
        if self._running:
            self._logger.warning("ClipboardMonitor is already running.")
            return

        self._running = True
        # Initialize last content to current clipboard to avoid immediate trigger
        try:
            self._last_content, self._last_type = self._get_clipboard_content()
        except Exception as e:
            self._logger.error(f"Failed to read initial clipboard content: {e}")
            self._last_content = ""
            self._last_type = "text"

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self._logger.info("Clipboard monitoring started.")

    def stop(self):
        """Stops the monitoring thread."""
        if not self._running:
            return
            
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._logger.info("Clipboard monitoring stopped.")

    def _get_clipboard_content(self) -> Tuple[str, str]:
        """Get clipboard content with type detection - checks in order: files, images, text."""
        try:
            # Check for files FIRST (Windows specific)
            if platform.system() == 'Windows':
                try:
                    import win32clipboard
                    import win32con
                    
                    win32clipboard.OpenClipboard()
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                        files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                        if files:
                            self._logger.debug(f"Clipboard contains {len(files)} files")
                            return '\n'.join(files), "file"
                except Exception as e:
                    self._logger.debug(f"Error checking for files in clipboard: {e}")
                finally:
                    try:
                        win32clipboard.CloseClipboard()
                    except:
                        pass
            
            # Check for images
            image = ImageGrab.grabclipboard()
            if image:
                self._logger.debug("Clipboard contains image")
                return self._image_to_base64(image), "image"
                
            # Finally check for text
            text = pyperclip.paste()
            if text:
                self._logger.debug("Clipboard contains text")
                return text, "text"
                        
        except Exception as e:
            self._logger.error(f"Error reading clipboard: {e}")
            
        return "", "text"

    def _image_to_base64(self, image) -> str:
        """Convert PIL Image to base64 string."""
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_data = img_buffer.getvalue()
        return base64.b64encode(img_data).decode('utf-8')

    def _monitor_loop(self):
        """Internal loop to check clipboard content."""
        while self._running:
            try:
                current_content, current_type = self._get_clipboard_content()
                
                if current_content and (current_content != self._last_content or current_type != self._last_type):
                    self._last_content = current_content
                    self._last_type = current_type
                    self._logger.debug(f"Clipboard change detected (type: {current_type})")
                    try:
                        self._on_change(current_content, current_type)
                    except Exception as e:
                        self._logger.error(f"Error in clipboard callback: {e}")
                        
            except Exception as e:
                self._logger.error(f"Unexpected error in clipboard monitor: {e}")
                
            time.sleep(self._check_interval)
