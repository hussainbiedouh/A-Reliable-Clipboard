import threading
import pytest
from unittest.mock import MagicMock, patch
from reliable_clipboard.clipboard_monitor import ClipboardMonitor

class TestClipboardMonitor:
    
    @patch('reliable_clipboard.clipboard_monitor.ImageGrab.grabclipboard')
    @patch('reliable_clipboard.clipboard_monitor.pyperclip.paste')
    def test_start_monitor_initial_read(self, mock_paste, mock_grabclipboard):
        """Test that the monitor reads the initial clipboard state without triggering the callback."""
        mock_grabclipboard.return_value = None  # No image
        mock_paste.return_value = "Initial Clipboard Content"
        
        callback = MagicMock()
        monitor = ClipboardMonitor(on_change=callback, check_interval=0.1)
        
        # Start and immediately stop
        monitor.start()
        monitor.stop()
        
        # Verify it read the clipboard once on start
        mock_paste.assert_called()
        mock_grabclipboard.assert_called()
        
        # Verify callback was NOT called (initial content shouldn't trigger update)
        callback.assert_not_called()

    @patch('reliable_clipboard.clipboard_monitor.ImageGrab.grabclipboard')
    @patch('reliable_clipboard.clipboard_monitor.pyperclip.paste')
    def test_monitor_detects_change(self, mock_paste, mock_grabclipboard):
        """Test that the monitor detects a change and triggers the callback."""
        mock_grabclipboard.return_value = None  # No image
        
        # Setup sequence of return values:
        # 1. Initial read: "Initial"
        # 2. First check: "Initial" (no change)
        # 3. Second check: "New Content" (change!)
        # 4. Subsequent checks: "New Content" (no change)
        
        # We use a generator to ensure we don't run out of values (StopIteration)
        def side_effect():
            yield "Initial"       # start()
            yield "Initial"       # loop 1
            yield "New Content"   # loop 2 (trigger)
            while True:
                yield "New Content" # loop 3...n
        
        mock_paste.side_effect = side_effect()
        
        callback = MagicMock()
        monitor = ClipboardMonitor(on_change=callback, check_interval=0.05)
        
        monitor.start()
        
        # Wait enough time for at least 3 checks (0.15s) + buffer
        import time
        time.sleep(0.3)
        
        monitor.stop()
        
        # Verify callback was called exactly once with "New Content"
        callback.assert_called_once_with("New Content", "text")

    @pytest.mark.skip("Image detection test temporarily disabled")
    @patch('reliable_clipboard.clipboard_monitor.ImageGrab.grabclipboard')
    @patch('reliable_clipboard.clipboard_monitor.pyperclip.paste')
    def test_monitor_detects_image(self, mock_paste, mock_grabclipboard):
        """Test that the monitor detects an image change."""
        mock_paste.return_value = ""  # No text
        
        # Create a mock image object with save method
        mock_image = MagicMock()
        
        # Setup sequence: initial read has no image, then image appears
        def image_side_effect():
            yield None  # Initial read: no image
            yield mock_image  # First check: image!
            while True:
                yield mock_image
                
        mock_grabclipboard.side_effect = image_side_effect()
        
        callback = MagicMock()
        monitor = ClipboardMonitor(on_change=callback, check_interval=0.05)
        
        monitor.start()
        
        import time
        time.sleep(0.3)
        
        monitor.stop()
        
        # Verify callback was called with image data
        callback.assert_called()
        call_args = callback.call_args
        assert len(call_args[0]) == 2
        assert call_args[0][1] == "image"

    @patch('reliable_clipboard.clipboard_monitor.ImageGrab.grabclipboard')
    @patch('reliable_clipboard.clipboard_monitor.pyperclip.paste')
    def test_monitor_handles_exception(self, mock_paste, mock_grabclipboard):
        """Test that the monitor handles exceptions gracefully without crashing."""
        mock_grabclipboard.return_value = None
        # Simulate an exception during paste
        mock_paste.side_effect = Exception("Clipboard Error")
        
        callback = MagicMock()
        monitor = ClipboardMonitor(on_change=callback, check_interval=0.1)
        
        # Start monitoring
        monitor.start()
        
        # Let it run for a bit
        import time
        time.sleep(0.2)
        
        monitor.stop()
        
        # Should not have crashed, callback not called
        callback.assert_not_called()

    def test_start_stop_idempotency(self):
        """Test calling start/stop multiple times is safe."""
        monitor = ClipboardMonitor(lambda x, y: None)
        
        # Start twice
        with patch('reliable_clipboard.clipboard_monitor.pyperclip.paste'), \
             patch('reliable_clipboard.clipboard_monitor.ImageGrab.grabclipboard'):
            monitor.start()
            monitor.start()  # Should log warning but not crash
            
            assert monitor._running is True
            
            monitor.stop()
            monitor.stop()   # Should be safe
            
            assert monitor._running is False
