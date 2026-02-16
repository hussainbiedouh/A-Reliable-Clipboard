import sys
from unittest.mock import MagicMock

# Mock pyperclip if not installed
if 'pyperclip' not in sys.modules:
    mock_pyperclip = MagicMock()
    mock_pyperclip.paste.return_value = ""
    mock_pyperclip.copy.return_value = None
    
    # Define a real Exception class for PyperclipException
    class PyperclipException(Exception):
        pass
    
    mock_pyperclip.PyperclipException = PyperclipException
    
    sys.modules['pyperclip'] = mock_pyperclip

# Mock watchdog if needed
if 'watchdog' not in sys.modules:
    sys.modules['watchdog'] = MagicMock()
