import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock tkinter before importing gui. Use a dummy object.
mock_tk = MagicMock()
mock_tk.Tk = MagicMock
mock_tk.END = "end"
mock_tk.LEFT = "left"
mock_tk.RIGHT = "right"
mock_tk.BOTH = "both"
mock_tk.X = "x"
mock_tk.Y = "y"
mock_tk.VERTICAL = "vertical"

# Create mock factories for StringVar and BooleanVar
def mock_string_var_factory(*args, **kwargs):
    m = MagicMock()
    m.get.return_value = ""
    m.set = MagicMock()
    m.trace = MagicMock()
    return m

def mock_bool_var_factory(*args, **kwargs):
    m = MagicMock()
    m.get.return_value = False
    m.set = MagicMock()
    return m

mock_tk.StringVar = mock_string_var_factory
mock_tk.BooleanVar = mock_bool_var_factory

# Mock ttk
mock_ttk = MagicMock()

sys.modules['tkinter'] = mock_tk
sys.modules['tkinter.ttk'] = mock_ttk
sys.modules['tkinter.messagebox'] = MagicMock()

# Now import the class to test
from reliable_clipboard.gui import ClipboardApp

class TestGUI(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock()
        
        # Mock storage manager
        self.mock_storage = MagicMock()
        self.mock_storage.get_recent_clips.return_value = [
            {'id': 1, 'content': 'Test Clip', 'timestamp': 1234567890.0}
        ]
        self.mock_storage.search_clips.return_value = []
        
        # Patch StorageManager in gui.py
        patcher = patch('reliable_clipboard.gui.StorageManager', return_value=self.mock_storage)
        self.mock_storage_cls = patcher.start()
        self.addCleanup(patcher.stop)

        # Patch pyperclip
        patcher_clip = patch('reliable_clipboard.gui.pyperclip')
        self.mock_pyperclip = patcher_clip.start()
        self.addCleanup(patcher_clip.stop)
        
        # Patch ClipHistory
        patcher_hist = patch('reliable_clipboard.gui.ClipHistory')
        self.mock_hist = patcher_hist.start()
        self.addCleanup(patcher_hist.stop)
        
        # Patch ClipboardMonitor
        patcher_mon = patch('reliable_clipboard.gui.ClipboardMonitor')
        self.mock_mon = patcher_mon.start()
        self.addCleanup(patcher_mon.stop)

    def test_init(self):
        """Test initialization and initial refresh."""
        app = ClipboardApp(self.root, "test.db")
        # Verify storage was initialized
        self.mock_storage_cls.assert_called_with("test.db")

    def test_refresh_list(self):
        app = ClipboardApp(self.root, "test.db")
        
        # Reset mocks
        self.mock_storage.get_recent_clips.reset_mock()
        app.tree = MagicMock() # Mock the tree instance on the app
        app.tree.get_children.return_value = []
        
        app.refresh_list()
        
        self.mock_storage.get_recent_clips.assert_called()
        app.tree.insert.assert_called()
        
        # Verify arguments - insert("", "end", values=(...))
        call_args = app.tree.insert.call_args
        # call_args is (args, kwargs)
        # args should be ("", tk.END)
        # values should be in kwargs
        self.assertIn('values', call_args.kwargs)

    def test_copy_selected(self):
        app = ClipboardApp(self.root, "test.db")
        app.tree = MagicMock()
        app.tree.selection.return_value = ("I001",)
        app.tree.item.return_value = {'values': [1, '2023-01-01', 'Selected Content']}
        
        app.copy_selected()
        
        self.mock_pyperclip.copy.assert_called_with('Selected Content')

    def test_search(self):
        app = ClipboardApp(self.root, "test.db")
        app.search_var = MagicMock()
        app.search_var.get.return_value = "query"
        
        app.search_clips()
        
        self.mock_storage.search_clips.assert_called_with("query")

if __name__ == '__main__':
    unittest.main()
